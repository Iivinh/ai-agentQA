---
type: concept
name: Course Registration and Schedule Workflow
---
**Khái niệm: Quy trình Đăng ký môn học và Xếp lịch**
*   **Mục đích:** Giải thích luồng dữ liệu hoàn chỉnh của quá trình đăng ký và xếp lịch cho một sinh viên trong một học kỳ, kết nối các bảng `SCHEDULE`, `THEORY_SCHEDULE`, `GROUP_PRACTICE`, `PRACTICE_SCHEDULE`, `APPLY_SUBJECT`, và `EXAM_SUBJECT`.
*   **Luồng hoạt động (Workflow):**

    **1. Mở Lớp học phần (Bảng `SCHEDULE`):**
    *   Mọi thứ bắt đầu từ bảng `SCHEDULE`. Đây là bảng trung tâm, định nghĩa một "Lớp học phần" (một môn học cụ thể được mở trong một kỳ). Nó chứa kế hoạch học tập chung (ví dụ: học vào Thứ Hai, trong 15 buổi, vào các tuần 2,3,4...).

    **2. Chi tiết hóa Lịch học (Lý thuyết và Thực hành):**
    *   Từ kế hoạch chung trong `SCHEDULE`, lịch học được chi tiết hóa thành các ngày cụ thể:
        *   **Lịch Lý thuyết:** Bảng `THEORY_SCHEDULE` lấy thông tin từ `SCHEDULE` và tạo ra các dòng cho từng buổi học lý thuyết với ngày tháng chính xác.
        *   **Lịch Thực hành (Quy trình 2 bước):**
            a. Đầu tiên, bảng `GROUP_PRACTICE` chia một Lớp học phần thành nhiều "Nhóm Thực hành" nhỏ (ví dụ: 01, 02), mỗi nhóm có thể có lịch chung riêng.
            b. Sau đó, bảng `PRACTICE_SCHEDULE` sẽ chi tiết hóa lịch cho **từng nhóm thực hành** đó thành các ngày tháng cụ thể.

    **3. Sinh viên Đăng ký (Bảng `APPLY_SUBJECT`):**
    *   Đây là bảng ghi lại hành động của sinh viên. Khi một sinh viên đăng ký, một dòng mới sẽ được tạo trong `APPLY_SUBJECT`.
    *   Dòng này tạo ra một liên kết quan trọng: nó nối một `STUDENT` với một `SCHEDULE` (cho phần lý thuyết) và một `GROUP_PRACTICE` (cho phần thực hành mà sinh viên đã chọn).

    **4. Lên Lịch thi (Bảng `EXAM_SUBJECT`):**
    *   Cuối cùng, lịch thi cuối kỳ cho toàn bộ Lớp học phần (`SCHEDULE`) sẽ được định nghĩa trong bảng `EXAM_SUBJECT`, bao gồm ngày, giờ, phòng thi và hình thức thi.

*   **Tóm tắt luồng dữ liệu:**
    *   **Về cấu trúc lịch:** `SCHEDULE` là "cha" của `THEORY_SCHEDULE` và `GROUP_PRACTICE`. `GROUP_PRACTICE` là "cha" của `PRACTICE_SCHEDULE`.
    *   **Về hành động của sinh viên:** `STUDENT` --(thông qua `APPLY_SUBJECT`)--> liên kết với `SCHEDULE` và `GROUP_PRACTICE`.
    *   **Về lịch thi:** `SCHEDULE` --(dẫn đến)--> `EXAM_SUBJECT`.
