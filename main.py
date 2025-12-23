"""
Main orchestrator: nhận câu hỏi người dùng → gọi bộ lập kế hoạch (file #1)
→ thực thi theo kế hoạch: SQL_ONLY | RAG_ONLY | HYBRID.

Yêu cầu môi trường:
- Python packages: google-generativeai, elasticsearch, pyodbc (hoặc pymssql), python-dotenv
- ENV cho Gemini: GEMINI_API_KEY
- ENV cho SQL Server (nếu chạy SQL):
  SQLSERVER_HOST, SQLSERVER_PORT (mặc định 1433), SQLSERVER_DB,
  SQLSERVER_USER, SQLSERVER_PASSWORD, SQLSERVER_DRIVER (ví dụ: "ODBC Driver 17 for SQL Server")

Giả định:
- File #1 (planner) có các hàm: configure_gemini(), load_context_from_folders(list[str]) -> str,
  get_execution_plan(user_query: str, full_context: str) -> dict | None
- File #2 (retrieval) có hàm: run_qa_pipeline(query_text: str, keywords: str | None = None, filters: dict | None = None,
  initial_top_k: int = 5, max_top_k_cap: int = 50, max_iters: int = 4)

Cập nhật import cho đúng tên file của bạn.
"""
from __future__ import annotations
import os
import re
import json
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# ==== CẬP NHẬT LẠI CHO ĐÚNG TÊN MODULE CỦA BẠN ====
# Ví dụ, nếu file #1 tên "planner.py" và file #2 tên "retrieval.py":
# from planner import configure_gemini, load_context_from_folders, get_execution_plan
# from retrieval import run_qa_pipeline
#
# Nếu tên khác, sửa lại 2 dòng import dưới cho khớp:
from Orchestrator.task import orchestrator, fix_sql_error_with_gemini  # type: ignore
from scripts.rag_pipeline import run_qa_pipeline  # type: ignore  # nếu bạn đã để run_qa_pipeline trong file test.py


# ---------- STUB SQL EXECUTOR (bạn sẽ bổ sung sau) ----------
from typing import List, Tuple, Any
import pyodbc
import google.generativeai as genai
def configure_gemini():
    """Cấu hình API key cho Gemini từ biến môi trường."""
    load_dotenv()
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Biến môi trường GEMINI_API_KEY chưa được thiết lập.")
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"Lỗi khi cấu hình Gemini: {e}")
        exit()
        
def _split_batches(sql: str) -> List[str]:
    parts, buf = [], []
    for line in sql.splitlines():
        if re.match(r'^\s*GO\s*$', line, flags=re.IGNORECASE):
            if buf:
                parts.append("\n".join(buf).strip())
                buf = []
        else:
            buf.append(line)
    if buf:
        parts.append("\n".join(buf).strip())
    return [p for p in parts if p]

def execute_sql_query(sql: str) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """
    Thực thi T-SQL bằng Windows Authentication tới CNTT @ SQLEXPRESS.
    - Hỗ trợ script nhiều batch có 'GO'
    - Trả về (columns, rows) của result set CUỐI CÙNG
    - Nếu lỗi: raise Exception với thông báo lỗi chi tiết
    """
    conn = None
    try:
        conn = pyodbc.connect(
            r"DRIVER={ODBC Driver 18 for SQL Server};"
            r"SERVER=localhost\SQLEXPRESS;"
            r"DATABASE=CNTT;"
            r"Trusted_Connection=yes;"
            r"Encrypt=yes;TrustServerCertificate=yes;",
            autocommit=True,
            timeout=15,
        )
        cur = conn.cursor()

        batches = _split_batches(sql) or [sql]
        last_cols: List[str] = []
        last_rows: List[Tuple[Any, ...]] = []

        for b in batches:
            try:
                cur.execute(b)
            except pyodbc.Error as e:
                # Trả lỗi cụ thể cho từng batch
                raise Exception(f"Lỗi SQL ở batch:\n{b}\nChi tiết: {e}")

            # Xử lý result set chính
            if cur.description is not None:
                cols = [c[0] for c in cur.description]
                data = cur.fetchall()
                last_cols, last_rows = cols, [tuple(r) for r in data]
            else:
                last_cols, last_rows = ["rows_affected"], [(cur.rowcount,)]

            # Xử lý các result set tiếp theo (nếu có)
            while cur.nextset():
                if cur.description is not None:
                    cols = [c[0] for c in cur.description]
                    data = cur.fetchall()
                    last_cols, last_rows = cols, [tuple(r) for r in data]
                else:
                    last_cols, last_rows = ["rows_affected"], [(cur.rowcount,)]

        return last_cols, last_rows

    except pyodbc.Error as e:
        # Trả lỗi ra ngoài để Gemini xử lý
        raise Exception(f"Lỗi khi thực thi SQL:\n{e}")

    finally:
        try:
            if conn:
                conn.close()
        except:
            pass

        
