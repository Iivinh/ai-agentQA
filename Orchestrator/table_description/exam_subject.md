---
type: table_description
name: EXAM_SUBJECT
---
**Bảng: EXAM_SUBJECT (Lịch thi)**
*   **Mô tả nghiệp vụ:** Bảng này chứa thông tin chi tiết về lịch thi cuối kỳ của một Lớp học phần (`SCHEDULE`). Do một lớp học phần có thể có nhiều sinh viên, họ có thể được chia thành các tổ thi/nhóm thi nhỏ để thi ở các phòng khác nhau.
*   **Các cột:**
    *   `ID_SCHEDULE`, `ID_SUBJECT`, `YEAR`, `SEMESTER`: Các cột này cùng nhau tạo thành một khóa ngoại để liên kết tới một Lớp học phần cụ thể trong bảng `SCHEDULE`.
    *   `DAY` (DATE): Ngày thi chính thức. Đây là một phần của khóa chính.
    *   `START` (TIME(0)): Giờ bắt đầu thi.
    *   `DURATION` (INT): Thời gian làm bài thi, tính bằng phút.
    *   `ROOM` (VARCHAR(10)): Phòng thi.
    *   `SUB_GROUP` (VARCHAR(10)): Tên hoặc mã của **Tổ thi / Nhóm thi**. Sinh viên trong cùng một lớp học phần có thể được chia vào các tổ thi khác nhau.
    *   `TYPE` (NVARCHAR(20)): Hình thức thi. Ví dụ: 'Tự luận', 'Trắc nghiệm', 'Vấn đáp', 'Bài tập lớn'.
    *   `DAY_NAME` (NVARCHAR(20)): Thứ trong tuần của ngày thi.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ sáu cột: `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER, DAY, START)`.
    *   Bộ bốn cột `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER)` là khóa ngoại, liên kết tới bảng `SCHEDULE`.
