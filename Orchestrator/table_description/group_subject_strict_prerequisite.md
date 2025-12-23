---
type: table_description
name: GROUP_SUBJECT_STRICT_PREREQUISITE
---
**Bảng: GROUP_SUBJECT_STRICT_PREREQUISITE (Áp dụng Nhóm môn làm Tiên quyết CỨNG)**
*   **Mô tả nghiệp vụ:** Bảng này áp dụng một **NHÓM** các môn học làm điều kiện tiên quyết cứng cho một môn học chính. Logic của quy tắc này là **AND**: sinh viên phải học và có kết quả 'Đạt' đối với **TẤT CẢ** các môn học nằm trong nhóm tiên quyết được chỉ định.
*   **QUAN TRỌNG - QUY TRÌNH TRA CỨU HOÀN CHỈNH:**
    1.  **Bước 1 (Bảng này):** Tìm môn học chính (`ID_SUBJECT`) để lấy ra mã nhóm tiên quyết tương ứng (`ID_GROUP`).
    2.  **Bước 2 (Bảng `PREREQUISITE_GROUP_SUBJECTS`):** Dùng `ID_GROUP` tìm được ở bước 1 để truy vấn vào bảng `PREREQUISITE_GROUP_SUBJECTS`. Thao tác này sẽ trả về danh sách mã của tất cả các môn học (`ID_SUBJECT`) thuộc nhóm tiên quyết đó.
    3.  **Bước 3 (Bảng `SUBJECT_RESULT`):** Kiểm tra xem sinh viên đã có kết quả 'Đạt' cho **TẤT CẢ** các môn học tìm được ở bước 2 hay chưa.
*   **Các cột:**
    *   `ID_PROGRAM` (VARCHAR(8)): Mã của chương trình đào tạo mà quy tắc này áp dụng.
    *   `ADMISSION_YEAR` (INT): Khóa tuyển sinh mà quy tắc này áp dụng.
    *   `ID_SUBJECT` (VARCHAR(8)): Mã môn học chính (môn có điều kiện tiên quyết là một nhóm).
    *   `ID_GROUP` (VARCHAR(8)): Mã của **NHÓM** môn học tiên quyết. Đây là khóa ngoại, liên kết tới bảng `PREREQUISITE_GROUP`.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ bốn cột: `(ID_PROGRAM, ADMISSION_YEAR, ID_SUBJECT, ID_GROUP)`.
    *   Cặp cột `(ID_PROGRAM, ADMISSION_YEAR)` là khóa ngoại, liên kết tới bảng `PROGRAM`.
    *   Cột `ID_SUBJECT` là khóa ngoại, liên kết tới bảng `SUBJECT`.
