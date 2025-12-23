---
type: table_description
name: SUBJECT
---
**Bảng: SUBJECT (Môn học)**
*   **Mô tả nghiệp vụ:** Bảng này chứa danh sách tất cả các môn học có trong tất cả chương trình giảng dạy của trường.
*   **Các cột:**
    *   `ID_SUBJECT` (VARCHAR(8)): Mã môn học, là định danh duy nhất cho mỗi môn học và là khóa chính.Ví dụ: '502061'.
    *   `NAME` (NVARCHAR(400)): Tên đầy đủ của môn học. Ví dụ: 'Nhập môn lập trình hướng đối tượng'.
    *   `TOTAL_CREDIT` (INT): Tổng số tín chỉ của môn học. Một tín chỉ thường tương đương với một số giờ học nhất định.
    *   `THEORY` (INT): Số tiết (hoặc tín chỉ) lý thuyết của môn học.
    *   `PRACTICE` (INT): Số tiết (hoặc tín chỉ) thực hành của môn học.
    *   `EXAM` (INT): Số tiết (hoặc tín chỉ) dành cho thi/kiểm tra cuối kỳ.