def _print_sql_result(cols: List[str], rows: List[Tuple[Any, ...]], limit: int = 50) -> None:
    if not cols:
        print("⛔ Không có cột/kết quả.")
        return
    print("\n--- KẾT QUẢ SQL ---")
    print(", ".join(cols))
    for i, r in enumerate(rows[:limit], 1):
        print(f"{i:>3}: " + ", ".join([str(v) for v in r]))
    if len(rows) > limit:
        print(f"... ({len(rows) - limit} dòng nữa)")

# ---------- Helper ----------


def print_plan(plan: Dict[str, Any]) -> None:
    print("\n--- KẾ HOẠCH ---")
    print(json.dumps(plan, indent=2, ensure_ascii=False))


# ---- Chuẩn hóa rows SQL -> JSON cho LLM dễ hiểu ----
def _rows_to_json(columns: list[str], rows: list[tuple]) -> list[dict]:
    if not columns or not rows:
        return []
    out = []
    for r in rows:
        out.append({columns[i]: (r[i] if i < len(r) else None) for i in range(len(columns))})
    return out

# ---- Gọi Gemini để tổng hợp câu trả lời cuối ----
FINAL_MODEL = os.getenv("MODEL_FINAL", "models/gemini-2.5-pro")

def _finalize_answer_llm(user_query: str,
                         sql_columns: list[str] | None,
                         sql_rows: list[tuple] | None,
                         rag_text: str | None) -> str:
    sql_json = _rows_to_json(sql_columns or [], sql_rows or [])
    prompt = (
        "Bạn là trợ lý học vụ. Hãy tổng hợp câu trả lời NGẮN GỌN, RÕ RÀNG từ hai nguồn sau.\n"
        "- SQL_DATA: dữ liệu bảng (nếu có) - trích ra các điểm/chỉ số quan trọng.\n"
        "- RAG_SNIPPET: trích lược quy định/chính sách - dùng làm căn cứ giải thích.\n"
        "- Nếu thiếu dữ liệu để kết luận, nói rõ phần nào còn thiếu.\n\n"
        f"USER_QUERY:\n{user_query}\n\n"
        f"SQL_DATA_JSON:\n{json.dumps(sql_json, ensure_ascii=False)}\n\n"
        f"RAG_SNIPPET:\n{rag_text or ''}\n\n"
        "YÊU CẦU ĐẦU RA: Trả lời tiếng Việt, tối đa ~8 gạch đầu dòng hoặc 1 đoạn ngắn; "
        "nếu cần liệt kê nguồn, thêm dòng cuối 'Nguồn: ...'."
    )
    try:
        import google.generativeai as genai
        # configure_gemini() đã được gọi ở trên, nên genai đã có API key
        model = genai.GenerativeModel(FINAL_MODEL)
        resp = model.generate_content(prompt, generation_config={"temperature": 0.2})
        return (resp.text or "").strip()
    except Exception as e:
        return f"[Finalizer error] {e}"
    
