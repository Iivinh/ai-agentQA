---
type: concept
name: Optional Subjects System
---
**Khái niệm: Hệ thống Môn học Tự chọn**
*   **Mục đích:** Giải thích cách thức hoạt động của các môn học tự chọn, từ việc định nghĩa các nhóm, áp dụng chúng vào chương trình đào tạo, cho đến cách sinh viên lựa chọn môn học để đáp ứng yêu cầu.
*   **Luồng hoạt động và các thành phần chính:**

    **1. Định nghĩa các "Rổ" Tự chọn (Bảng `optional_group`):**
    *   Đầu tiên, hệ thống định nghĩa ra các "rổ" chứa môn học tự chọn, gọi là các **Nhóm môn tự chọn**.
    *   Mỗi nhóm có một điều kiện hoàn thành mặc định, thường là yêu cầu tích lũy một số tín chỉ tối thiểu (`MIN_CREDIT`) HOẶC hoàn thành một số lượng môn học tối thiểu (`MIN_SUBJECT`).

    **2. Áp dụng và Tùy chỉnh cho Chương trình Đào tạo (Bảng `optional_group_program`):**
    *   Tiếp theo, các nhóm tự chọn này được áp dụng cho từng chương trình đào tạo cụ thể.
    *   Bảng này cho phép **tùy chỉnh** yêu cầu của nhóm cho từng chương trình. Ví dụ, nó có thể **ghi đè (override)** yêu cầu tín chỉ mặc định.
    *   Quan trọng hơn, nó cho phép **chia nhỏ yêu cầu** của một nhóm lớn ra nhiều học kỳ. Ví dụ, một nhóm yêu cầu 15 tín chỉ có thể được chia thành: "hoàn thành 6 tín chỉ trong học kỳ 5" và "hoàn thành 9 tín chỉ trong học kỳ 6".

    **3. Liệt kê các Môn học để Lựa chọn (Bảng `optional_group_subject`):**
    *   Cuối cùng, bảng này sẽ liệt kê chi tiết tất cả các môn học (`ID_SUBJECT`) mà sinh viên có thể lựa chọn từ một nhóm tự chọn (`ID_OPTIONAL_GROUP`) cụ thể.

*   **Tóm tắt quy trình kiểm tra yêu cầu cho sinh viên:**
    1.  Xác định chương trình và khóa học của sinh viên.
    2.  Truy vấn `optional_group_program` để tìm tất cả các nhóm tự chọn và yêu cầu (số tín chỉ/môn học) cho từng học kỳ mà sinh viên phải hoàn thành.
    3.  Truy vấn `optional_group_subject` để tìm danh sách các môn học mà sinh viên có thể chọn cho mỗi nhóm.
    4.  Đối chiếu với bảng `subject_result` của sinh viên để xem họ đã tích lũy đủ tín chỉ/môn học yêu cầu cho mỗi nhóm hay chưa.
