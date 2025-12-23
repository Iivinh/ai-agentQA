---
type: table_description
name: EVENT_TRAINING_POINT
---
**Bảng: EVENT_TRAINING_POINT (Sự kiện ảnh hưởng đến Điểm rèn luyện)**
*   **Mô tả nghiệp vụ:** Bảng này hoạt động như một **nhật ký chi tiết**, ghi lại từng sự kiện, hoạt động, thành tích hoặc vi phạm cụ thể có ảnh hưởng đến điểm rèn luyện của sinh viên trong một học kỳ. Điểm tổng kết trong bảng `TRAINING_POINT` chính là tổng hợp của các điểm số (`SCORE`) được ghi nhận trong bảng này.
*   **Các cột:**
    *   `ID_EVENT` (VARCHAR(10)): Mã định danh cho sự kiện hoặc hoạt động được ghi nhận.
    *   `ID_STUDENT` (VARCHAR(8)): Mã của sinh viên liên quan đến sự kiện.
    *   `SEMESTER` (INT): Học kỳ diễn ra sự kiện.
    *   `YEAR` (VARCHAR(20)): Năm học diễn ra sự kiện.
    *   `ID_CRITERIA` (VARCHAR(10)): Mã của Tiêu chí mà sự kiện này thuộc về (tham chiếu tới bảng `CRITERIA_TRAINING_POINT`).
    *   `NAME` (NVARCHAR(300)): Tên mô tả cụ thể của sự kiện. Ví dụ: "Tham gia chiến dịch Mùa Hè Xanh 2024" (điểm cộng), "Không tham gia sinh hoạt đầu năm" (điểm trừ).
    *   `SCORE` (INT): Số điểm được ghi nhận cho sự kiện này. **QUAN TRỌNG: Giá trị này có thể là số dương (điểm CỘNG cho thành tích, hoạt động) hoặc số âm (điểm TRỪ cho vi phạm, kỷ luật).**
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ năm cột: `(ID_EVENT, ID_STUDENT, SEMESTER, YEAR, ID_CRITERIA)`, đảm bảo mỗi lần ghi nhận một sự kiện cho sinh viên dưới một tiêu chí là duy nhất.
    *   Bộ ba cột `(ID_STUDENT, SEMESTER, YEAR)` tạo thành một khóa ngoại, liên kết tới một dòng điểm tổng kết tương ứng trong bảng `TRAINING_POINT`.
    *   Cột `ID_CRITERIA` là khóa ngoại, liên kết tới bảng `CRITERIA_TRAINING_POINT`.
