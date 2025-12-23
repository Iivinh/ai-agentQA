---
type: table_description
name: CLASS
---
**Bảng: CLASS (Lớp sinh hoạt)**
*   **Mô tả nghiệp vụ:** Bảng này chứa danh sách các Lớp sinh hoạt. Lớp sinh hoạt là một tập hợp cá sinh viên cùng khóa, cùng ngành, học tập theo một lộ trình chung. Mỗi Lớp sinh hoạt phải thuộc về một Ngành học (MAJOR) cụ thể.
*   **Các cột:**
    *   `ID_CLASS` (VARCHAR(8)): Mã định danh duy nhất cho mỗi Lớp sinh hoạt. Đây là khóa chính. Ví dụ: '22050301'.
    *   `ID_MAJOR` (VARCHAR(10)): Mã của Ngành học mà Lớp này trực thuộc. Đây là khóa ngoại, liên kết tới bảng `MAJOR`.
