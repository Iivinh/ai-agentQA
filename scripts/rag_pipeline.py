import os, google.generativeai as genai
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch

GEMINI_API_KEY = "AIzaSyAJlOwMZm7n08S-vqfzgISw1P-0D-UcnlI"
EMBED_MODEL    = "models/gemini-embedding-001"
EMBED_DIMS     = 3072
genai.configure(api_key=GEMINI_API_KEY)

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX = "school_knowledge"
es = Elasticsearch(ES_URL)
TOP_K = 10
RRF_K = 60  # tham số RRF (rank_constant)
RRF_WINDOW = 50  # số doc lấy từ mỗi nguồn (BM25, kNN) để fuse
KNN_NUM_CANDIDATES = 200  # số candidates để kNN lọc trước khi lấy top k
# ====== Embedding ======
def embed_query(text: str) -> List[float]:
    r = genai.embed_content(model=EMBED_MODEL, content=text)
    return r["embedding"]

# ... các import & config như bạn có ...
import os

# Ẩn toàn bộ log gRPC/absl
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_ABORT_ON_LEAKS"] = "false"

import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

from typing import Iterable, Literal, Union



def hybrid_search(
    query_text: str,
    keywords: str | None = None,
    filters: dict | None = None,
    top_k: int = 10,
    rrf_window: int = 50,
    knn_num_candidates: int = 200,
    rrf_k: int = 60,
):
    # 1) BM25
    must = []
    if keywords:
        must.append({
            "multi_match": {
                "query": keywords,
                "fields": ["title^2", "text"],
                "operator": "and"
            }
        })

    bm25_body = {
        "size": rrf_window,
        "query": {
            "bool": {
                "must": must or [{"match_all": {}}],
                **({"filter": filters} if filters else {})
            }
        },
        "_source": ["title","page_from","page_to","text"]
    }
    bm25_res = es.search(index=ES_INDEX, body=bm25_body)
    bm25_hits = bm25_res.get("hits", {}).get("hits", [])

    # 2) kNN
    qvec = embed_query(query_text)
    knn_body = {
        "knn": {
            "field": "vector",
            "query_vector": qvec,
            "k": rrf_window,
            "num_candidates": knn_num_candidates
        },
        "_source": ["title","page_from","page_to","text"],
        "highlight": {"fields": {"text": {"fragment_size": 150, "number_of_fragments": 1}}}
    }
    if filters:
        knn_body["knn"]["filter"] = filters

    # ⚠️ perform_request trả về TransportApiResponse -> cần .body
    knn_raw = es.transport.perform_request(
        "POST",
        f"/{ES_INDEX}/_knn_search",
        headers={"Content-Type": "application/json"},
        body=knn_body,
    )
    knn_res = knn_raw.body if hasattr(knn_raw, "body") else knn_raw
    knn_hits = knn_res.get("hits", {}).get("hits", [])

    # 3) RRF fuse
    def rrf_fuse(bm25_hits, knn_hits, top_k=top_k, k=rrf_k):
        scores = {}
        # cộng 1/(k + rank)
        for rank, h in enumerate(bm25_hits, start=1):
            _id = h["_id"]; scores[_id] = scores.get(_id, 0.0) + 1.0/(k+rank)
        for rank, h in enumerate(knn_hits, start=1):
            _id = h["_id"]; scores[_id] = scores.get(_id, 0.0) + 1.0/(k+rank)

        # lấy _source từ một trong hai list
        idx = {h["_id"]: h for h in bm25_hits}
        idx.update({h["_id"]: h for h in knn_hits})

        out = []
        for _id, sc in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            src = idx[_id].get("_source", {})
            out.append({
                "_id": _id,
                "rrf_score": sc,
                "title": src.get("title"),
                "page_from": src.get("page_from"),
                "page_to": src.get("page_to"),
                "snippet": src.get("text")
            })
        return out
    
    return rrf_fuse(bm25_hits, knn_hits)

from collections import Counter
from typing import List, Dict, Any, Iterable, Optional

