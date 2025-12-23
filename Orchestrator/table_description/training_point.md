---
type: table_description
name: TRAINING_POINT
---
**Bảng: TRAINING_POINT (Điểm rèn luyện)**
*   **Mô tả nghiệp vụ:** Bảng này lưu trữ điểm rèn luyện **tổng kết** của mỗi sinh viên theo từng học kỳ của mỗi năm học. Điểm số này thường được tổng hợp từ các hoạt động, sự kiện mà sinh viên tham gia, được ghi nhận chi tiết trong bảng `EVENT_TRAINING_POINT`.
*   **Các cột:**
    *   `ID_STUDENT` (VARCHAR(8)): Mã của sinh viên được ghi nhận điểm rèn luyện.
    *   `SEMESTER` (INT): Học kỳ mà điểm rèn luyện được ghi nhận. Ví dụ: `1`, `2`.
    *   `YEAR` (VARCHAR(20)): Năm học mà điểm rèn luyện được ghi nhận. Ví dụ: '2023-2024'.
    *   `SCORE` (INT): Điểm rèn luyện tổng kết của sinh viên trong học kỳ đó. Có thể có giá trị NULL nếu điểm chưa được xét hoặc chưa có.
*   **Lưu ý quan trọng về khóa:**
    *   Khóa chính của bảng này là một bộ ba cột: `(ID_STUDENT, SEMESTER, YEAR)`.
    *   Điều này đảm bảo mỗi sinh viên chỉ có một dòng điểm rèn luyện duy nhất cho mỗi học kỳ của một năm học.
    *   Cột `ID_STUDENT` là khóa ngoại, liên kết tới bảng `STUDENT`.
