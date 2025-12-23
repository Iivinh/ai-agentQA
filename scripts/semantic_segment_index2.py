# -*- coding: utf-8 -*-
"""
PDF → (one-shot per file) plan bằng anchors câu (mịn) → materialize → auto-refine → embed → index (Elasticsearch)
- KHÔNG dùng ENV, KHÔNG dùng argparse.
- ÉP hạt mịn bằng ràng buộc độ dài + hậu kiểm tự chia nhỏ.

Yêu cầu:
  pip install pdfplumber google-generativeai tqdm elasticsearch==8.* regex
"""

import os, json, time, random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import pdfplumber
from tqdm import tqdm
from elasticsearch import Elasticsearch, helpers
import google.generativeai as genai
import regex as re

# ===================== CẤU HÌNH TRỰC TIẾP =====================
PDF_DIR        = "data/pdf"
ES_URL         = "http://localhost:9200"
ES_INDEX       = "school_knowledge"
GEMINI_API_KEY = "AIzaSyAJlOwMZm7n08S-vqfzgISw1P-0D-UcnlI"
EMBED_MODEL    = "models/gemini-embedding-001"
SEGMENT_MODEL  = "gemini-2.5-pro"
PLAN_BATCH_PAGES = 10 
# Lưu kiểm tra
SAVE_CLEAN     = True
SAVE_PLAN      = True
SAVE_PLAN_RAW  = False
SAVE_SEGMENT   = True
USE_EXISTING_PLAN = True

# Kiểm soát độ hạt
ANCHOR_MAX_CHARS   = 120
TARGET_SEG_CHARS   = 2000     # mục tiêu  ~900 ký tự/segment
MIN_SEG_CHARS      = 0     # đừng để quá ngắn (trừ tiêu đề)
MAX_SEG_CHARS      = 3000    # trần tuyệt đối; > trần sẽ bị tự chia nhỏ
MAX_SPANS_PER_SEG  = 2       # mỗi segment bắc tối đa qua 2 trang (nếu dài hơn → LLM phải chia nhỏ)
SNAP_TO_BOUNDARY   = True
MIN_CHUNK_CHARS    = 8

# ===================== KẾT NỐI & KIỂM TRA =====================
def get_es() -> Elasticsearch:
    return Elasticsearch(ES_URL)

def configure_gemini():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "PUT_YOUR_GEMINI_API_KEY_HERE":
        raise RuntimeError("Chưa cấu hình GEMINI_API_KEY ở đầu file.")
    genai.configure(api_key=GEMINI_API_KEY, transport="rest")

def check_connections():
    print("🔌 Kiểm tra Elasticsearch…")
    try:
        es = get_es()
        ok = es.ping()
        info = es.info() if ok else {}
        print(f"  • ES_URL: {ES_URL} | Ping: {'OK' if ok else 'FAIL'}")
        if ok:
            print(f"  • Cluster: {info.get('cluster_name')} | Version: {info.get('version',{}).get('number')}")
            try:
                exists = es.indices.exists(index=ES_INDEX)
                print(f"  • Index '{ES_INDEX}': {'tồn tại' if exists else 'chưa có'}")
            except Exception as e:
                print(f"  • Không kiểm tra được index: {e}")
    except Exception as e:
        print(f"❌ Lỗi Elasticsearch: {e}")

    print("\n🤖 Kiểm tra Gemini…")
    try:
        configure_gemini()
        r = genai.embed_content(model=EMBED_MODEL, content="health check")
        dims = len(r.get("embedding", []))
        print(f"  • EMBED_MODEL: {EMBED_MODEL} (dims={dims or 'UNKNOWN'})")
        txt = (genai.GenerativeModel(SEGMENT_MODEL)
               .generate_content("Chỉ trả lời: OK").text or "").strip()
        print(f"  • SEGMENT_MODEL: {SEGMENT_MODEL} | Gen sample: {txt[:40]}")
        print("✅ Gemini OK")
    except Exception as e:
        print(f"❌ Lỗi Gemini: {e}")

