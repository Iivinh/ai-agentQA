import os, google.generativeai as genai
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch

GEMINI_API_KEY = 
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

# ====== LLM Orchestrator (Step 6) ======
import json
from typing import List, Dict, Any

# Cho phép override model bằng ENV; mặc định nhắm "2.5 pro" (đổi fallback nếu cần)
MODEL_QA = os.getenv("MODEL_QA", "models/gemini-2.5-pro")
FALLBACK_MODELS = ["models/gemini-1.5-pro", "models/gemini-pro"]

def _format_context_for_prompt(hits: List[Dict[str, Any]], max_chars: int = 8000) -> str:
    """
    Biến danh sách hits -> block context có đánh số [cit:N].
    Mỗi mục: [#cit=N] {title p.page_from–page_to}: snippet
    """
    lines, used = [], 0
    for i, h in enumerate(hits, 1):
        title = (h.get("title") or "").strip()
        pfrom = h.get("page_from")
        pto   = h.get("page_to")
        snippet = (h.get("snippet") or "").strip().replace("\n", " ")
        line = f"[#cit={i}] {title} – p.{pfrom}–{pto}: {snippet}"
        if used + len(line) + 1 > max_chars:
            break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines)

def _build_qa_instruction() -> str:
    """
    Ràng buộc phong cách trả lời: NGẮN GỌN + DỄ ĐỌC + Có quyết định đủ/thiếu thông tin.
    Trả về JSON để dễ parse.
    """
    return (
        "Bạn là trợ lý học thuật. Chỉ sử dụng THÔNG TIN TRONG CONTEXT.\n"
        "- Nếu đủ thông tin để trả lời: tạo câu trả lời NGẮN GỌN, DỄ ĐỌC (<= 6 gạch đầu dòng hoặc 1 đoạn ngắn), có đánh dấu trích dẫn dạng [cit:1], [cit:2] theo các mục trong CONTEXT.\n"
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

def strip_inline_citations(answer: str) -> str:
    return _cit_pat.sub("", answer).replace("  ", " ").strip()

def format_references(ids: list[int], hits: list[dict], max_refs: int = 6) -> str:
    """
    ids: danh sách N theo [cit:N]; map về hits[N-1].
    Loại trùng, giữ theo thứ tự xuất hiện. Nếu trống → fallback lấy top 1–3 hit đầu.
    """
    seen = set()
    refs = []
    for n in ids:
        if n < 1 or n > len(hits): 
            continue
        if n in seen:
            continue
        seen.add(n)
        h = hits[n-1]
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

    # Fallback nếu model không chèn [cit:N]
    if not refs:
        for i, h in enumerate(hits[: min(3, len(hits))], 1):
            title = (h.get("title") or "").strip() or "Tài liệu"
            pfrom, pto = h.get("page_from"), h.get("page_to")
            if pfrom is not None and pto is not None:
                refs.append(f"- {title} — trang {pfrom}–{pto}")
            elif pfrom is not None:
                refs.append(f"- {title} — trang {pfrom}")
            else:
                refs.append(f"- {title}")
    return "\n".join(refs)


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
    models_try = [MODEL_QA] + FALLBACK_MODELS
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
        # 1) lấy danh sách id citation
        ids = extract_citation_ids(raw_answer)
        # 2) gỡ [cit:N] khỏi nội dung hiển thị
        clean_answer = strip_inline_citations(raw_answer)
        # 3) xây mục “Nguồn tham khảo”
        refs_block = format_references(ids, hits)
        final_text = f"{clean_answer}\n\nNguồn tham khảo:\n{refs_block}"
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


# # ====== Demo chạy thử ======
# if __name__ == "__main__":
#     results = hybrid_search(
#         # The `query_text` parameter is specifying the main search query text as "điều kiện xét tuyển
#         # thẳng năm nay", which translates to "conditions for direct admission this year" in English.
#         # This is the text that will be used to search for relevant documents.
#         query_text="điều kiện xét tuyển thẳng năm nay",
#         keywords="xét tuyển thẳng",
#         filters={"term": {"doc_id": "Quy_che_tuyen_sinh"}},  # có thể bỏ nếu muốn tìm toàn bộ
#         top_k=5
#     )
#     for i, r in enumerate(results, 1):
#         print(f"{i}. (RRF={r['rrf_score']:.4f}) {r['title']}  p.{r['page_from']}")
#         print(f"   {r['snippet']}\n")
# if __name__ == "__main__":
#     # 1) Retrieval như bạn đã có:
#     hits = hybrid_search(
#         query_text="điều kiện xét tuyển thẳng năm nay",
#         keywords="xét tuyển thẳng",
#         filters={"term": {"doc_id": "Quy_che_tuyen_sinh"}},
#         top_k=5
#     )

#     # 2) Gọi LLM Orchestrator:
#     result = generate_answer_or_retry(
#         query_text="điều kiện xét tuyển thẳng năm nay",
#         hits=hits,
#         current_top_k=5,
#         max_top_k_cap=50
#     )

#     # 3) Hành vi theo tín hiệu:
#     if result["status"] == "ANSWER":
#         print("\n=== TRẢ LỜI NGẮN GỌN ===")
#         print(result["answer"])
#         print(f"(confidence ~ {result.get('confidence', 0):.2f})")
#     else:
#         print("\n=== THIẾU THÔNG TIN – CẦN RETRIEVAL LẠI ===")
#         print("Lý do:", result.get("reason"))
#         print("Gợi ý tăng top_k lên:", result["next_top_k"])
# ====== Pipeline chạy hỏi-đáp có vòng lặp tăng top_k ======
def run_qa_pipeline(
    query_text: str,
    keywords: Optional[str] = None,
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

        print(f"\n--- ITER {it} | top_k={current_k} | rrf_window={rrf_window} | knn_candidates={knn_num_candidates} ---")

        hits = hybrid_search(
            query_text=query_text,
            keywords=keywords,
            filters=filters,
            top_k=current_k,
            rrf_window=rrf_window,
            knn_num_candidates=knn_num_candidates,
            rrf_k=RRF_K
        )

        # Nếu không có hit nào → tăng mạnh trước khi gọi LLM
        if not hits:
            # Bước an toàn: nhân đôi + cộng 5, kẹp trần
            next_k = min(max_top_k_cap, max(current_k * 2, current_k + 5))
            if next_k == current_k:
                print("❗Không có kết quả truy xuất và không thể tăng top_k thêm. Kết thúc.")
                break
            print(f"⚠️ Không có kết quả. Tăng top_k lên {next_k} rồi thử lại.")
            current_k = next_k
            continue

        result = generate_answer_or_retry(
            query_text=query_text,
            hits=hits,
            current_top_k=current_k,
            max_top_k_cap=max_top_k_cap
        )

        if result.get("status") == "ANSWER":
            print("\n=== TRẢ LỜI NGẮN GỌN ===")
            print(result["answer"])
            print(f"(confidence ~ {result.get('confidence', 0):.2f})")
            return

        # RETRY
        next_k = int(result.get("next_top_k") or 0)
        reason = result.get("reason") or "Model signaled insufficient context."
        if next_k <= current_k:
            # Nếu model đề xuất không tăng, tự tăng theo heuristic
            next_k = min(max_top_k_cap, max(current_k * 2, current_k + 5))

        print("\n=== THIẾU THÔNG TIN – CẦN RETRIEVAL LẠI ===")
        print("Lý do:", reason)
        print(f"Gợi ý tăng top_k lên: {next_k}")

        if next_k == current_k:
            print("❗Không thể tăng top_k thêm. Kết thúc.")
            break

        current_k = next_k

    # Nếu thoát vòng lặp mà chưa có ANSWER
    print("\n⛔ Kết thúc vòng lặp mà chưa đủ thông tin để trả lời.")
    print("• Gợi ý: tăng max_top_k_cap, nới max_iters, hoặc mở rộng nguồn dữ liệu/filters.")


# ====== Entry point ======
if __name__ == "__main__":
    # Ví dụ chạy:
    run_qa_pipeline(
        query_text="điều kiện xét tuyển thẳng năm nay",
        keywords="xét tuyển thẳng",
        filters={"term": {"doc_id": "Quy_che_tuyen_sinh"}},  # hoặc None để tìm toàn bộ
        initial_top_k=5,
        max_top_k_cap=50,
        max_iters=4
    )
