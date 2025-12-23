import os
import re
import json
import google.generativeai as genai
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
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

def load_context_from_folders(folder_paths: List[str]) -> str:
    print("Bắt đầu nạp ngữ cảnh từ các thư mục...")
    full_context = []
    for folder_path in folder_paths:
        path = Path(folder_path)
        print(f"Nạp từ thư mục: {path}")
        if not path.is_dir():
            print(f"Cảnh báo: Thư mục '{folder_path}' không tồn tại.")
            continue
        
        md_files = sorted(list(path.glob("*.md")))
        print(f"Tìm thấy {len(md_files)} file .md trong '{folder_path}'")
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    full_context.append(f"--- START OF FILE {md_file.name} ---\n{f.read()}\n--- END OF FILE {md_file.name} ---\n")
            except Exception as e:
                print(f"Lỗi khi đọc file {md_file}: {e}")
    
    print("Nạp ngữ cảnh thành công!")
    return "\n".join(full_context)

def build_master_prompt(full_context: str, user_query: str, previous_keywords: Optional[List[str]] = None) -> str:
    rag_capability_summary = """
    <knowledge_base_summary>
    Hệ thống KNOWLEDGE_SEARCH (RAG) chứa các văn bản về các chủ đề chung sau:
    - QUY CHẾ HỌC VỤ: quy định về tín chỉ, điểm số, thi cử, cảnh báo học vụ, điều kiện tốt nghiệp.
    - HỌC BỔNG: danh sách học bổng, tiêu chí, yêu cầu hồ sơ, thời gian nộp.
    - HỌC PHÍ: chính sách học phí, các khoản thu, hướng dẫn thanh toán.
    - THỦ TỤC HÀNH CHÍNH: quy trình làm lại thẻ sinh viên, xin bảng điểm, giấy xác nhận.
    </knowledge_base_summary>
    """
    
    output_format_definition = """
    --- OUTPUT FORMAT DEFINITION ---
    Bạn PHẢI trả lời bằng một khối mã JSON duy nhất, không có bất kỳ văn bản nào khác trước hoặc sau nó.
    JSON phải tuân thủ nghiêm ngặt cấu trúc sau:
    
    ```json
    {
        "query_type": "SQL_ONLY | RAG_ONLY | HYBRID",
        "explanation": "Một chuỗi văn bản giải thích ngắn gọn và súc tích tại sao bạn lại chọn 'query_type' này, dựa trên phân tích câu hỏi của người dùng.",
        "sql_query": "Câu lệnh SQL hoàn chỉnh và sẵn sàng để thực thi. Nếu 'query_type' là 'RAG_ONLY', giá trị của trường này PHẢI là null.",
        "keywords_for_rag": [
            "Một mảng các chuỗi, mỗi chuỗi là một từ khóa hoặc khái niệm chính được rút trích từ câu hỏi người dùng để tối ưu cho việc tìm kiếm.",
            "Ưu tiên rút trích các danh từ, cụm danh từ và thuật ngữ chuyên ngành.",
            "Nếu 'query_type' là 'SQL_ONLY', giá trị của trường này PHẢI là null."
        ]
    }
    ```
    """
    
    # 🟩 Thêm hướng dẫn mới nếu có từ khóa cũ
    keyword_retry_hint = ""
    if previous_keywords:
        keyword_retry_hint = f"""
    ⚠️ Ghi chú bổ sung:
    Trước đây, hệ thống đã sử dụng các từ khóa sau cho truy vấn RAG nhưng kết quả không tốt:
    {', '.join(previous_keywords)}.
    Hãy phân tích nguyên nhân tại sao những từ khóa này chưa hiệu quả, và **sinh thêm hoặc đề xuất lại các từ khóa mới phù hợp hơn**
    để tăng khả năng tìm thấy nội dung liên quan trong hệ thống KNOWLEDGE_SEARCH.
    """
    
    prompt = f"""
    Bạn là một AI Agent điều phối thông minh của một trường đại học. Nhiệm vụ của bạn là phân tích câu hỏi của sinh viên và tạo ra một kế hoạch hành động dưới dạng JSON để các hệ thống khác thực thi. TUYỆT ĐỐI không được trả lời trực tiếp câu hỏi.

    Bạn có quyền truy cập vào hai công cụ:
    1. SQL_DATABASE: Một CSDL chứa thông tin cá nhân và có cấu trúc của sinh viên.
    2. KNOWLEDGE_SEARCH (RAG): Một hệ thống tra cứu văn bản chứa các quy định, chính sách chung của nhà trường.

    --- DATABASE & CONCEPT CONTEXT START ---
    {full_context}
    --- DATABASE & CONCEPT CONTEXT END ---
    
    {rag_capability_summary}

    Dựa vào câu hỏi của người dùng và toàn bộ ngữ cảnh được cung cấp, hãy thực hiện logic sau:
    1. **PHÂN TÍCH YÊU CẦU:** Đọc kỹ câu hỏi để xác định các thực thể và ý định chính. Đối chiếu chúng với ngữ cảnh CSDL và tóm tắt khả năng của KNOWLEDGE_SEARCH.
    
    2. **QUYẾT ĐỊNH LOẠI TRUY VẤN ('query_type'):**
        - Nếu câu hỏi CHỈ yêu cầu thông tin cá nhân, có cấu trúc từ CSDL (ví dụ: 'điểm của tôi', 'lịch học của tôi'), hãy đặt là "SQL_ONLY".
        - Nếu câu hỏi CHỈ yêu cầu thông tin chung, quy định, chính sách (ví dụ: 'quy định về học bổng', 'thủ tục làm lại thẻ'), hãy đặt là "RAG_ONLY".
        - Nếu câu hỏi yêu cầu KẾT HỢP cả hai loại thông tin trên, hãy đặt là "HYBRID".

    3. **TẠO TẢI TRỌNG (Payload):**
        - Đối với 'sql_query': Hãy sinh một câu lệnh SQL hoàn chỉnh, tuân thủ cú pháp T-SQL của Microsoft SQL Server,  BẮT BUỘC phải sử dụng tiền tố N cho tất cả các chuỗi ký tự có dấu (Unicode).,chính xác về mặt nghiệp vụ dựa trên ngữ cảnh CSDL được cung cấp (bao gồm cả schema, table descriptions và concepts).
        - Đối với 'keywords_for_rag': Hãy rút trích một danh sách các từ khóa và khái niệm cốt lõi nhất từ câu hỏi.
        
    {keyword_retry_hint}
    
    4. **ĐỊNH DẠNG ĐẦU RA:** Trả về kết quả dưới dạng một file JSON duy nhất tuân thủ nghiêm ngặt định nghĩa dưới đây.
    
    {output_format_definition}

    --- USER QUERY START ---
    {user_query}
    --- USER QUERY END ---
    """
    return prompt

