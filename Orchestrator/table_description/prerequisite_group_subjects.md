---
type: table_description
name: PREREQUISITE_GROUP_SUBJECTS
---
**Bảng: PREREQUISITE_GROUP_SUBJECTS (Các môn học trong Nhóm tiên quyết)**
*   **Mô tả nghiệp vụ:** Bảng này chi tiết hóa thành phần của mỗi Nhóm môn tiên quyết. Nó trả lời câu hỏi: "Nhóm X bao gồm những môn học cụ thể nào?". Mỗi dòng trong bảng này thể hiện rằng một môn học thuộc về một nhóm.
*   **Cách hoạt động:** Để tìm tất cả các môn học của một nhóm, bạn sẽ truy vấn bảng này bằng cách lọc theo `ID_GROUP`. Tất cả các `ID_SUBJECT` được trả về chính là danh sách các môn học trong nhóm đó.
*   **Các cột:**
    *   `ID_GROUP` (VARCHAR(8)): Mã của Nhóm môn tiên quyết.
    *   `ID_SUBJECT` (VARCHAR(8)): Mã của một môn học thuộc về nhóm đó.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Đây là một bảng quan hệ, tạo ra mối liên kết nhiều-nhiều giữa `PREREQUISITE_GROUP` và `SUBJECT`.
    *   Khóa chính của bảng này là một cặp cột: `(ID_GROUP, ID_SUBJECT)`.
    *   Cột `ID_GROUP` là khóa ngoại, liên kết tới bảng `PREREQUISITE_GROUP`.
    *   Cột `ID_SUBJECT` là khóa ngoại, liên kết tới bảng `SUBJECT`.