# ===================== PDF CLEANING =====================
def clean_pdf_text(text: str) -> str:
    text = text or ""
    text = re.sub(r'(\w)-\s*\n(\w)', r'\1\2', text, flags=re.UNICODE)
    text = text.replace('\r', '')
    placeholder = "<<<PARA>>>"
    text = text.replace("\n\n", placeholder)
    text = re.sub(r'[ \t]*\n[ \t]*', ' ', text)
    text = text.replace(placeholder, "\n\n")
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_pdf_pages(pdf_path: str, min_len: int = 20) -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, p in enumerate(pdf.pages, start=1):
                raw = p.extract_text() or ""
                txt = clean_pdf_text(raw)
                if txt and len(txt) >= min_len:
                    pages.append({"page_num": i, "text": txt})
    except Exception as e:
        print(f"⚠️ Lỗi đọc {os.path.basename(pdf_path)}: {e}")
    return pages

def read_and_clean_pdfs() -> Dict[str, List[Dict[str, Any]]]:
    if not os.path.isdir(PDF_DIR):
        print(f"⚠️ Thư mục PDF không tồn tại: {PDF_DIR}")
        return {}
    pdfs = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    print(f"📂 Tìm thấy {len(pdfs)} file PDF trong {PDF_DIR}")

    results: Dict[str, List[Dict[str, Any]]] = {}
    for pdf_path in pdfs:
        base = os.path.basename(pdf_path); doc_id = os.path.splitext(base)[0]
        pages = extract_pdf_pages(pdf_path, min_len=20)
        if not pages:
            print(f"⚠️ Bỏ qua (không có text hợp lệ): {base}")
            continue
        results[doc_id] = pages
        print(f"✅ {base}: {len(pages)} trang hợp lệ")
        if SAVE_CLEAN:
            os.makedirs("clean", exist_ok=True)
            with open(os.path.join("clean", f"{doc_id}.pages.jsonl"), "w", encoding="utf-8") as f:
                for rec in pages: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            with open(os.path.join("clean", f"{doc_id}.full.txt"), "w", encoding="utf-8") as f:
                for rec in pages: f.write(f"=== Page {rec['page_num']} ===\n{rec['text']}\n\n")
            print(f"   ↳ Đã lưu clean/{doc_id}.pages.jsonl & clean/{doc_id}.full.txt")
    return results

