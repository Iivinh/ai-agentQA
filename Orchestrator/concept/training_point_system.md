---
type: concept
name: Training Point System
---
**Khái niệm: Hệ thống Điểm rèn luyện**
*   **Mục đích:** Giải thích cách hệ thống theo dõi, tính toán và tổng hợp điểm rèn luyện cho sinh viên theo từng học kỳ.
*   **Luồng hoạt động và các thành phần chính:**

    **1. Định nghĩa Khung đánh giá (Bảng `criteria_training_point`):**
    *   Đầu tiên, hệ thống định nghĩa một bộ các **Tiêu chí** để làm khung đánh giá điểm rèn luyện.
    *   Mỗi tiêu chí có một mã (`ID_CRITERIA`), tên (ví dụ: "Ý thức học tập") và có thể có một mức điểm tối đa (`SCORE`).

    **2. Ghi nhận các Sự kiện chi tiết (Bảng `event_training_point`):**
    *   Đây là bảng ghi lại nhật ký chi tiết. Mỗi khi có một hoạt động ảnh hưởng đến điểm rèn luyện của sinh viên, một dòng mới sẽ được tạo trong bảng này.
    *   Mỗi sự kiện được ghi nhận sẽ thuộc về một **Tiêu chí** cụ thể (`ID_CRITERIA`).
    *   **QUAN TRỌNG:** Điểm số (`SCORE`) trong bảng này có thể là **số dương (điểm CỘNG)** cho các thành tích, hoạt động tốt, hoặc **số âm (điểm TRỪ)** cho các vi phạm, kỷ luật.

    **3. Tổng hợp Kết quả cuối cùng (Bảng `training_point`):**
    *   Cuối mỗi học kỳ, điểm số từ tất cả các sự kiện của một sinh viên trong bảng `event_training_point` sẽ được **tổng hợp** lại.
    *   Kết quả tổng kết cuối cùng này được lưu vào bảng `training_point`. Bảng này chỉ chứa một dòng duy nhất cho mỗi sinh viên trong một học kỳ/năm học cụ thể.

*   **Tóm tắt luồng tính toán:**
    *   Nhiều sự kiện trong `EVENT_TRAINING_POINT` (được phân loại bởi `CRITERIA_TRAINING_POINT`) được cộng dồn lại để tạo thành một điểm tổng kết duy nhất trong `TRAINING_POINT`.