def _flatten_hits(hits_per_kw: Iterable[Any], pick_top1_per_kw: bool = True) -> List[Dict[str, Any]]:
    """
    hits_per_kw có thể là:
      - List[Dict] (mỗi phần tử đã là 1 hit)
      - List[List[Dict]] (mỗi keyword trả 1 list hit)
    pick_top1_per_kw=True: nếu là list các list thì chỉ lấy hit đầu mỗi keyword
    """
    flat: List[Dict[str, Any]] = []
    for item in hits_per_kw:
        if isinstance(item, list):
            if not item:
                continue
            flat.append(item[0] if pick_top1_per_kw else item)  # nếu False sẽ thêm cả list (ít dùng)
        elif isinstance(item, dict):
            flat.append(item)
        else:
            # bỏ qua kiểu lạ
            continue
    # nếu có phần tử là list (do pick_top1_per_kw=False), flatten nốt
    out: List[Dict[str, Any]] = []
    for x in flat:
        if isinstance(x, list):
            out.extend([h for h in x if isinstance(h, dict)])
        elif isinstance(x, dict):
            out.append(x)
    return out

def merge_hits_to_single_hit(
    hits_per_kw: Iterable[Any],
    max_snippet_chars: int = 1200,
    joiner: str = " … ",
    score_field_candidates: List[str] = ("rrf_score", "_score"),
) -> Optional[Dict[str, Any]]:
    """
    Gộp tất cả hit lại thành 1 hit duy nhất:
      - id: nối các _id bằng '+'
      - title: giá trị xuất hiện nhiều nhất (most common) trong các hit có title
      - page_from/page_to: min / max trong các hit có số trang
      - snippet: nối các đoạn text/snippet (loại trùng), cắt độ dài tổng max_snippet_chars
      - kw: danh sách từ khóa (field 'kw' hoặc '_kw') unique
      - score: tổng các điểm (ưu tiên 'rrf_score', fallback '_score')
    """
    hits = _flatten_hits(hits_per_kw, pick_top1_per_kw=True)
    if not hits:
        return None

    # 1) gom trường cơ bản
    ids = [str(h.get("_id") or "") for h in hits if h.get("_id")]
    titles = [h.get("title") for h in hits if h.get("title")]
    pages_from = [h.get("page_from") for h in hits if isinstance(h.get("page_from"), (int, float))]
    pages_to   = [h.get("page_to")   for h in hits if isinstance(h.get("page_to"), (int, float))]
    kwords = []
    for h in hits:
        for key in ("kw", "_kw"):
            if h.get(key):
                kwords.append(str(h[key]))

    # 2) chọn title phổ biến nhất
    title_final = None
    if titles:
        cnt = Counter(titles)
        title_final = cnt.most_common(1)[0][0]

    # 3) snippet: ưu tiên 'snippet', fallback '_source.text'; loại trùng, nối lại
    seen = set()
    parts = []
    for h in hits:
        txt = h.get("snippet")
        if not txt:
            src = h.get("_source") or {}
            txt = src.get("text")
        if not txt:
            continue
        t = str(txt).strip()
        if t and t not in seen:
            seen.add(t)
            parts.append(t)
    merged_snippet = joiner.join(parts)
    if len(merged_snippet) > max_snippet_chars:
        merged_snippet = merged_snippet[:max_snippet_chars].rstrip() + " …"

    # 4) điểm: tổng các score từ field ưu tiên
    total_score = 0.0
    for h in hits:
        sc = None
        for f in score_field_candidates:
            if h.get(f) is not None:
                try:
                    sc = float(h.get(f))
                    break
                except Exception:
                    pass
        if sc is not None:
            total_score += sc

    merged = {
        "_id": "+".join(ids) if ids else None,
        "title": title_final,
        "page_from": min(pages_from) if pages_from else None,
        "page_to": max(pages_to) if pages_to else None,
        "snippet": merged_snippet if merged_snippet else None,
        "kw": sorted(set(kwords)) if kwords else None,
        "score_sum": total_score,
        "sources_count": len(hits),
    }
    return merged


# ====== LLM Orchestrator (Step 6) ======
import json
from typing import List, Dict, Any

# Cho phép override model bằng ENV; mặc định nhắm "2.5 pro" (đổi fallback nếu cần)
MODEL_QA = os.getenv("MODEL_QA", "models/gemini-2.5-flash")
def _format_context_for_prompt(hits: List[Any]) -> str:
    """
    Biến danh sách hits (có thể là List[Dict] hoặc List[List[Dict]]) -> block context có đánh số [cit:N].
    KHÔNG GIỚI HẠN độ dài context — xuất toàn bộ.
    """
    # 🔧 Flatten an toàn: nếu phần tử là list → mở rộng, nếu là dict → giữ nguyên
    flat_hits = []
    for item in hits:
        if isinstance(item, list):
            flat_hits.extend(item)
        elif isinstance(item, dict):
            flat_hits.append(item)
        else:
            continue

    lines = []
    for i, h in enumerate(flat_hits, 1):
        if not isinstance(h, dict):
            continue

        title = str(h.get("title") or "").strip()
        pfrom = h.get("page_from") or "?"
        pto   = h.get("page_to") or "?"
        snippet = str(h.get("snippet") or "").strip().replace("\n", " ")

        # Nếu trống cả title & snippet → bỏ qua
        if not (title or snippet):
            continue

        line = f"[#cit={i}] {title} – p.{pfrom}–{pto}: {snippet}"
        lines.append(line)

    return "\n".join(lines)


