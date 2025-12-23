---
type: table_description
name: MAJOR
---
**Bảng: MAJOR (Ngành học)**
*   **Mô tả nghiệp vụ:** Bảng này lưu trữ danh sách các Ngành học được đào tạo trong trường. Mỗi Ngành học phải thuộc về một Khoa (FACULTY) duy nhất.
*   **Các cột:**
    *   `ID_MAJOR` (VARCHAR(10)): Mã định danh duy nhất cho mỗi Ngành học. Đây là khóa chính. Ví dụ: '7480103'.
    *   `NAME` (NVARCHAR(100)): Tên đầy đủ của Ngành học. Ví dụ: 'Kỹ thuật phần mềm'.
    *   `ID_FACULTY` (VARCHAR(1)): Mã của Khoa mà Ngành học này trực thuộc. Đây là khóa ngoại, liên kết tới bảng `FACULTY`.
