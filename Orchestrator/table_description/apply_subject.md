---
type: table_description
name: APPLY_SUBJECT
---
**Bảng: APPLY_SUBJECT (Đăng ký môn học của Sinh viên)**
*   **Mô tả nghiệp vụ:** Bảng này ghi lại hành động một sinh viên (`ID_STUDENT`) đã đăng ký thành công vào một Lớp học phần (`ID_SCHEDULE`) trong một học kỳ cụ thể. Nếu lớp học phần đó có chia nhóm thực hành, bảng này cũng ghi lại sinh viên đã đăng ký vào Nhóm thực hành (`ID_GROUP`) nào.
*   **Các cột:**
    *   `ID_STUDENT` (VARCHAR(8)): Mã của sinh viên thực hiện đăng ký.
    *   `ID_SCHEDULE`, `ID_SUBJECT`, `YEAR`, `SEMESTER`: Các cột này xác định Lớp học phần mà sinh viên đã đăng ký.
    *   `ID_GROUP` (VARCHAR(8)): Mã của Nhóm thực hành mà sinh viên đã chọn. **Lưu ý: Cột này có thể không bắt buộc (nullable) hoặc có giá trị mặc định nếu môn học không có thực hành.**
    *   `DAY_APPLY` (DATETIME): Thời điểm chính xác (ngày và giờ) mà sinh viên đã thực hiện hành động đăng ký.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ năm cột: `(ID_STUDENT, ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER)`. Điều này đảm bảo một sinh viên chỉ có thể đăng ký vào một lớp học phần một lần duy nhất trong một học kỳ.
    *   Cột `ID_STUDENT` là khóa ngoại, liên kết tới bảng `STUDENT`.
    *   Bộ bốn cột `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER)` là khóa ngoại, liên kết tới bảng `SCHEDULE`.
    *   Bộ năm cột `(ID_SCHEDULE, ID_SUBJECT, YEAR, SEMESTER, ID_GROUP)` là khóa ngoại, liên kết tới bảng `GROUP_PRACTICE`, để xác định nhóm thực hành cụ thể.
