---
type: table_description
name: PROGRAM_SUBJECT
---
**Bảng: PROGRAM_SUBJECT (Môn học trong Chương trình đào tạo)**
*   **Mô tả nghiệp vụ:** Bảng này đóng vai trò là **Lộ trình học tập khung** (curriculum). Nó quy định rằng một Chương trình đào tạo cụ thể (xác định bởi `ID_PROGRAM` và `ADMISSION_YEAR`) sẽ bao gồm những Môn học nào (`ID_SUBJECT`), và gợi ý Môn học đó nên được học vào Học kỳ (`SEMESTER`) thứ mấy.
*   **Các cột:**
    *   `ID_SUBJECT` (VARCHAR(8)): Mã của môn học thuộc chương trình đào tạo.
    *   `ID_PROGRAM` (VARCHAR(8)): Mã của chương trình đào tạo.
    *   `ADMISSION_YEAR` (INT): Khóa tuyển sinh áp dụng cho chương trình đào tạo.
    *   `SEMESTER` (INT): Số thứ tự của học kỳ mà môn học này được xếp vào theo lộ trình gợi ý. **Ví dụ: giá trị `1` có nghĩa là môn học thuộc Học kỳ 1, `2` là Học kỳ 2, v.v.**
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Đây là một bảng quan hệ, tạo ra mối liên kết nhiều-nhiều giữa `PROGRAM` và `SUBJECT`.
    *   Khóa chính của bảng này là một bộ ba cột: `(ID_SUBJECT, ID_PROGRAM, ADMISSION_YEAR)`.
    *   Cặp cột `(ID_PROGRAM, ADMISSION_YEAR)` là khóa ngoại, liên kết tới bảng `PROGRAM`.
    *   Cột `ID_SUBJECT` là khóa ngoại, liên kết tới bảng `SUBJECT`.
