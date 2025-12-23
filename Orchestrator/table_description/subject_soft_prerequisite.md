---
type: table_description
name: SUBJECT_SOFT_PREREQUISITE
---
**Bảng: SUBJECT_SOFT_PREREQUISITE (Môn học trước / Tiên quyết MỀM)**
*   **Mô tả nghiệp vụ:** Bảng này định nghĩa quy tắc ràng buộc **Môn học trước** (hay còn gọi là Tiên quyết MỀM). Khác với tiên quyết CỨNG, quy tắc này chỉ yêu cầu sinh viên **đã từng HỌC** môn `ID_SUBJECT_SOFT_PREREQUISITE` từ một học kỳ trước đó. Nó **không yêu cầu** sinh viên phải có kết quả 'Đạt' cho môn học điều kiện này.
*   **Các cột:**
    *   `ID_PROGRAM` (VARCHAR(8)): Mã của chương trình đào tạo mà quy tắc này áp dụng.
    *   `ADMISSION_YEAR` (INT): Khóa tuyển sinh mà quy tắc này áp dụng.
    *   `ID_SUBJECT` (VARCHAR(8)): Mã môn học chính (môn có điều kiện).
    *   `ID_SUBJECT_SOFT_PREREQUISITE` (VARCHAR(8)): Mã môn học điều kiện (môn phải học trước).
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ bốn cột: `(ID_PROGRAM, ADMISSION_YEAR, ID_SUBJECT, ID_SUBJECT_SOFT_PREREQUISITE)`.
    *   Cặp cột `(ID_PROGRAM, ADMISSION_YEAR)` là khóa ngoại, liên kết tới bảng `PROGRAM`.
    *   Cả hai cột `ID_SUBJECT` và `ID_SUBJECT_SOFT_PREREQUISITE` đều là khóa ngoại, cùng liên kết tới bảng `SUBJECT`.
    *   Đây là một trong ba loại quy tắc ràng buộc môn học. Các quy tắc khác được định nghĩa trong các bảng `SUBJECT_STRICT_PREREQUISITE` và `SUBJECT_PARALLEL`.