def _finalize_answer_with_gemini(
    user_query: str,
    sql_columns: Optional[List[str]] = None,
    sql_rows: Optional[List[Tuple[Any, ...]]] = None,
    rag_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tổng hợp kết quả từ SQL và RAG để đánh giá mức độ đủ thông tin.
    - Nếu chỉ có SQL → sinh câu trả lời dựa trên dữ liệu SQL.
    - Nếu chỉ có RAG → kiểm tra đủ thông tin, nếu thiếu → INSUFFICIENT_INFO.
    - Nếu có cả hai → sinh câu trả lời kết hợp giữa SQL và RAG.
    Trả về:
        {
            "status": "ANSWER" | "INSUFFICIENT_INFO" | "ERROR",
            "answer": str,
            "reason": str,
        }
    """
    try:
        # 1️⃣ Chuyển SQL kết quả thành JSON dễ đọc
        sql_json = []
        if sql_columns and sql_rows:
            sql_json = [
                {sql_columns[i]: (r[i] if i < len(r) else None) for i in range(len(sql_columns))}
                for r in sql_rows
            ]

        # 2️⃣ Kiểm tra nếu cả 2 đều rỗng
        if not sql_json and not rag_text:
            return {
                "status": "INSUFFICIENT_INFO",
                "reason": "Không có dữ liệu từ SQL hoặc RAG để đánh giá.",
                "answer": "",
            }

        # 3️⃣ Xây dựng context đầu vào
        context_blocks = []
        if sql_json:
            context_blocks.append(f"📘 SQL_RESULT_JSON:\n{json.dumps(sql_json, ensure_ascii=False, indent=2)}")
        if rag_text:
            context_blocks.append(f"📗 RAG_SNIPPET:\n{rag_text.strip()}")

        full_context = "\n\n".join(context_blocks)

        # 4️⃣ Prompt cho Gemini
        prompt = f"""
Bạn là trợ lý học vụ tại trường đại học. Dưới đây là câu hỏi và dữ liệu được truy xuất từ hai nguồn:

CÂU HỎI:
{user_query}

--- DỮ LIỆU TRUY XUẤT ---
{full_context}
---------------------------

Nhiệm vụ:
1. Phân tích xem dữ liệu hiện có (SQL, RAG hoặc cả hai) có đủ để trả lời câu hỏi của sinh viên hay không.
2. Nếu chỉ có SQL → hãy viết chuyển đổi dữ liệu dạng bảng thành đoạn văn.
3. Nếu chỉ có RAG → hãy kiểm tra xem RAG đã đủ chưa. Nếu chưa đủ → trả về trạng thái "INSUFFICIENT_INFO".
4. Nếu có cả SQL và RAG → sinh câu trả lời kết hợp, sử dụng thông tin từ RAG và đối chiếu / bổ sung bằng dữ liệu SQL nếu cần.

YÊU CẦU ĐẦU RA (JSON CHUẨN):
```json
{{
  "status": "ANSWER" | "INSUFFICIENT_INFO",
  "answer": "Câu trả lời ngắn gọn nếu đủ dữ liệu, nếu chưa đủ thì để trống",
  "reason": "Giải thích vì sao đủ hoặc chưa đủ"
}}
"""
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt, generation_config={"temperature": 0.2})
        text = (response.text or "").strip()

        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        parsed = json.loads(text)

        status = parsed.get("status", "").upper()
        if status not in ["ANSWER", "INSUFFICIENT_INFO"]:
            return {"status": "ERROR", "reason": f"Trạng thái không hợp lệ: {status}", "answer": ""}

        parsed["answer"] = (parsed.get("answer") or "").strip()
        parsed["reason"] = (parsed.get("reason") or "").strip()
        return parsed

    except Exception as e:
        return {"status": "ERROR", "reason": f"Lỗi trong quá trình tổng hợp: {e}", "answer": ""}


# ---------- Orchestrator ----------
def run_orchestrator(
    user_query: str,
) -> None:
    """
    1) Nạp ngữ cảnh (cho planner)
    2) Gọi get_execution_plan(user_query, full_context)
    3) Thực thi theo query_type: SQL_ONLY | RAG_ONLY | HYBRID
       - SQL: gọi execute_sql_query(sql) [stub]
       - RAG: gọi run_qa_pipeline(query_text, keywords, filters)
    """
    load_dotenv()


    plan = orchestrator(user_query)

    sql_query: Optional[str] = plan.get("sql_query")
    kws: Optional[List[str]] = plan.get("keywords_for_rag")
    max_attempt = 3  # số lần gọi lại tối đa nếu không đủ dữ liệu
    attempt = 1
    sql_cols, sql_rows = [], []
    # 3) Thực thi theo kế hoạch
    while attempt <= max_attempt:
        if sql_query:
            current_sql = sql_query
            check_error_sql = True

            while check_error_sql:
                try:
                    # Thực thi truy vấn
                    sql_cols, sql_rows = execute_sql_query(current_sql)
                    _print_sql_result(sql_cols, sql_rows)
                    break  # dừng nếu thành công

                except Exception as e:
                    # ❌ Nếu lỗi, lấy thông báo lỗi chi tiết
                    sql_error = str(e)
                    # 🔧 Gọi Gemini để sửa truy vấn
                    try:
                        print("\n🔧 Gọi Gemini để sửa truy vấn...")
                        fixed_sql = fix_sql_error_with_gemini(
                            question=user_query,
                            sql_query=current_sql,
                            sql_error=sql_error,
                        )
                        print(f"\nGemini đề xuất truy vấn mới:\n{fixed_sql}")
                        current_sql = fixed_sql  # cập nhật câu mới để thử lại
                    except Exception as e2:
                        print(f"Lỗi khi gọi Gemini sửa SQL: {e2}")
                        break
            else:
                print("Hết số lần thử, không thể sửa truy vấn.")
            
        if kws: #kws != null
            print("\n🔍 Chạy RAG với từ khóa:", kws)
            result = run_qa_pipeline(
                query_text=user_query,
                keywords=kws,
                filters=None,
                initial_top_k=5,
                max_top_k_cap=50,
                max_iters=4,
            )
            
        #Todo: Finalize answer
        final_eval = _finalize_answer_with_gemini(
            user_query=user_query,
            sql_columns=sql_cols,
            sql_rows=sql_rows,
            rag_text=result.get("answer", "") if kws else None,
        )

        status = final_eval.get("status")
        if status == "ANSWER":
            print("\n✅ CÂU TRẢ LỜI CUỐI CÙNG ===")
            print(final_eval["answer"])
            return
        elif status == "INSUFFICIENT_INFO":
            print(f"\nDữ liệu chưa đủ: {final_eval['reason']}")
            # Gọi orchestrator(user_query) hoặc sinh keyword mới
            attempt += 1
        else:
            print(f"\nLỗi khi tổng hợp: {final_eval.get('reason')}")
            return
    
    

# ---------- Entry ----------
if __name__ == "__main__":
    try:
        # q = input("Nhập câu hỏi của bạn: ").strip()
        # q = "điều kiện xét tuyển thẳng"
        q = "Cho em hỏi điều kiện để học môn Cấu trúc dữ liệu và giải thuật là gì?"
    except EOFError:
        q = ""
    if not q:
        q = "Cho em hỏi điều kiện để học môn Cấu trúc dữ liệu và giải thuật là gì?"
        print(f"(Dùng mặc định) {q}")

    # Ví dụ filter cho RAG (để None nếu muốn tìm toàn bộ)
    rag_filters_example = None
    # rag_filters_example = {"term": {"doc_id": "Quy_che_tuyen_sinh"}}

    run_orchestrator(
        user_query=q
    )