def _build_qa_instruction() -> str:
    """
    Ràng buộc phong cách trả lời: NGẮN GỌN + DỄ ĐỌC + Có quyết định đủ/thiếu thông tin.
    Trả về JSON để dễ parse.
    """
    return (
        "Bạn là trợ lý học thuật. Chỉ sử dụng THÔNG TIN TRONG CONTEXT.\n"
        "- Nếu đủ thông tin để trả lời: tạo câu trả lời NGẮN GỌN, DỄ ĐỌC, có đánh dấu trích dẫn dạng [cit:1], [cit:2] theo các mục trong CONTEXT.\n"
        "- Nếu KHÔNG đủ thông tin: KHÔNG đoán. Trả trạng thái NEED_MORE.\n"
        "ĐỊNH DẠNG TRẢ VỀ: JSON duy nhất, theo schema:\n"
        "{\n"
        '  "status": "ANSWER" | "NEED_MORE",\n'
        '  "answer": "string (chỉ khi status=ANSWER, ngắn gọn, có [cit:N])",\n'
        '  "confidence": 0.0_to_1.0,\n'
        '  "reason": "string (giải thích ngắn vì sao thiếu/đủ)",\n'
        '  "suggested_top_k": 0  // khi NEED_MORE, gợi ý top_k mới (lớn hơn hiện tại)\n'
        "}\n"
        "Chỉ trả về JSON hợp lệ, không kèm văn bản nào khác."
    )

import re

_cit_pat = re.compile(r"\[cit:(\d+)\]")

def extract_citation_ids(answer: str) -> list[int]:
    return [int(m.group(1)) for m in _cit_pat.finditer(answer)]

import re

import re

def strip_inline_citations(text: str) -> str:
    # Xoá mọi block [cit:1] hoặc [cit:1, cit:2, ...]
    text = re.sub(r"\[(?:\s*cit:\s*\d+\s*(?:,\s*)?)+\]", "", text, flags=re.IGNORECASE)
    return _tidy_punctuation(text)

def _tidy_punctuation(s: str) -> str:
    # Xoá khoảng trắng trước dấu , . ; :
    s = re.sub(r"\s+,", ",", s)
    s = re.sub(r"\s+\.", ".", s)
    s = re.sub(r"\s+;", ";", s)
    s = re.sub(r"\s+:", ":", s)

    # Xử lý các cụm thừa sau khi gỡ cit
    s = re.sub(r",\s*\.", ".", s)     # ", ." -> "."
    s = re.sub(r"\s*,\s*,", ", ", s)  # ", ," -> ", "
    s = re.sub(r"\(\s+\)", "", s)     # "(   )" -> ""
    s = re.sub(r"\s{2,}", " ", s)     # nhiều space -> 1 space
    s = re.sub(r"\n\s+\n", "\n\n", s) # dọn khoảng trắng thừa giữa dòng

    return s.strip()


