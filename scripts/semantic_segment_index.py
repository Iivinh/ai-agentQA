import os, re, json, time, random, argparse
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import pdfplumber
from tqdm import tqdm
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers, exceptions
import google.generativeai as genai

# ===================== ENV & CLIENTS =====================
load_dotenv()

def get_es(es_url: Optional[str] = None) -> Elasticsearch:
    es_url = es_url or os.getenv("ES_URL", "http://localhost:9200")
    return Elasticsearch(es_url)

def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY chưa được thiết lập trong .env")
    genai.configure(api_key=api_key, transport="rest")
    
    
# === KẾT NỐI: Elasticsearch & Gemini ===
def check_connections():
    es_url   = os.getenv("ES_URL", "http://localhost:9200")
    es_index = os.getenv("ES_INDEX", "school_knowledge")
    embed_model = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")
    seg_model   = os.getenv("GEMINI_SEGMENT_MODEL", "gemini-2.5-flash")

    print("🔌 Kiểm tra Elasticsearch…")
    try:
        es = get_es(es_url)
        ok = es.ping()
        info = es.info() if ok else {}
        print(f"  • ES_URL      : {es_url}")
        print(f"  • Ping        : {'OK' if ok else 'FAIL'}")
        if ok:
            print(f"  • Cluster     : {info.get('cluster_name')}")
            print(f"  • ES version  : {info.get('version', {}).get('number')}")
            # Thử gọi cat.indices (an toàn nếu không có quyền, sẽ bắt lỗi)
            try:
                exists = es.indices.exists(index=es_index)
                print(f"  • Index '{es_index}': {'tồn tại' if exists else 'chưa có'}")
            except Exception as e:
                print(f"  • Không kiểm tra được index: {e}")
        else:
            print("⚠️  Không ping được Elasticsearch.")
    except Exception as e:
        print(f"❌ Lỗi Elasticsearch: {e}")

    print("\n🤖 Kiểm tra Gemini…")
    try:
        configure_gemini()
        # 1) thử embed một chuỗi ngắn
        r = genai.embed_content(model=embed_model, content="health check")
        dims = len(r.get("embedding", []))
        print(f"  • EMBED_MODEL : {embed_model}")
        print(f"  • Embed dims  : {dims if dims else 'UNKNOWN'}")

        # 2) thử generate_content rất ngắn (model phân đoạn)
        model = genai.GenerativeModel(seg_model)
        resp = model.generate_content("Chỉ trả lời: OK")
        txt = (resp.text or "").strip()
        print(f"  • SEGMENT_MODEL: {seg_model}")
        print(f"  • Gen sample   : {txt[:60]}")
        print("✅ Gemini OK")
    except Exception as e:
        print(f"❌ Lỗi Gemini: {e}")

def clean_pdf_text(text: str) -> str:
    """Chuẩn hoá text PDF, giữ xuống dòng đoạn (\n\n), tránh đứt từ."""
    text = text or ""
    text = re.sub(r'(\w)-\s*\n(\w)', r'\1\2', text, flags=re.UNICODE)  # nối từ bị gạch nối qua dòng
    text = text.replace('\r', '')
    # giữ \n\n làm ngắt đoạn, còn \n đơn -> space
    placeholder = "<<<PARA>>>"
    text = text.replace("\n\n", placeholder)
    text = re.sub(r'[ \t]*\n[ \t]*', ' ', text)  # \n đơn -> space
    text = text.replace(placeholder, "\n\n")
    text = re.sub(r'[ \t]+', ' ', text)  # chuẩn hoá khoảng trắng
    return text.strip()

