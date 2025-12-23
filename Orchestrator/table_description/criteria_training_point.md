---
type: table_description
name: CRITERIA_TRAINING_POINT
---
**Bảng: CRITERIA_TRAINING_POINT (Tiêu chí Điểm rèn luyện)**
*   **Mô tả nghiệp vụ:** Bảng này đóng vai trò là một danh mục, dùng để định nghĩa các **Tiêu chí** được sử dụng để đánh giá điểm rèn luyện. Mỗi dòng trong bảng này đại diện cho một tiêu chí cụ thể.
*   **Ví dụ về các tiêu chí:** "Việc tuân thủ kỷ luật, nề nếp", "Việc tham gia các hoạt động chuyên môn học thuật", "Tinh thần tiên phong, gương mẫu", v.v.
*   **Các cột:**
    *   `ID_CRITERIA` (VARCHAR(10)): Mã định danh duy nhất cho mỗi Tiêu chí. Đây là khóa chính.
    *   `NAME` (NVARCHAR(300)): Tên mô tả đầy đủ của tiêu chí.
    *   `SCORE` (INT): Mức điểm tối đa có thể đạt được cho tiêu chí này.