def format_references(ids: list[int], hits: list, llm_answer: str = "", max_refs: int = 6):
    """
    ids: danh sách [cit:N]; ánh xạ sang hits[N-1]
    hits: có thể là List[Dict] hoặc List[List[Dict]]
    llm_answer: câu trả lời từ model (có thể chứa [cit:N])
    Trả về tuple: (answer_cleaned, refs_block)
    """

    # --- 1. Flatten hits nếu có list lồng nhau ---
    flat_hits = []
    for h in hits:
        if isinstance(h, list):
            flat_hits.extend(h)
        elif isinstance(h, dict):
            flat_hits.append(h)
    hits = flat_hits

    # --- 2. Tạo danh sách nguồn tham khảo ---
    seen = set()
    refs = []
    for n in ids:
        if n < 1 or n > len(hits):
            continue
        if n in seen:
            continue
        seen.add(n)
        h = hits[n - 1]
        title = (h.get("title") or "").strip() or "Tài liệu"
        pfrom, pto = h.get("page_from"), h.get("page_to")

        if pfrom is not None and pto is not None:
            refs.append(f"- {title} — trang {pfrom}–{pto}")
        elif pfrom is not None:
            refs.append(f"- {title} — trang {pfrom}")
        else:
            refs.append(f"- {title}")

        if len(refs) >= max_refs:
            break

    # --- 3. Fallback nếu không có [cit:N] ---
    if not refs and hits:
        for i, h in enumerate(hits[: min(3, len(hits))], 1):
            title = (h.get("title") or "").strip() or "Tài liệu"
            pfrom, pto = h.get("page_from"), h.get("page_to")
            if pfrom is not None and pto is not None:
                refs.append(f"- {title} — trang {pfrom}–{pto}")
            elif pfrom is not None:
                refs.append(f"- {title} — trang {pfrom}")
            else:
                refs.append(f"- {title}")

    # --- 4. Xoá toàn bộ [cit:N] khỏi câu trả lời LLM ---
    answer_cleaned = re.sub(r"\[cit:\d+\]", "", llm_answer).strip()

    # --- 5. Tạo block hiển thị ---
    refs_block = "\n".join(refs)
    if refs_block:
        refs_block = f"\n\n📚 **Nguồn tham khảo:**\n{refs_block}"

    return answer_cleaned, refs_block


def build_qa_prompt(query_text: str, hits: List[Dict[str, Any]]) -> str:
    ctx = _format_context_for_prompt(hits)
    instruction = _build_qa_instruction()
    return (
        f"{instruction}\n\n"
        f"USER QUESTION:\n{query_text}\n\n"
        f"CONTEXT (nguồn đã trích lục, có [#cit=N]):\n{ctx}\n"
    )

def _call_gemini_json(prompt: str) -> Dict[str, Any]:
    """
    Gọi Gemini, cố gắng buộc JSON. Có fallback model nếu model chính không khả dụng.
    """
    models_try = [MODEL_QA]
    last_err = None
    for m in models_try:
        try:
            model = genai.GenerativeModel(m)
            # Một số SDK hỗ trợ response_mime_type, nhưng để an toàn ta vẫn ràng buộc bằng prompt
            resp = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2
                }
            )
            text = resp.text if hasattr(resp, "text") else (resp.candidates[0].content.parts[0].text if resp.candidates else "")
            # Chỉ nhận JSON
            text = text.strip()
            # Cắt guard nếu model lỡ thêm code fence
            if text.startswith("```"):
                text = text.strip("`")
                # có thể còn 'json\n{...}'
                if "\n" in text:
                    text = text.split("\n", 1)[1]
            return json.loads(text)
        except Exception as e:
            last_err = e
            continue
    # Nếu tất cả đều lỗi, trả NEED_MORE mặc định
    return {
        "status": "NEED_MORE",
        "answer": "",
        "confidence": 0.0,
        "reason": f"LLM error: {last_err}",
        "suggested_top_k": 0
    }

def generate_answer_or_retry(
    query_text: str,
    hits: List[Dict[str, Any]],
    current_top_k: int,
    max_top_k_cap: int = 50
) -> Dict[str, Any]:
    """
    Trả về 1 trong 2 nhánh:
    - {"status":"ANSWER","answer": "...","citations":[...], "confidence": float}
    - {"status":"RETRY","next_top_k": int, "reason": "..."}
    """
    # Heuristic nhanh: nếu context quá ít -> yêu cầu tăng top_k trước khi gọi LLM
    if len(hits) == 0:
        next_k = min(max(current_top_k * 2, current_top_k + 5), max_top_k_cap)
        return {"status": "RETRY", "next_top_k": next_k, "reason": "No retrieval hits."}

    prompt = build_qa_prompt(query_text, hits)
    out = _call_gemini_json(prompt)
    if not isinstance(out, dict) or "status" not in out:
        # Không parse được → thử tăng top_k
        next_k = min(max(current_top_k * 2, current_top_k + 5), max_top_k_cap)
        return {"status": "RETRY", "next_top_k": next_k, "reason": "LLM did not return valid JSON."}

    if out.get("status", "").upper() == "ANSWER":
        raw_answer = (out.get("answer") or "").strip()

        # 1) ids từ nội dung gốc
        ids = extract_citation_ids(raw_answer)

        # 2) gỡ [cit:N] + dọn dấu câu
        clean_answer = strip_inline_citations(raw_answer)

        # 3) refs (string, KHÔNG phải tuple)
        refs_block = format_references(ids, hits)  # <- trả về string

        final_text = clean_answer
        if refs_block:
            final_text = f"{final_text}\n\nNguồn tham khảo:\n{refs_block}"

        return {
            "status": "ANSWER",
            "answer": final_text,
            "confidence": float(out.get("confidence") or 0.0),
        }

    # NEED_MORE → đề nghị tăng top_k
    suggested = int(out.get("suggested_top_k") or 0)
    if suggested <= current_top_k:
        suggested = current_top_k * 2
    next_k = min(suggested, max_top_k_cap)

    return {
        "status": "RETRY",
        "next_top_k": next_k,
        "reason": out.get("reason") or "Model signaled insufficient context."
    }