def extract_pdf_pages(pdf_path: str, min_len: int = 20) -> List[Dict[str, Any]]:
    """Đọc từng trang và làm sạch. Bỏ trang quá ngắn."""
    pages: List[Dict[str, Any]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, p in enumerate(pdf.pages, start=1):
                raw = p.extract_text() or ""
                txt = clean_pdf_text(raw)
                if txt and len(txt) >= min_len:
                    pages.append({"page_num": i, "text": txt})
    except Exception as e:
        print(f"⚠️ Lỗi đọc {pdf_path}: {e}")
    return pages

def read_and_clean_pdfs(save: Optional[bool] = None, min_len: int = 20) -> Dict[str, List[Dict[str, Any]]]:
    """
    Đọc toàn bộ PDF trong PDF_DIR và làm sạch theo trang.
    - Mặc định KHÔNG lưu ra file. Chỉ lưu khi save=True hoặc env SAVE_CLEAN=1.
    - Trả về dict: {doc_id: [ {page_num, text}, ... ], ...}
    """
    # quyết định lưu hay không
    if save is None:
        save = os.getenv("SAVE_CLEAN", "0") == "1"

    PDF_DIR = os.getenv("PDF_DIR", "data/pdf")
    OUT_DIR = "clean"

    if not os.path.isdir(PDF_DIR):
        print(f"⚠️ Thư mục PDF không tồn tại: {PDF_DIR}")
        return {}

    pdfs = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    print(f"📂 Tìm thấy {len(pdfs)} file PDF trong {PDF_DIR}")

    results: Dict[str, List[Dict[str, Any]]] = {}
    for pdf_path in pdfs:
        base = os.path.basename(pdf_path)
        doc_id = os.path.splitext(base)[0]
        pages = extract_pdf_pages(pdf_path, min_len=min_len)
        if not pages:
            print(f"⚠️ Bỏ qua (không có text hợp lệ): {base}")
            continue

        results[doc_id] = pages
        print(f"✅ {base}: {len(pages)} trang hợp lệ")

        if save:
            os.makedirs(OUT_DIR, exist_ok=True)
            # lưu JSONL theo trang
            jsonl_path = os.path.join(OUT_DIR, f"{doc_id}.pages.jsonl")
            with open(jsonl_path, "w", encoding="utf-8") as f:
                for rec in pages:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            # lưu full TXT gộp trang
            fulltxt_path = os.path.join(OUT_DIR, f"{doc_id}.full.txt")
            with open(fulltxt_path, "w", encoding="utf-8") as f:
                for rec in pages:
                    f.write(f"=== Page {rec['page_num']} ===\n{rec['text']}\n\n")
            print(f"   ↳ Đã lưu: {jsonl_path}, {fulltxt_path}")

    return results

def group_pages_by_window(
    pages: List[Dict[str, Any]],
    block_size: int = 3,
    overlap: int = 1
) -> List[Dict[str, Any]]:
    """Gom N trang thành 1 block, trượt overlap."""
    blocks = []
    n = len(pages)
    i = 0
    step = block_size - overlap
    while i < n:
        j = min(i + block_size, n)
        block_pages = pages[i:j]
        if not block_pages:
            break
        text = "\n\n".join(p["text"] for p in block_pages if p["text"])
        blocks.append({
            "page_from": block_pages[0]["page_num"],
            "page_to":   block_pages[-1]["page_num"],
            "text": text.strip()
        })
        if j == n:
            break
        i += step
    return blocks

def _strip_code_fences(s: str) -> str:
    # Bỏ ```json ... ``` hoặc ``` ... ```
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json|JSON)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()

def _largest_json_object(s: str) -> Optional[str]:
    # Tìm khối JSON { ... } lớn nhất (cân ngoặc)
    start = None; depth = 0; best = None
    for i, ch in enumerate(s):
        if ch == '{':
            if depth == 0: start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    cand = s[start:i+1]
                    if not best or len(cand) > len(best):
                        best = cand
    return best

def _safe_json_loads(s: str) -> Optional[dict]:
    if not s: return None
    s = _strip_code_fences(s)
    # Thử parse trực tiếp
    try:
        return json.loads(s)
    except Exception:
        pass
    # Thử tìm khối { ... } lớn nhất
    blob = _largest_json_object(s)
    if blob:
        try:
            return json.loads(blob)
        except Exception:
            return None
    return None

def _sanitize_for_log(s: str) -> str:
    # bỏ control chars để log an toàn
    return ''.join(ch for ch in s if ch == '\n' or 32 <= ord(ch) <= 126 or ord(ch) >= 160).strip()


