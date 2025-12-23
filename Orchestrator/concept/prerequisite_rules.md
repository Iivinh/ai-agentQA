---
type: concept
name: Prerequisite Rules
---
**Khái niệm: Các loại quy tắc ràng buộc Môn học**
*   **Mục đích:** Giải thích tất cả các điều kiện mà một sinh viên có thể cần phải thỏa mãn trước khi được phép đăng ký một môn học. Một môn học có thể có nhiều loại ràng buộc khác nhau cùng lúc.
*   **Các loại quy tắc ràng buộc:**

    **1. Tiên quyết CỨNG (Strict Prerequisite):**
    *   **Ý nghĩa:** Sinh viên BẮT BUỘC phải học và có kết quả **'Đạt'** đối với môn học điều kiện từ một học kỳ trước đó.
    *   **Nơi lưu trữ dữ liệu:** Bảng `subject_strict_prerequisite`.

    **2. Học trước / Tiên quyết MỀM (Soft Prerequisite):**
    *   **Ý nghĩa:** Sinh viên CHỈ CẦN **ĐÃ TỪNG HỌC** môn học điều kiện, không quan trọng kết quả Đạt hay Rớt.
    *   **Nơi lưu trữ dữ liệu:** Bảng `subject_soft_prerequisite`.

    **3. Song hành (Parallel):**
    *   **Ý nghĩa:** Sinh viên phải đăng ký học môn học điều kiện **CÙNG LÚC** (trong cùng một học kỳ) với môn học chính.
    *   **Nơi lưu trữ dữ liệu:** Bảng `subject_parallel`.

    **4. Nhóm Tiên quyết CỨNG (Group Strict Prerequisite):**
    *   **Ý nghĩa:** Đây là quy tắc phức tạp nhất, yêu cầu sinh viên phải học và có kết quả **'Đạt'** đối với **TẤT CẢ** các môn học nằm trong một Nhóm tiên quyết đã được định nghĩa trước.
    *   **Nơi lưu trữ dữ liệu:** Quy tắc này được định nghĩa qua sự kết hợp của 3 bảng:
        *   `group_subject_strict_prerequisite`: Áp dụng một nhóm làm điều kiện cho môn chính.
        *   `prerequisite_group`: Định nghĩa tên nhóm.
        *   `prerequisite_group_subjects`: Liệt kê các môn học cụ thể trong từng nhóm.

*   **QUAN TRỌNG - Tóm tắt quy trình kiểm tra:**
    *   Khi người dùng hỏi về "điều kiện" hoặc "môn tiên quyết" của một môn học, Agent phải kiểm tra **TẤT CẢ** các bảng liên quan (`subject_strict_prerequisite`, `subject_soft_prerequisite`, `subject_parallel`, và hệ thống các bảng nhóm) để cung cấp một câu trả lời đầy đủ và chính xác nhất.
