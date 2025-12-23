---
type: table_description
name: PROGRAM
---
**Bảng: PROGRAM (Chương trình đào tạo)**
*   **Mô tả nghiệp vụ:** Bảng này định nghĩa các Chương trình đào tạo. Mỗi chương trình là một lộ trình học tập khung, quy định tổng số tín chỉ và số học kỳ cho một Ngành học cụ thể, áp dụng cho một Khóa tuyển sinh nhất định.
*   **Các cột:**
    *   `ID_PROGRAM` (VARCHAR(8)): Mã của chương trình đào tạo.
    *   `ADMISSION_YEAR` (INT): Khóa tuyển sinh mà chương trình đào tạo này áp dụng.
    *   `TOTAL_CREDIT` (INT): Tổng số tín chỉ mà sinh viên cần tích lũy để hoàn thành chương trình đào tạo này.
    *   `TOTAL_SEMESTER` (INT): Tổng số học kỳ được thiết kế cho chương trình đào tạo.
    *   `ID_MAJOR` (VARCHAR(10)): Mã Ngành học mà chương trình đào tạo này thuộc về (tham chiếu tới bảng `MAJOR`).
*   **Lưu ý quan trọng về khóa chính:**
    *   Khóa chính của bảng này là một cặp cột: `(ID_PROGRAM, ADMISSION_YEAR)`. Điều này có nghĩa là một chương trình đào tạo được xác định duy nhất bởi cả Mã chương trình và Khóa tuyển sinh. Ví dụ, chương trình cho ngành Công nghệ thông tin khóa 2021 có thể có lộ trình học khác với khóa 2022.
