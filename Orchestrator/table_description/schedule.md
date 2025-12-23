---
type: table_description
name: SCHEDULE
---
**Bảng: SCHEDULE (Lớp học phần)**
*   **Mô tả nghiệp vụ:** Bảng này chứa thông tin chung và cốt lõi về một **Lớp học phần** được mở trong một học kỳ cụ thể. Mỗi dòng trong bảng này đại diện cho một môn học được giảng dạy. Đây là bảng "cha" chứa thông tin tổng quát, và các lịch học chi tiết (lý thuyết, thực hành) sẽ tham chiếu đến nó.
*   **Các cột:**
    *   `ID_SCHEDULE` (VARCHAR(8)): Mã của Lớp học phần, giúp phân biệt các lớp khác nhau của cùng một môn học.
    *   `ID_SUBJECT` (VARCHAR(8)): Mã môn học được giảng dạy trong lớp học phần này.
    *   `YEAR` (VARCHAR(20)): Năm học mà lớp học phần được mở.
    *   `SEMESTER` (INT): Học kỳ mà lớp học phần được mở.
    *   `DAY_NAME` (NVARCHAR(50)): Thứ trong tuần theo lịch chung (ví dụ: 'Thứ Hai').
    *   `SESSION` (INT): **Tổng số buổi học** theo kế hoạch của lớp học phần. Ví dụ: `15` có nghĩa là môn học này được thiết kế để học trong 15 buổi.
    *   `WEEK` (VARCHAR(50)): **Chuỗi ký tự biểu diễn các tuần học.** Đây là một chuỗi đặc biệt, trong đó mỗi vị trí (index) tương ứng với một tuần trong học kỳ. Ký tự tại một vị trí cho biết tuần đó có học hay không.
        *   **Ví dụ:** Chuỗi `-2345678-0----------` có nghĩa là lớp học phần này sẽ học vào các tuần: **2, 3, 4, 5, 6, 7, 8, và 10**.
    *   `START_PERIOD` (INT): Tiết học bắt đầu.
    *   `PERIODS` (INT): Tổng số tiết học trong một buổi.
    *   `TEACHER` (NVARCHAR(100)): Tên giảng viên phụ trách (có thể NULL).
    *   `ROOM` (VARCHAR(10)): Phòng học chung (có thể NULL).
    *   `NOTE` (NVARCHAR(300)): Ghi chú thêm.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ bốn cột: `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER)`.
    *   Đây là bảng trung tâm. Nó được tham chiếu bởi các bảng lịch chi tiết hơn như `THEORY_SCHEDULE`, `GROUP_PRACTICE`, cũng như bảng đăng ký của sinh viên `APPLY_SUBJECT` và lịch thi `EXAM_SUBJECT`.
    
