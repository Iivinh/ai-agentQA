---
type: table_description
name: SUBJECT_PARALLEL
---
**Bảng: SUBJECT_PARALLEL (Môn song hành)**
*   **Mô tả nghiệp vụ:** Bảng này định nghĩa quy tắc ràng buộc **Môn song hành**. Quy tắc này yêu cầu sinh viên phải đăng ký học môn `ID_SUBJECT_PARALLEL` **trong cùng một học kỳ** với môn `ID_SUBJECT`. Nó không yêu cầu phải học trước, mà là học đồng thời.
*   **Các cột:**
    *   `ID_PROGRAM` (VARCHAR(8)): Mã của chương trình đào tạo mà quy tắc này áp dụng.
    *   `ADMISSION_YEAR` (INT): Khóa tuyển sinh mà quy tắc này áp dụng.
    *   `ID_SUBJECT` (VARCHAR(8)): Mã môn học chính.
    *   `ID_SUBJECT_PARALLEL` (VARCHAR(8)): Mã môn học cần đăng ký song hành.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ bốn cột: `(ID_PROGRAM, ADMISSION_YEAR, ID_SUBJECT, ID_SUBJECT_PARALLEL)`.
    *   Cặp cột `(ID_PROGRAM, ADMISSION_YEAR)` là khóa ngoại, liên kết tới bảng `PROGRAM`.
    *   Cả hai cột `ID_SUBJECT` và `ID_SUBJECT_PARALLEL` đều là khóa ngoại, cùng liên kết tới bảng `SUBJECT`.
    *   Đây là một trong ba loại quy tắc ràng buộc môn học. Các quy tắc khác được định nghĩa trong các bảng `SUBJECT_STRICT_PREREQUISITE` và `SUBJECT_SOFT_PREREQUISITE`.
