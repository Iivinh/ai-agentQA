---
type: concept
name: Academic Program and Results Workflow
---
**Khái niệm: Lộ trình học tập và Kết quả của Sinh viên**
*   **Mục đích:** Giải thích luồng thông tin hoàn chỉnh từ lúc xác định chương trình học cho một sinh viên cho đến khi ghi nhận kết quả học tập của họ.
*   **Luồng hoạt động (Workflow):**
    1.  **Xác định Lộ trình cho Sinh viên:**
        *   Mỗi sinh viên trong bảng `STUDENT` được gán vào một phiên bản chương trình đào tạo cụ thể thông qua hai cột: `ID_PROGRAM` và `ADMISSION_YEAR`.
        *   Cặp giá trị này liên kết duy nhất tới một dòng trong bảng `PROGRAM`, xác định rõ tổng số tín chỉ và số học kỳ của lộ trình đó.

    2.  **Chi tiết hóa Lộ trình:**
        *   Từ `PROGRAM`, chúng ta sử dụng bảng `PROGRAM_SUBJECT` để xem chi tiết các môn học (`ID_SUBJECT`) mà sinh viên cần phải hoàn thành.
        *   Bảng `PROGRAM_SUBJECT` hoạt động như một **"Lộ trình học tập chuẩn"**, nó liệt kê tất cả các môn học bắt buộc và gợi ý chúng nên được học vào học kỳ (`SEMESTER`) nào.

    3.  **Ghi nhận Kết quả:**
        *   Khi sinh viên học một môn học trong lộ trình, kết quả sẽ được ghi vào bảng `SUBJECT_RESULT`.
        *   Bảng này theo dõi kết quả của từng lần học thông qua cột `ATTEMPT`. Nếu một sinh viên học lại môn, sẽ có một dòng mới với giá trị `ATTEMPT` tăng lên.
        *   Trạng thái cuối cùng của lần học đó (`'Đạt'` hay `'Rớt'`) được lưu trong cột `STATUS`.

*   **Tóm tắt luồng liên kết:**
    `STUDENT` -> `PROGRAM` -> `PROGRAM_SUBJECT` -> `SUBJECT_RESULT`
