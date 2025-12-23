---
type: table_description
name: PRACTICE_SCHEDULE
---
**Bảng: PRACTICE_SCHEDULE (Lịch học Thực hành chi tiết)**
*   **Mô tả nghiệp vụ:** Bảng này chi tiết hóa lịch học cho phần **thực hành** của một **Nhóm Thực hành** cụ thể (đã được định nghĩa trong bảng `GROUP_PRACTICE`). Mỗi dòng trong bảng này đại diện cho một buổi học thực hành diễn ra vào một **ngày cụ thể**.
*   **Cách hoạt động:** Trong khi bảng `GROUP_PRACTICE` đưa ra một kế hoạch chung cho một nhóm (ví dụ: "nhóm 01 học vào các tuần 2, 4, 6..."), bảng này sẽ chuyển đổi kế hoạch đó thành các ngày thực tế trên lịch (ví dụ: '2024-09-12', '2024-09-26', '2024-10-10'...).
*   **Các cột:**
    *   `ID_SCHEDULE`, `ID_SUBJECT`, `YEAR`, `SEMESTER`, `ID_GROUP`: Các cột này cùng nhau tạo thành một khóa ngoại để liên kết tới một Nhóm Thực hành cụ thể trong bảng `GROUP_PRACTICE`.
    *   `DAY` (DATE): Ngày diễn ra buổi học thực hành theo lịch. Đây là một phần của khóa chính.
    *   `DAY_NAME` (NVARCHAR(50)): Thứ trong tuần của ngày học đó.
    *   `ROOM` (VARCHAR(10)): Phòng học cho buổi thực hành cụ thể này.
    *   `STATUS` (NVARCHAR(100)): Trạng thái của buổi học. Ví dụ: 'Bình thường', 'Báo vắng', 'Học bù'.
    *   `START_PERIOD` (INT): Tiết học bắt đầu.
    *   `PERIODS` (INT): Tổng số tiết học trong buổi học này.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ sáu cột: `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER, ID_GROUP, DAY)`.
    *   Bộ năm cột `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER, ID_GROUP)` là khóa ngoại, liên kết tới bảng `GROUP_PRACTICE`, thể hiện mối quan hệ cha-con.