# ====== Pipeline chạy hỏi-đáp có vòng lặp tăng top_k ======
def run_qa_pipeline(
    query_text: str,
    keywords: Optional[Union[str, Iterable[str]]] = None,
    filters: Optional[dict] = None,
    initial_top_k: int = 5,
    max_top_k_cap: int = 50,
    max_iters: int = 4,
):
    """
    Vòng lặp:
      1) hybrid_search(top_k=current_k)
      2) generate_answer_or_retry(...)
         - Nếu ANSWER: in và thoát
         - Nếu RETRY: lấy next_top_k (đã kẹp max_top_k_cap), tăng current_k và lặp
    """
    current_k = max(1, int(initial_top_k))
    for it in range(1, max_iters + 1):
        # Tăng rrf_window và num_candidates tương ứng để RRF có "đất" lựa chọn
        rrf_window = max(50, min(max_top_k_cap * 5, current_k * 5))
        knn_num_candidates = max(200, min(2000, current_k * 10))
        
        # 1) Lấy hits riêng cho từng keyword
        hits_per_kw: List[List[Dict[str, Any]]] = []
        for kw in keywords:
            hits_kw = hybrid_search(
                query_text=query_text,
                keywords=kw,              # CHỈ 1 keyword mỗi lần
                filters=filters,
                top_k=current_k,          # công bằng mỗi keyword lấy cùng top_k
                rrf_window=rrf_window,
                knn_num_candidates=knn_num_candidates,
                rrf_k=RRF_K,
            )
            hits_per_kw.append(hits_kw or [])
        # Không có kết quả truy xuất
        if not hits_per_kw:
            next_k = min(max_top_k_cap, max(current_k * 2, current_k + 5))
            if next_k == current_k:
                return {
                    "status": "INSUFFICIENT_RETRIEVAL",
                    "reason": "Không có tài liệu truy xuất và không thể tăng top_k thêm.",
                    "last_top_k": current_k,
                    "iters": it,
                }
            current_k = next_k
            continue

        result = generate_answer_or_retry(
            query_text=query_text,
            hits=hits_per_kw,
            current_top_k=current_k,
            max_top_k_cap=max_top_k_cap
        )

        if result.get("status") == "ANSWER":
            return {
                "status": "ANSWER",
                "answer": result.get("answer", "").strip(),
                "confidence": result.get("confidence", 0.0),
                "last_top_k": current_k,
                "iters": it,
            }

       # ❌ Chưa đủ thông tin → retry
        next_k = int(result.get("next_top_k") or 0)
        reason = result.get("reason") or "Model signaled insufficient context."
        if next_k <= current_k:
            next_k = min(max_top_k_cap, max(current_k * 2, current_k + 5))

        if next_k == current_k:
            return {
                "status": "INSUFFICIENT_RETRIEVAL",
                "reason": reason,
                "last_top_k": current_k,
                "iters": it,
            }
        current_k = next_k
        
        
    # Hết vòng lặp mà vẫn chưa có ANSWER
    return {
        "status": "INSUFFICIENT_RETRIEVAL",
        "reason": "Đã hết vòng lặp mà chưa đủ thông tin để trả lời.",
        "last_top_k": current_k,
        "iters": max_iters,
    }


# ====== Entry point ======
if __name__ == "__main__":
    # Ví dụ chạy:
    print(run_qa_pipeline(
        query_text="điều kiện xét tuyển thẳng",
        keywords=['điều kiện xét tuyển thẳng', 'xét tuyển thẳng'],
        filters=None,  # hoặc None để tìm toàn bộ
        initial_top_k=5,
        max_top_k_cap=20,
        max_iters=1
    ))
