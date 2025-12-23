---
type: table_description
name: SUBJECT_RESULT
---
**Bảng: SUBJECT_RESULT (Kết quả môn học)**
*   **Mô tả nghiệp vụ:** Bảng này lưu trữ kết quả học tập chi tiết của sinh viên cho mỗi lần học một môn học. Vì sinh viên có thể học lại một môn nhiều lần nếu trượt, bảng này sử dụng cột `ATTEMPT` để phân biệt các lần học đó.
*   **Các cột:**
    *   `ID_STUDENT` (VARCHAR(8)): Mã của sinh viên có kết quả học tập.
    *   `ID_SUBJECT` (VARCHAR(8)): Mã của môn học được ghi nhận kết quả.
    *   `ATTEMPT` (INT): Lần học thứ mấy của sinh viên đối với môn học này. **Ví dụ: `1` là lần học đầu tiên, `2` là lần học lại thứ nhất.**
    *   **Các cột điểm thành phần (FLOAT):** Các điểm này có thể có giá trị NULL nếu môn học chưa có hoặc không có cột điểm tương ứng.
        *   `TEST_1`: Điểm quá trình 1.
        *   `TEST_2`: Điểm quá trình 2.
        *   `MIDTERM_TEST`: Điểm thi giữa kỳ.
        *   `FINAL_TEST`: Điểm thi cuối kỳ.
    *   `STATUS` (NVARCHAR(10)): Trạng thái cuối cùng của môn học sau lần học này. **QUAN TRỌNG: Các giá trị thường gặp là 'Đạt' (Passed) hoặc 'Rớt' (Failed).**
*   **Lưu ý quan trọng về khóa:**
    *   Khóa chính của bảng này là một bộ ba cột: `(ID_STUDENT, ID_SUBJECT, ATTEMPT)`. Điều này đảm bảo mỗi lần học một môn của một sinh viên là duy nhất.
    *   Cột `ID_STUDENT` là khóa ngoại, liên kết tới bảng `STUDENT`.
    *   Cột `ID_SUBJECT` là khóa ngoại, liên kết tới bảng `SUBJECT`.
