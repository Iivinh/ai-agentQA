---
type: table_description
name: SUBJECT_STRICT_PREREQUISITE
---
**Bảng: SUBJECT_STRICT_PREREQUISITE (Môn tiên quyết CỨNG)**
*   **Mô tả nghiệp vụ:** Bảng này định nghĩa quy tắc ràng buộc quan trọng nhất: **Môn tiên quyết CỨNG**. Quy tắc này có nghĩa là: để được phép đăng ký học môn `ID_SUBJECT`, sinh viên BẮT BUỘC phải học và có kết quả 'Đạt' (trong bảng `SUBJECT_RESULT`) đối với môn `ID_SUBJECT_STRICT_PREREQUISITE` từ một học kỳ trước đó. Quy tắc này áp dụng cho một chương trình đào tạo cụ thể.
*   **Các cột:**
    *   `ID_PROGRAM` (VARCHAR(8)): Mã của chương trình đào tạo mà quy tắc này áp dụng.
    *   `ADMISSION_YEAR` (INT): Khóa tuyển sinh mà quy tắc này áp dụng.
    *   `ID_SUBJECT` (VARCHAR(8)): Mã môn học chính (môn có điều kiện tiên quyết).
    *   `ID_SUBJECT_STRICT_PREREQUISITE` (VARCHAR(8)): Mã môn học tiên quyết (môn điều kiện phải học trước).
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ bốn cột: `(ID_PROGRAM, ADMISSION_YEAR, ID_SUBJECT, ID_SUBJECT_STRICT_PREREQUISITE)`.
    *   Cặp cột `(ID_PROGRAM, ADMISSION_YEAR)` là khóa ngoại, liên kết tới bảng `PROGRAM`.
    *   Cả hai cột `ID_SUBJECT` và `ID_SUBJECT_STRICT_PREREQUISITE` đều là khóa ngoại, cùng liên kết tới bảng `SUBJECT`.
    *   Đây là một trong ba loại quy tắc ràng buộc môn học. Các quy tắc khác được định nghĩa trong các bảng `SUBJECT_SOFT_PREREQUISITE` và `SUBJECT_PARALLEL`.
