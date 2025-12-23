---
type: table_description
name: THEORY_SCHEDULE
---
**Bảng: THEORY_SCHEDULE (Lịch học Lý thuyết chi tiết)**
*   **Mô tả nghiệp vụ:** Bảng này chi tiết hóa lịch học cho phần **lý thuyết** của một Lớp học phần đã được định nghĩa trong bảng `SCHEDULE`. Mỗi dòng trong bảng này đại diện cho một buổi học lý thuyết diễn ra vào một **ngày cụ thể**.
*   **Cách hoạt động:** Trong khi bảng `SCHEDULE` đưa ra một kế hoạch chung (ví dụ: "học vào các tuần 2, 3, 4..."), bảng này sẽ chuyển đổi kế hoạch đó thành các ngày thực tế trên lịch (ví dụ: '2024-09-09', '2024-09-16', '2024-09-23'...).
*   **Các cột:**
    *   `ID_SCHEDULE`, `ID_SUBJECT`, `YEAR`, `SEMESTER`: Các cột này cùng nhau tạo thành một khóa ngoại để liên kết tới một Lớp học phần cụ thể trong bảng `SCHEDULE`.
    *   `DAY` (DATE): Ngày diễn ra buổi học lý thuyết theo lịch. Đây là một phần của khóa chính.
    *   `DAY_NAME` (NVARCHAR(50)): Thứ trong tuần của ngày học đó.
    *   `ROOM` (VARCHAR(10)): Phòng học cho buổi học cụ thể này.
    *   `STATUS` (NVARCHAR(100)): Trạng thái của buổi học. Ví dụ: 'Bình thường', 'Báo vắng', 'Học bù'.
    *   `START_PERIOD` (INT): Tiết học bắt đầu.
    *   `PERIODS` (INT): Tổng số tiết học trong buổi học này.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ năm cột: `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER, DAY)`.
    *   Bộ bốn cột `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER)` là khóa ngoại, liên kết tới bảng `SCHEDULE`, thể hiện mối quan hệ cha-con.