def segment_with_gemini(raw_block: str, model_name: Optional[str] = None,
                        max_retries: int = 3, save_raw: bool = False,
                        raw_path: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Gọi Gemini để cắt block thành các đoạn mạch lạc.
    Nếu không parse được JSON, fallback: trả 1 segment chứa toàn bộ raw_block.
    Khi save_raw=True, ghi nguyên response ra file để kiểm tra.
    """
    model_name = model_name or os.getenv("GEMINI_SEGMENT_MODEL", "gemini-2.5-flash")

    system_prompt = (
        "Bạn là công cụ phân đoạn văn bản học thuật/quy chế.\n"
        "Chia văn bản sau thành các đoạn mạch lạc theo ý nghĩa.\n"
        "- Không cắt giữa câu; giữ đúng thứ tự; không bỏ sót.\n"
        "Chỉ trả về JSON hợp lệ dạng:\n"
        "{\"segments\":[{\"title\":\"\",\"text\":\"...\"}, ...]}\n"
    )
    user_input = f"Văn bản:\n{raw_block}"

    model = genai.GenerativeModel(model_name)

    last_txt = ""
    for attempt in range(max_retries):
        try:
            resp = model.generate_content([system_prompt, user_input])
            txt = (resp.text or "").strip()
            last_txt = txt
            payload = _safe_json_loads(txt)
            if not payload:
                raise ValueError("LLM không trả JSON hợp lệ")

            segments = payload.get("segments", [])
            out: List[Dict[str, str]] = []
            for seg in segments:
                title = (seg.get("title") or "").strip()
                text  = (seg.get("text")  or "").strip()
                if text:
                    out.append({"title": title, "text": text})
            if out:
                # lưu raw nếu cần
                if save_raw and raw_path:
                    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
                    with open(raw_path, "w", encoding="utf-8") as f:
                        f.write(_sanitize_for_log(txt))
                return out
            else:
                raise ValueError("JSON hợp lệ nhưng không có segments")
        except Exception as e:
            if attempt == max_retries - 1:
                # Fallback: 1 segment = toàn block
                print(f"❌ Gemini segmentation lỗi: {e} → dùng fallback 1 segment.")
                if save_raw and raw_path:
                    try:
                        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
                        with open(raw_path, "w", encoding="utf-8") as f:
                            f.write(_sanitize_for_log(last_txt))
                    except Exception:
                        pass
                return [{"title": "", "text": raw_block}]
            time.sleep(2 ** attempt)



def segment_docs(
    pages_by_doc: Dict[str, List[Dict[str, Any]]],
    block_size: int = 3,
    overlap: int = 1,
    save: Optional[bool] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Gom trang -> block -> segment bằng Gemini.
    Trả về dict {doc_id: [segment,...]}.
    Nếu save=True hoặc SAVE_SEGMENT=1 thì lưu ra segments/<doc_id>.jsonl
    """
    if save is None:
        save = os.getenv("SAVE_SEGMENT", "0") == "1"

    out_all: Dict[str, List[Dict[str, Any]]] = {}
    os.makedirs("segments", exist_ok=True)

    for doc_id, pages in pages_by_doc.items():
        print(f"📑 {doc_id}: {len(pages)} trang → gom {block_size} trang 1 block (overlap={overlap})")
        blocks = group_pages_by_window(pages, block_size=block_size, overlap=overlap)
        segments: List[Dict[str, Any]] = []

        for idx, b in enumerate(blocks, start=1):
            rawfile = None
            want_save = save or (os.getenv("SAVE_SEGMENT", "0") == "1")
            if want_save:
                rawfile = os.path.join("segments", f"{doc_id}_block_{b['page_from']}-{b['page_to']}.raw.txt")
            segs = segment_with_gemini(
                b["text"],
                save_raw=want_save,
                raw_path=rawfile
            )
            for s in segs:
                s["page_from"] = b["page_from"]
                s["page_to"]   = b["page_to"]
            segments.extend(segs)


        out_all[doc_id] = segments
        print(f"   → {len(blocks)} blocks, Gemini trả {len(segments)} segments")

        if save and segments:
            seg_path = os.path.join("segments", f"{doc_id}.jsonl")
            with open(seg_path, "w", encoding="utf-8") as f:
                for seg in segments:
                    f.write(json.dumps(seg, ensure_ascii=False) + "\n")
            print(f"   ↳ Đã lưu {seg_path}")

    return out_all

def ensure_index(es: Elasticsearch, index_name: str, dims: int) -> None:
    try:
        if es.indices.exists(index=index_name):
            return
    except Exception:
        pass

    body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "doc_id":      {"type": "keyword"},
                "title":       {"type": "text"},
                "text":        {"type": "text"},
                "page_from":   {"type": "integer"},
                "page_to":     {"type": "integer"},
                "ingested_at": {"type": "date"},
                # ES 8/9: dense_vector native kNN (không cần plugin)
                "vector": {
                    "type": "dense_vector",
                    "dims": dims,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
    es.indices.create(index=index_name, body=body)
    print(f"🆕 Đã tạo index '{index_name}' (dims={dims})")
    
    
def embed_text(text: str, model_name: Optional[str] = None, max_retries: int = 4) -> List[float]:
    model_name = model_name or os.getenv("EMBED_MODEL", "models/gemini-embedding-001")
    for attempt in range(max_retries):
        try:
            r = genai.embed_content(
                model=model_name,
                content=text,
                task_type="retrieval_document"
            )
            vec = r.get("embedding", [])
            if not vec:
                raise RuntimeError("Empty embedding")
            return vec
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep((2 ** attempt) + random.uniform(0, 0.4))
    return []

    
def iter_actions_for_bulk(
    segments_by_doc: Dict[str, List[Dict[str, Any]]],
    embed_model: Optional[str] = None
):
    embed_model = embed_model or os.getenv("EMBED_MODEL", "models/gemini-embedding-001")
    for doc_id, segs in segments_by_doc.items():
        for i, s in enumerate(segs):
            title = (s.get("title") or "").strip()
            text  = (s.get("text")  or "").strip()
            if not text:
                continue
            # Embed
            vec = embed_text(text, model_name=embed_model)
            # Tạo action
            _id = f"{doc_id}-{s.get('page_from','')}-{s.get('page_to','')}-{i}"
            yield {
                "_op_type": "index",
                "_id": _id,
                "doc_id": doc_id,
                "title": title,
                "text": text,
                "page_from": int(s.get("page_from") or 0),
                "page_to": int(s.get("page_to") or 0),
                "ingested_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "vector": vec
            }



def embed_and_index(segments_by_doc: Dict[str, List[Dict[str, Any]]]) -> Tuple[int,int]:
    es_url   = os.getenv("ES_URL", "http://localhost:9200")
    es_index = os.getenv("ES_INDEX", "school_knowledge")
    embed_model = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")

    configure_gemini()
    es = get_es(es_url)

    # Lấy dims 1 lần để tạo mapping chính xác
    probe = genai.embed_content(model=embed_model, content="probe")
    dims = len(probe.get("embedding", [])) or 3072  # fallback 768 nếu API không trả

    ensure_index(es, es_index, dims)

    print("🚀 Bắt đầu embed + index …")
    success, fail = 0, 0
    # Gọi bulk theo batch giúp ổn định bộ nhớ
    batch, BATCH_SIZE = [], 200
    for act in iter_actions_for_bulk(segments_by_doc, embed_model=embed_model):
        # gắn index vào action
        act["_index"] = es_index
        batch.append(act)
        if len(batch) >= BATCH_SIZE:
            ok, err = helpers.bulk(es, batch, raise_on_error=False)
            success += ok; fail += len(err)
            batch.clear()
    if batch:
        ok, err = helpers.bulk(es, batch, raise_on_error=False)
        success += ok; fail += len(err)

    print(f"✅ Indexed: {success} | ❌ Errors: {fail}")
    return success, fail


if __name__ == "__main__":
    check_connections()
    pages_by_doc = read_and_clean_pdfs()
    segments_by_doc = segment_docs(pages_by_doc, block_size=5, overlap=1, save=True)
    embed_and_index(segments_by_doc)