def get_execution_plan(user_query: str, full_context: str) -> Optional[Dict]:
    """
    Gửi prompt đến Gemini và nhận về bản kế hoạch hành động dưới dạng JSON.
    """
    print("\nĐang xây dựng Master Prompt...")
    master_prompt = build_master_prompt(full_context, user_query)
    generation_config = genai.GenerationConfig(
        temperature=0.1,
        candidate_count=1,
    )
    print("Đang gửi yêu cầu đến Gemini...")
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(
            master_prompt,
            generation_config=generation_config
        )
        # Xử lý output, loại bỏ các ký tự không cần thiết mà model có thể thêm vào
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        print("Nhận phản hồi từ Gemini. Đang phân tích JSON...")
        # Phân tích chuỗi JSON thành dictionary của Python
        return json.loads(response_text)
    except json.JSONDecodeError:
        print("\n--- LỖI PHÂN TÍCH JSON ---")
        print("Không thể phân tích phản hồi từ Gemini thành JSON. Phản hồi thô:")
        print(response.text)
        return None
    except Exception as e:
        print(f"\n--- ĐÃ XẢY RA LỖI ---")
        print(f"Lỗi khi gọi API Gemini: {e}")
        return None    


# ====== Prompt sửa SQL======
def build_sql_fix_prompt_raw(DATABASE_SCHEMA: str, QUESTION: str, HINT: str, QUERY: str, RESULT: str, EXAMPLES: str = "") -> str:
    return f"""**Mô tả nhiệm vụ:**
Bạn là một chuyên gia cơ sở dữ liệu SQL, được giao nhiệm vụ sửa một câu truy vấn SQL. Lần chạy trước đó
không cho kết quả chính xác — có thể do lỗi khi thực thi, hoặc vì kết quả trả về rỗng hoặc không đúng như mong đợi.
Vai trò của bạn là phân tích lỗi dựa trên **cấu trúc cơ sở dữ liệu (schema)** được cung cấp và chi tiết về lần thực thi thất bại,
sau đó đưa ra **phiên bản truy vấn SQL đã được chỉnh sửa đúng**.

**Quy trình thực hiện:**
1. Xem xét cấu trúc cơ sở dữ liệu:
   - Đọc kỹ các lệnh tạo bảng để hiểu rõ cấu trúc và mối quan hệ giữa các bảng.

2. Phân tích yêu cầu của truy vấn:
   - Câu hỏi gốc: Xác định dữ liệu mà truy vấn cần lấy.
   - Gợi ý (Hint): Sử dụng các gợi ý được cung cấp để hiểu rõ hơn về quan hệ giữa các bảng và điều kiện truy vấn.
   - Câu truy vấn SQL đã chạy: Kiểm tra câu truy vấn SQL đã được thực thi và gây ra lỗi hoặc kết quả không chính xác.
   - Kết quả thực thi: Phân tích thông tin trả về của truy vấn (ví dụ: lỗi cú pháp, sai tên cột, sai điều kiện JOIN hoặc WHERE).

3. Sửa truy vấn:
   - Chỉnh sửa câu truy vấn SQL để khắc phục các lỗi đã xác định, đảm bảo rằng truy vấn trả về dữ liệu chính xác
     theo **schema cơ sở dữ liệu** và **yêu cầu của câu hỏi**.

**Định dạng đầu ra:**
- Hãy trình bày truy vấn SQL đã được sửa **trên một dòng duy nhất**, ngay sau cụm từ **Final Answer:**.
- Không được xuống dòng trong truy vấn.
- Phải sử dụng **cú pháp của Microsoft SQL Server (T-SQL)**.
- Chỉ được sinh ra **truy vấn đọc dữ liệu (SELECT/CTE)**, tuyệt đối **không sinh lệnh DML hoặc DDL** như INSERT, UPDATE, DELETE, DROP, EXEC,…

Dưới đây là một số ví dụ:
{EXAMPLES}

======= Nhiệm vụ của bạn =======
**************************
Các câu lệnh tạo bảng:
{DATABASE_SCHEMA}
**************************
Câu hỏi gốc:
Question:
{QUESTION}
Gợi ý (Hint):
{HINT}
Câu truy vấn SQL đã thực thi:
{QUERY}
Kết quả thực thi:
{RESULT}
**************************
Dựa trên câu hỏi, cấu trúc bảng và truy vấn trước đó, hãy phân tích nguyên nhân và đưa ra câu truy vấn SQL đã được sửa đúng.
"""


