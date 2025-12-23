import os, re, json, time, random
from typing import List, Dict, Any, Optional
from datetime import datetime

import pdfplumber
from tqdm import tqdm
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers, exceptions
import google.generativeai as genai

# ---------- ENV ----------
load_dotenv()
ES_URL      = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX    = os.getenv("ES_INDEX", "school_knowledge")
PDF_DIR     = os.getenv("PDF_DIR", "data/pdf")
GEMINI_KEY  = os.getenv("GEMINI_API_KEY")  # 🔐 KHÔNG hardcode
EMBED_MODEL = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY chưa được thiết lập trong .env")

genai.configure(api_key=GEMINI_KEY)
es = Elasticsearch(ES_URL)

# ===================== PDF EXTRACT =====================
def extract_pdf_pages(pdf_path: str) -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, p in enumerate(pdf.pages, start=1):
                txt = p.extract_text() or ""
                txt = clean_pdf_text(txt)
                if txt and len(txt.strip()) > 20:  # bỏ đoạn quá ngắn
                    pages.append({"page_num": i, "text": txt})
    except Exception as e:
        print(f"⚠️ Lỗi đọc {pdf_path}: {e}")
    return pages

# ===================== CLEAN & SENTENCE TOKENIZE =====================
def clean_pdf_text(text: str) -> str:
    text = re.sub(r'(\w)-\s*\n(\w)', r'\1\2', text, flags=re.UNICODE)
    text = text.replace('\r', '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]*\n[ \t]*', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def sentence_tokenize_vi(text: str) -> List[str]:
    try:
        from underthesea import sent_tokenize
        sents = sent_tokenize(text)
    except Exception:
        sents = re.split(r'(?<=[\.!?…])\s+(?=[A-ZÀ-Ỵ])', text)
    return [s.strip() for s in sents if s and s.strip()]

def approx_token_len(s: str) -> int:
    return max(1, len(s) // 4)

def split_long_sentence(s: str, max_tokens: int) -> List[str]:
    parts = re.split(r'([,;:–—\(\)•\-])', s)
    segs: List[str] = []
    buf = ""
    for p in parts:
        if not p:
            continue
        if approx_token_len(buf + p) > max_tokens and buf:
            segs.append(buf.strip()); buf = p
        else:
            buf += p
    if buf: segs.append(buf.strip())

    out: List[str] = []
    for seg in segs:
        if approx_token_len(seg) <= max_tokens:
            out.append(seg); continue
        words = seg.split()
        OVERLAP = 20
        i = 0
        while i < len(words):
            cur: List[str] = []; cur_tok = 0
            while i < len(words) and cur_tok + approx_token_len(words[i]+' ') <= max_tokens:
                cur.append(words[i]); cur_tok += approx_token_len(words[i]+' '); i += 1
            if cur:
                out.append(' '.join(cur).strip())
                i = max(i - OVERLAP, i)
            else:
                # fallback cực đoan
                out.append(seg[:max_tokens*4])
                seg = seg[max_tokens*4:]; words = seg.split(); i = 0
    return out

def chunk_by_tokens(text: str, max_tokens: int = 800, overlap_tokens: int = 80) -> List[str]:
    sents = sentence_tokenize_vi(text)
    chunks: List[str] = []
    buf: List[str] = []; buf_tok = 0

    def flush():
        nonlocal buf, buf_tok, chunks
        if not buf: return
        merged = ' '.join(buf).strip()
        if merged: chunks.append(merged)
        if overlap_tokens > 0:
            keep: List[str] = []; t = 0
            for sent in reversed(buf):
                keep.append(sent); t += approx_token_len(sent+' ')
                if t >= overlap_tokens: break
            keep.reverse(); buf = keep
            buf_tok = sum(approx_token_len(s + ' ') for s in buf)
        else:
            buf, buf_tok = [], 0

    for s in sents:
        tok = approx_token_len(s + ' ')
        if tok > max_tokens:
            flush()
            for seg in split_long_sentence(s, max_tokens):
                if approx_token_len(seg) > max_tokens:
                    seg = seg[:max_tokens*4]
                chunks.append(seg.strip())
            buf, buf_tok = [], 0
            continue
        if buf_tok + tok > max_tokens:
            flush()
        buf.append(s); buf_tok += tok

    if buf: chunks.append(' '.join(buf).strip())
    return [c for c in chunks if c]

# ===================== EMBEDDING (batch + retry) =====================
def _retry_sleep(attempt: int):
    # exponential backoff + jitter
    time.sleep(min(60, (2 ** attempt) + random.random()))

def embed_texts(texts: List[str], batch_size: int = 8) -> List[List[float]]:
    vecs: List[List[float]] = []
    dims: Optional[int] = None

    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch = texts[i:i+batch_size]
        # API embed từng mục một (API hiện tại không multi-input)
        for t in batch:
            for attempt in range(5):
                try:
                    r = genai.embed_content(model=EMBED_MODEL, content=t)
                    v = r["embedding"]
                    if dims is None:  # xác nhận chiều động
                        dims = len(v)
                    if len(v) != dims:
                        raise ValueError(f"Chiều embedding không khớp: {len(v)} != {dims}")
                    vecs.append(v)
                    break
                except Exception as e:
                    if attempt == 4:
                        # log ngắn nội dung gây lỗi để debug
                        print(f"❌ Embed lỗi sau 5 lần. Nội dung (50 ký tự): {t[:50]!r}. Lỗi: {e}")
                        raise
                    _retry_sleep(attempt)
    return vecs, (dims or 0)

# ===================== INDEX MANAGEMENT (Elasticsearch 8/9) =====================
def build_index_body(dims: int) -> Dict[str, Any]:
    return {
        "settings": {
            "analysis": {
                "analyzer": {
                    "vn_icu": {
                        "type": "custom",
                        "tokenizer": "icu_tokenizer",
                        "filter": ["lowercase", "icu_folding"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id":   {"type": "keyword"},
                "title":    {"type": "keyword"},
                "text":     {"type": "text", "analyzer": "vn_icu"},
                # ES 8/9: dùng dense_vector indexable + HNSW
                "vector": {
                    "type": "dense_vector",
                    "dims": dims,
                    "index": True,
                    "similarity": "cosine",
                    "index_options": {"type": "hnsw", "m": 16, "ef_construction": 128}
                },
                "page_from":      {"type": "integer"},
                "page_to":        {"type": "integer"},
                "effective_date": {"type": "date"},
                "version":        {"type": "keyword"},
                "tags":           {"type": "keyword"}
            }
        }
    }

def ensure_index(es_client: Elasticsearch, index_name: str, dims: int):
    if es_client.indices.exists(index=index_name):
        # kiểm tra dims hiện tại (nếu cần, có thể đọc mapping và so)
        return
    es_client.indices.create(index=index_name, body=build_index_body(dims))

def safe_bulk(es_client: Elasticsearch, actions: List[Dict[str, Any]]):
    try:
        helpers.bulk(es_client.options(request_timeout=180), actions)
    except exceptions.BulkIndexError as e:
        example = e.errors[0] if e.errors else {}
        print("❌ BulkIndexError (ví dụ 1 lỗi):", json.dumps(example, ensure_ascii=False, indent=2))
        raise

def delete_old_docs(es_client: Elasticsearch, index_name: str, doc_id: str):
    """Xoá tài liệu cũ theo doc_id trước khi index lại (idempotent)."""
    try:
        es_client.delete_by_query(
            index=index_name,
            body={"query": {"term": {"doc_id": doc_id}}},
            wait_for_completion=True,
            refresh=True,
            conflicts="proceed",
            slices="auto"
        )
    except Exception as e:
        print(f"⚠️ delete_by_query thất bại (doc_id={doc_id}): {e}")

# ===================== BULK INDEX PDF =====================
def index_pdf(pdf_path: str, max_tokens: int = 800, overlap_tokens: int = 80):
    base = os.path.basename(pdf_path)
    doc_id = os.path.splitext(base)[0]

    pages = extract_pdf_pages(pdf_path)
    if not pages:
        print(f"⚠️ Bỏ qua (không có text): {base}")
        return

    chunks: List[Dict[str, Any]] = []
    for p in pages:
        page_text = p["text"]
        for ch in chunk_by_tokens(page_text, max_tokens=max_tokens, overlap_tokens=overlap_tokens):
            chunks.append({
                "text": ch,
                "page_from": p["page_num"],
                "page_to": p["page_num"]
            })

    if not chunks:
        print(f"⚠️ Bỏ qua (không tạo được chunk): {base}")
        return

    texts = [c["text"] for c in chunks]
    vectors, dims = embed_texts(texts)

    ensure_index(es, ES_INDEX, dims)

    # dọn cũ trước khi bơm mới
    delete_old_docs(es, ES_INDEX, doc_id)

    actions = []
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for i, (c, v) in enumerate(zip(chunks, vectors), start=1):
        # _id idempotent: doc_id-page
        _id = f"{doc_id}:{c['page_from']}:{i}"
        actions.append({
            "_op_type": "index",
            "_index": ES_INDEX,
            "_id": _id,
            "_source": {
                "doc_id": doc_id,
                "title": base,
                "text": c["text"],
                "vector": v,
                "page_from": c["page_from"],
                "page_to": c["page_to"],
                "effective_date": today,
                "version": "1.0",
                "tags": ["pdf_import"]
            }
        })

    safe_bulk(es, actions)
    print(f"✅ Indexed {len(actions)} chunks từ {base}")

# ===================== MAIN =====================
def main():
    if not os.path.isdir(PDF_DIR):
        print(f"⚠️ Thư mục PDF không tồn tại: {PDF_DIR}")
        return
    pdfs = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    print(f"📂 Tìm thấy {len(pdfs)} file PDF trong {PDF_DIR}")
    for pdf in pdfs:
        index_pdf(pdf)

# if __name__ == "__main__":
#     main()
load_dotenv()
es = Elasticsearch(os.getenv("ES_URL", "http://localhost:9200"))
ES_INDEX = os.getenv("ES_INDEX", "school_knowledge")

# Xóa toàn bộ index (sẽ xóa cả mapping + data)
es.indices.delete(index=ES_INDEX, ignore_unavailable=True)
print(f"✅ Đã xóa index {ES_INDEX}")