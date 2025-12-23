---
type: table_description
name: GROUP_PRACTICE
---
**Bảng: GROUP_PRACTICE (Nhóm Thực hành)**
*   **Mô tả nghiệp vụ:** Bảng này dùng để định nghĩa các **Nhóm Thực hành** khác nhau cho một Lớp học phần. Một lớp học phần lý thuyết lớn có thể được chia thành nhiều nhóm nhỏ để học thực hành, và mỗi dòng trong bảng này đại diện cho một nhóm như vậy. Mỗi nhóm thực hành sẽ có lịch học riêng (khác thứ, khác buổi, khác tuần, hoặc khác giảng viên).
*   **Các cột:**
    *   `ID_SCHEDULE`, `ID_SUBJECT`, `YEAR`, `SEMESTER`: Các cột này cùng nhau tạo thành một khóa ngoại để liên kết tới một Lớp học phần "cha" trong bảng `SCHEDULE`.
    *   `ID_GROUP` (VARCHAR(8)): Mã định danh cho Nhóm Thực hành. Ví dụ: '01', '02'. Đây là một phần của khóa chính.
    *   `DAY_NAME` (NVARCHAR(50)): Thứ trong tuần mà nhóm này học thực hành.
    *   `SESSION` (INT): **Tổng số buổi học** theo kế hoạch của nhóm thực hành. Ví dụ: `10` có nghĩa là việc học thực hành này được thiết kế để học trong 10 buổi.
    *   `WEEK` (VARCHAR(50)): Chuỗi ký tự biểu diễn các tuần học thực hành của nhóm này. (Giải thích quy tắc mã hóa tương tự bảng `SCHEDULE`).
    *   `START_PERIOD` (INT): Tiết học bắt đầu.
    *   `PERIODS` (INT): Tổng số tiết học trong một buổi thực hành.
    *   `TEACHER` (NVARCHAR(100)): Tên giảng viên phụ trách nhóm thực hành này (có thể NULL).
    *   `ROOM` (VARCHAR(10)): Phòng học thực hành của nhóm (có thể NULL).
    *   `NOTE` (NVARCHAR(300)): Ghi chú thêm cho nhóm.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ năm cột: `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER, ID_GROUP)`.
    *   Lịch học thực hành chi tiết theo ngày của mỗi nhóm sẽ được lưu trong bảng `PRACTICE_SCHEDULE`.
