---
type: table_description
name: STUDENT
---
**Bảng: STUDENT (Sinh viên)**
*   **Mô tả nghiệp vụ:** Đây là bảng trung tâm và quan trọng nhất, lưu trữ tất cả thông tin cá nhân của mỗi sinh viên. Bảng này hoạt động như một đầu mối, liên kết đến Khoa, Ngành, Lớp và Chương trình đào tạo của sinh viên.
*   **Các cột:**
    *   `ID_STUDENT` (VARCHAR(8)): Mã số sinh viên, là định danh duy nhất cho mỗi sinh viên và là khóa chính.
    *   `NAME` (NVARCHAR(100)): Họ và tên đầy đủ của sinh viên.
    *   `SEX` (BIT): Giới tính của sinh viên. **QUAN TRỌNG: Quy ước 0 là Nam, 1 là Nữ.**
    *   `DATE_OF_BIRTH` (DATE): Ngày sinh của sinh viên.
    *   `GMAIL` (VARCHAR(100)): Địa chỉ email liên lạc của sinh viên.
    *   `ID_FACULTY` (VARCHAR(1)): Mã Khoa mà sinh viên đang theo học (liên kết đến bảng `FACULTY`).
    *   `ID_MAJOR` (VARCHAR(10)): Mã Ngành học mà sinh viên đang theo học (liên kết đến bảng `MAJOR`).
    *   `ID_CLASS` (VARCHAR(8)): Mã Lớp sinh hoạt mà sinh viên là thành viên (liên kết đến bảng `CLASS`).
    *   `ID_PROGRAM` (VARCHAR(8)): Mã chương trình đào tạo mà sinh viên theo học.
    *   `ADMISSION_YEAR` (INT): Khóa tuyển sinh của sinh viên, là một giá trị số. Ví dụ: 2021, 2022. 
*   **Lưu ý quan trọng về mối quan hệ:**
    *   Cặp cột `(ID_PROGRAM, ADMISSION_YEAR)` cùng nhau tạo thành một khóa ngoại để liên kết tới một chương trình đào tạo cụ thể trong bảng `PROGRAM`.