# ===================== JSON HELPERS =====================
def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json|JSON)?\s*", "", s); s = re.sub(r"\s*```$", "", s)
    return s.strip()

def _largest_json_object(s: str) -> Optional[str]:
    start=None; depth=0; best=None
    for i,ch in enumerate(s):
        if ch=='{':
            if depth==0: start=i
            depth+=1
        elif ch=='}':
            if depth>0:
                depth-=1
                if depth==0 and start is not None:
                    cand=s[start:i+1]
                    if not best or len(cand)>len(best): best=cand
    return best

def _safe_json_loads(s: str) -> Optional[dict]:
    if not s: return None
    s=_strip_code_fences(s)
    try: return json.loads(s)
    except Exception: pass
    blob=_largest_json_object(s)
    if blob:
        try: return json.loads(blob)
        except Exception: return None
    return None

def _sanitize_for_log(s: str) -> str:
    return ''.join(ch for ch in s if ch=='\n' or 32<=ord(ch)<=126 or ord(ch)>=160).strip()

# ===================== ANCHOR & SNAP HELPERS =====================
_PUNCT = set(list(".,;:!?…“”\"'()[]{}<>—–-•·/\\|"))
def _is_space(c: str) -> bool: return c.isspace()
def _is_punct(c: str) -> bool: return c in _PUNCT
def _is_alnum(c: str) -> bool: return c.isalnum()
def _at_boundary_left(t: str, i: int) -> bool: return i<=0 or _is_space(t[i-1]) or _is_punct(t[i-1])
def _at_boundary_right(t: str, i: int) -> bool: return i>=len(t) or _is_space(t[i]) or _is_punct(t[i])

def _snap_span_to_word_sentence(t: str, start: int, end: int) -> Tuple[int,int]:
    n=len(t); start=max(0,min(start,n)); end=max(start,min(end,n))
    if start<end:
        if start>0 and _is_alnum(t[start-1]) and start<n and _is_alnum(t[start]):
            if start-1>=0 and (_at_boundary_left(t,start-1) or _is_space(t[start-1]) or _is_punct(t[start-1])):
                start-=1
            else:
                while start>0 and _is_alnum(t[start-1]) and not _at_boundary_left(t,start): start-=1
        if end>0 and end<n and _is_alnum(t[end-1]) and _is_alnum(t[end]):
            if end+1<=n: end+=1
            while end<n and _is_alnum(t[end]) and not _at_boundary_right(t,end): end+=1
        while end<n and not _at_boundary_right(t,end) and not _is_space(t[end]) and not _is_punct(t[end]): end+=1
    return (start,end)

def _needs_joiner(prev_text: str) -> bool:
    if not prev_text: return False
    return not bool(re.search(r'[\s\.\!\?\:\;\,\)\]\}]+$', prev_text))

def _normalize_for_match(s: str) -> str:
    s = s.replace("\r"," ").strip()
    s = re.sub(r"\s+"," ",s)
    return s

def _anchor_to_regex(anchor: str) -> re.Pattern:
    a=_normalize_for_match(anchor)
    esc=re.escape(a); esc=re.sub(r"\\\s+", r"\\s+", esc)
    return re.compile(esc, re.IGNORECASE|re.UNICODE)

def _build_manifest_for_batch(batch_pages: List[Dict[str, Any]]) -> str:
    """Tạo manifest <<<PAGE i>>> cho 1 lô (đánh số trang 1..len(batch))."""
    lines=[]
    for i, p in enumerate(batch_pages, start=1):
        t=(p.get("text") or "").rstrip()
        lines.append(f"<<<PAGE {i}>>>")
        lines.append(t)
        lines.append("")
    return "\n".join(lines)


# ===================== GEMINI: ONE-SHOT PLAN (ANCHORS – HẠT MỊN) =====================
def one_shot_plan_for_doc_pages_by_sent_anchors(doc_id: str, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    model = genai.GenerativeModel(SEGMENT_MODEL)

    all_segments = []
    total_pages = len(pages)
    if total_pages == 0:
        return {"segments": []}

    # Lặp theo lô 10 trang
    for batch_start in range(0, total_pages, PLAN_BATCH_PAGES):
        batch_end = min(total_pages, batch_start + PLAN_BATCH_PAGES)
        batch_pages = pages[batch_start:batch_end]
        local_count = len(batch_pages)

        manifest = _build_manifest_for_batch(batch_pages)

        system_prompt = (
            "Bạn là công cụ LẬP KẾ HOẠCH phân đoạn THEO TRANG cho văn bản pháp quy.\n"
            "Đầu vào là một NHÓM TRANG có đánh dấu '<<<PAGE k>>>', với k chạy từ 1 đến {N} (chỉ trong lô này).\n"
            "Hãy chia thành NHIỀU đoạn (segment) mạch lạc, MỖI segment ~{T} ký tự (tối thiểu {MIN}, tối đa {MAX}); "
            "nếu dài hơn {MAX} PHẢI tách nhỏ. KHÔNG được gộp cả CHƯƠNG nếu vượt {MAX}.\n"
            "Mỗi segment bắc qua tối đa {SP} trang TRONG LÔ này; KHÔNG THAM CHIẾU sang trang ngoài lô.\n"
            "TRẢ VỀ JSON KẾ HOẠCH VỚI ANCHORS câu đầu/cuối cho từng span:\n"
            "{{\"segments\":[{{\"title\":\"ngắn gọn\",\"spans\":[{{\"page\":1,\"begin\":\"...\",\"end\":\"...\"}}, ...]}} , ...]}}\n"
            "- 'page' là CHỈ SỐ TRONG LÔ (1..{N}); 'begin'/'end' là NGUYÊN VĂN câu đầu/cuối cắt ngắn ≤ {A} ký tự."
        ).format(N=local_count, T=TARGET_SEG_CHARS, MIN=MIN_SEG_CHARS, MAX=MAX_SEG_CHARS,
                 SP=MAX_SPANS_PER_SEG, A=ANCHOR_MAX_CHARS)

        user_prompt = "Dưới đây là nội dung theo TRANG của lô hiện tại. Hãy trả về kế hoạch đúng yêu cầu:\n\n" + manifest

        # Gọi LLM
        resp = model.generate_content([system_prompt, user_prompt])
        txt = (resp.text or "").strip()
        if SAVE_PLAN_RAW:
            os.makedirs("segments", exist_ok=True)
            with open(os.path.join("segments", f"{doc_id}.plan.batch_{batch_start+1}_{batch_end}.raw.txt"),
                      "w", encoding="utf-8") as f:
                f.write(_sanitize_for_log(txt))

        plan_local = _safe_json_loads(txt)

        # Fallback nếu JSON hỏng: 1 segment gom cả lô, neo đầu/cuối mỗi trang trong lô
        if not plan_local or "segments" not in plan_local:
            spans=[]
            for i, p in enumerate(batch_pages, start=1):
                t=(p.get("text") or "")
                t_norm=_normalize_for_match(t)
                if not t_norm: continue
                begin=t_norm[:ANCHOR_MAX_CHARS]; end=t_norm[-ANCHOR_MAX_CHARS:]
                spans.append({"page": i, "begin": begin, "end": end})
            plan_local={"segments":[{"title":"", "spans":spans}]}

        # Điều chỉnh 'page' từ LOCAL → GLOBAL (cộng offset batch)
        page_offset = batch_start  # vì local page bắt đầu 1 → global = offset + local
        for seg in plan_local.get("segments", []):
            fixed_spans=[]
            for sp in seg.get("spans", []):
                try:
                    local_pid = int(sp["page"])
                except Exception:
                    continue
                global_pid = local_pid + page_offset
                # Bảo vệ biên
                if 1 <= global_pid <= total_pages:
                    sp2 = dict(sp)
                    sp2["page"] = global_pid
                    fixed_spans.append(sp2)
            if fixed_spans:
                all_segments.append({
                    "title": (seg.get("title") or "").strip(),
                    "spans": fixed_spans
                })

    # Gộp thành 1 kế hoạch chung
    out_plan = {"segments": all_segments}

    if SAVE_PLAN:
        os.makedirs("segments", exist_ok=True)
        with open(os.path.join("segments", f"{doc_id}.plan.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(out_plan, ensure_ascii=False, indent=2))
        print(f"   ↳ Đã lưu kế hoạch (anchors, theo lô {PLAN_BATCH_PAGES} trang): segments/{doc_id}.plan.json")

    return out_plan

# ===================== MATERIALIZE TỪ ANCHORS =====================
def apply_page_anchor_plan_to_segments(plan: Dict[str, Any], pages: List[Dict[str, Any]], joiner: str="\n\n", keep_prov: bool=True) -> List[Dict[str, Any]]:
    out=[]
    for seg in plan.get("segments", []):
        title=(seg.get("title") or "").strip()
        spans=sorted(seg.get("spans", []), key=lambda sp: int(sp["page"]))

        parts=[]; pf=None; pt=None; prov=[]
        for idx, sp in enumerate(spans):
            pid=int(sp["page"])
            if not (1<=pid<=len(pages)): continue
            raw=pages[pid-1].get("text") or ""
            hay_norm=_normalize_for_match(raw)

            begin=(sp.get("begin") or "")[:ANCHOR_MAX_CHARS]
            end  =(sp.get("end")   or "")[:ANCHOR_MAX_CHARS]

            # tìm begin (đầu tiên) và end (cuối cùng) tolerant khoảng trắng
            s_idx=0; e_idx=len(raw)
            if begin:
                m=list(_anchor_to_regex(begin).finditer(hay_norm))
                if m: s_idx=m[0].start()
            if end:
                m=list(_anchor_to_regex(end).finditer(hay_norm))
                if m: e_idx=max(s_idx+1, m[-1].end())

            if SNAP_TO_BOUNDARY and s_idx<e_idx:
                s_idx, e_idx = _snap_span_to_word_sentence(raw, s_idx, min(e_idx, len(raw)))

            chunk=raw[s_idx:e_idx]

            if idx>0 and parts and parts[-1] and _needs_joiner(parts[-1]): parts.append(joiner)
            parts.append(chunk)

            pg=pages[pid-1]["page_num"]
            pf = pg if pf is None else min(pf, pg)
            pt = pg if pt is None else max(pt, pg)

            if keep_prov:
                prov.append({"page": pid, "begin": begin, "end": end, "start": s_idx, "finish": e_idx})

        text="".join(parts).strip()
        if text:
            rec={"title": title, "text": text, "page_from": pf or 0, "page_to": pt or 0}
            if keep_prov: rec["spans"]=prov
            out.append(rec)
    return out

# ===================== HẬU KIỂM & TỰ CHIA NHỎ =====================
_SENT_SPLIT = re.compile(r"(?<=[\.\!\?\:;])\s+(?=[A-ZÀ-ỲĀĂĐĨŨƠƯẠ-ỹ])", re.UNICODE)
def _split_into_paras(text: str) -> List[str]:
    parts=[p.strip() for p in text.split("\n\n")]
    return [p for p in parts if p]

def _split_into_sentences(text: str) -> List[str]:
    sents = _SENT_SPLIT.split(text.strip())
    return [s.strip() for s in sents if s.strip()]

def _natural_refine(text: str, target: int, min_len: int, max_len: int) -> List[str]:
    """Chia text thành các mảnh gần target; ưu tiên ngắt đoạn, sau đó câu; đảm bảo min/max."""
    if len(text) <= max_len:
        return [text.strip()]

    paras=_split_into_paras(text)
    if len(paras)<=1:
        # không có ngắt đoạn → chia theo câu
        sents=_split_into_sentences(text)
        chunks=[]; buf=""
        for s in sents:
            if not buf: buf=s
            elif len(buf)+1+len(s) <= max_len:
                buf = buf + " " + s
            else:
                chunks.append(buf.strip()); buf=s
        if buf: chunks.append(buf.strip())
        # gộp các mảnh ngắn để đạt tối thiểu
        merged=[]; cur=""
        for c in chunks:
            if not cur: cur=c
            elif len(cur) < min_len or len(cur)+2+len(c) < min_len:
                cur = cur + "\n\n" + c
            else:
                merged.append(cur.strip()); cur=c
        if cur: merged.append(cur.strip())
        return merged

    # có ngắt đoạn → gộp đoạn gần target
    chunks=[]; cur=""
    for p in paras:
        if not cur:
            cur=p
        elif len(cur)+2+len(p) <= max_len:
            cur = cur + "\n\n" + p
        else:
            # nếu cur còn quá nhỏ, thử ghép mạnh tay thêm 1 đoạn
            if len(cur) < min_len and len(cur)+2+len(p) <= (max_len + max_len//5):
                cur = cur + "\n\n" + p
            else:
                chunks.append(cur.strip()); cur=p
    if cur: chunks.append(cur.strip())

    # nếu mảnh nào vẫn > max_len, rạch tiếp theo câu
    refined=[]
    for c in chunks:
        if len(c) > max_len:
            refined.extend(_natural_refine(c, target, min_len, max_len))
        else:
            refined.append(c)
    return refined

def refine_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bảo đảm mọi segment nằm trong [MIN_SEG_CHARS, MAX_SEG_CHARS] (trừ segment chỉ tiêu đề)."""
    out=[]
    for seg in segments:
        txt=seg["text"]; title=seg.get("title","").strip()
        if len(txt) <= MAX_SEG_CHARS:
            out.append(seg); continue

        # tách tự nhiên
        parts=_natural_refine(txt, TARGET_SEG_CHARS, MIN_SEG_CHARS, MAX_SEG_CHARS)
        for i, piece in enumerate(parts, start=1):
            rec=dict(seg)
            rec["text"]=piece
            rec["title"]= f"{title} (phần {i})" if title else f"(phần {i})"
            # provenance: giữ page_from/to của bản gốc
            out.append(rec)
    return out

# ===================== SEGMENT DRIVER (ANCHORS + REFINE) =====================
def segment_docs_pages_with_anchors(pages_by_doc: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    out_all={}
    os.makedirs("segments", exist_ok=True)
    for doc_id, pages in pages_by_doc.items():
        print(f"📑 {doc_id}: {len(pages)} trang → anchors (hạt mịn)")
        plan_path=os.path.join("segments", f"{doc_id}.plan.json")
        if USE_EXISTING_PLAN and os.path.isfile(plan_path):
            with open(plan_path,"r",encoding="utf-8") as f: plan=json.load(f)
            print(f"   ↳ Dùng kế hoạch có sẵn: {plan_path}")
        else:
            plan=one_shot_plan_for_doc_pages_by_sent_anchors(doc_id, pages)

        segs = apply_page_anchor_plan_to_segments(plan, pages, joiner="\n\n", keep_prov=True)
        segs_refined = refine_segments(segs)
        print(f"   → {len(segs)} segments (raw) → {len(segs_refined)} segments (refined)")
        out_all[doc_id]=segs_refined

        if SAVE_SEGMENT and segs_refined:
            with open(os.path.join("segments", f"{doc_id}.jsonl"), "w", encoding="utf-8") as f:
                for s in segs_refined: f.write(json.dumps(s, ensure_ascii=False) + "\n")
            print(f"   ↳ Đã lưu segments/{doc_id}.jsonl")
    return out_all

# ===================== ELASTICSEARCH INDEXING =====================
def ensure_index(es: Elasticsearch, index_name: str, dims: int) -> None:
    try:
        if es.indices.exists(index=index_name): return
    except Exception: pass
    body={
        "settings":{"number_of_shards":1,"number_of_replicas":0},
        "mappings":{
            "properties":{
                "doc_id":{"type":"keyword"},
                "title":{"type":"text"},
                "text":{"type":"text"},
                "page_from":{"type":"integer"},
                "page_to":{"type":"integer"},
                "ingested_at":{"type":"date"},
                "vector":{"type":"dense_vector","dims":dims,"index":True,"similarity":"cosine"}
            }
        }
    }
    es.indices.create(index=index_name, body=body)
    print(f"🆕 Đã tạo index '{index_name}'")

def embed_text(text: str, max_retries: int=4) -> List[float]:
    for attempt in range(max_retries):
        try:
            r=genai.embed_content(model=EMBED_MODEL, content=text, task_type="retrieval_document")
            vec=r.get("embedding", [])
            if not vec: raise RuntimeError("Empty embedding")
            return vec
        except Exception:
            if attempt==max_retries-1: raise
            time.sleep((2**attempt)+random.uniform(0,0.4))
    return []

def iter_actions_for_bulk(segments_by_doc: Dict[str, List[Dict[str, Any]]]):
    for doc_id, segs in segments_by_doc.items():
        for i, s in enumerate(segs):
            title=(s.get("title") or "").strip(); text=(s.get("text") or "").strip()
            if not text: continue
            vec=embed_text(text)
            _id=f"{doc_id}-{s.get('page_from','')}-{s.get('page_to','')}-{i}"
            yield {
                "_op_type":"index","_id":_id,"_index":ES_INDEX,
                "doc_id":doc_id,"title":title,"text":text,
                "page_from":int(s.get("page_from") or 0),
                "page_to":int(s.get("page_to") or 0),
                "ingested_at":datetime.utcnow().isoformat(timespec="seconds")+"Z",
                "vector":vec
            }

def embed_and_index(segments_by_doc: Dict[str, List[Dict[str, Any]]]) -> Tuple[int,int]:
    configure_gemini(); es=get_es()
    probe=genai.embed_content(model=EMBED_MODEL, content="probe")
    dims=len(probe.get("embedding", [])) or 3072
    ensure_index(es, ES_INDEX, dims)

    print("🚀 Bắt đầu embed + index …")
    success, fail = 0, 0
    batch=[]; BATCH_SIZE=200
    for act in iter_actions_for_bulk(segments_by_doc):
        batch.append(act)
        if len(batch)>=BATCH_SIZE:
            ok, err = helpers.bulk(es, batch, raise_on_error=False)
            success += ok; fail += len(err); batch.clear()
    if batch:
        ok, err = helpers.bulk(es, batch, raise_on_error=False)
        success += ok; fail += len(err)
    print(f"✅ Indexed: {success} | ❌ Errors: {fail}")
    return success, fail

# ===================== MAIN =====================
if __name__ == "__main__":
    print("=== HEALTH CHECK ==="); check_connections()
    print("\n=== READ & CLEAN PDFs ==="); pages_by_doc = read_and_clean_pdfs()
    print("\n=== SEGMENT (ANCHORS + REFINE) ==="); segments_by_doc = segment_docs_pages_with_anchors(pages_by_doc)
    print("\n=== EMBED + INDEX ==="); embed_and_index(segments_by_doc)