def fix_sql_error_with_gemini(
    question: str,
    sql_query: str,
    sql_error: str,
    hint: str = "",
    examples: str = "",
) -> str:
    """
    Gọi Gemini để sửa câu truy vấn SQL bị lỗi.
    Truyền vào:
        - DATABASE_SCHEMA: chuỗi chứa CREATE TABLE... (schema của DB)
        - question: câu hỏi gốc của người dùng
        - sql_query: câu SQL bị lỗi
        - sql_error: thông báo lỗi trả về từ SQL Server
        - hint/examples: tùy chọn (có thể bỏ trống)
    Trả về:
        - Câu SQL đã sửa (1 dòng)
    """
    base_dir = os.path.dirname(__file__)
    context_folders = [
        os.path.join(base_dir, "schema_relationship")
    ]

    # Ở đây, bạn có thể thêm cả schema, relationships vào một file .md và nạp chung
    
    database_context = load_context_from_folders(context_folders)
    
    # --- 2. Xây dựng prompt ---
    prompt = build_sql_fix_prompt_raw(
        DATABASE_SCHEMA=database_context,
        QUESTION=question,
        HINT=hint,
        QUERY=sql_query,
        RESULT=sql_error,
        EXAMPLES=examples,
    )
    
    
    # --- 3. Gọi Gemini ---
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.1}
    )
    text = (response.text or "").strip()

    # --- 4. Trích câu lệnh SQL sau "Final Answer:" ---
    match = re.search(r"Final Answer\s*:?\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)
    fixed_sql = match.group(1).strip() if match else text

    # --- 5. Ép về 1 dòng & loại code fence ```
    fixed_sql = re.sub(r"^```(?:sql)?", "", fixed_sql, flags=re.IGNORECASE).strip()
    fixed_sql = re.sub(r"```$", "", fixed_sql).strip()
    fixed_sql = " ".join(fixed_sql.split())

    # --- 6. Kiểm tra an toàn: chỉ SELECT/CTE ---
    if not re.match(r"^\s*(WITH|SELECT)\b", fixed_sql, flags=re.IGNORECASE):
        raise ValueError(f"⚠️ Model trả về lệnh không hợp lệ (chỉ SELECT/CTE):\n{fixed_sql}")

    print("\n✅ Câu SQL đã sửa thành công:")
    print(fixed_sql)
    return fixed_sql


    
def orchestrator(user_query: str) -> Optional[Dict]:
    # 1. Cấu hình
    configure_gemini()

    # 2. Nạp toàn bộ ngữ cảnh
    base_dir = os.path.dirname(__file__)
    context_folders = [
        os.path.join(base_dir, "table_description"),
        os.path.join(base_dir, "concept"),
        os.path.join(base_dir, "schema_relationship")
    ]

    # Ở đây, bạn có thể thêm cả schema, relationships vào một file .md và nạp chung
    
    database_context = load_context_from_folders(context_folders)
    
    # 3. Đặt câu hỏi của người dùng

    # user_query = "Ngành Khoa học máy tính gồm bao nhiêu nhóm tự chọn, gồm những nhóm nào"
    # user_query = "Ngành Kỹ thuật phần mềm thuộc khoa nào?"
    # user_query = "Tiêu chí để nhận học bổng khuyến khích học tập là gì?"
    
    print(f"\n--- BẮT ĐẦU XỬ LÝ CÂU HỎI ---\nCâu hỏi: '{user_query}'")

    # 5. Lấy bản kế hoạch
    plan = get_execution_plan(user_query, database_context)
    # Sau khi đã có: plan = get_execution_plan(...)
    # 6. In kết quả
    if plan:
        print("\n--- BẢN KẾ HOẠCH HÀNH ĐỘNG (JSON) ---")
        # In JSON một cách đẹp mắt
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print("\n--- KHÔNG THỂ TẠO BẢN KẾ HOẠCH ---")
    return plan



