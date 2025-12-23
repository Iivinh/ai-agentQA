---
type: table_description
name: OPTIONAL_GROUP_SUBJECT
---
**Bảng: OPTIONAL_GROUP_SUBJECT (Các môn học trong Nhóm tự chọn)**
*   **Mô tả nghiệp vụ:** Bảng này chi tiết hóa thành phần của mỗi Nhóm môn tự chọn. Nó trả lời câu hỏi: "Nhóm Tự chọn X bao gồm những môn học cụ thể nào mà sinh viên có thể đăng ký?". Mỗi dòng trong bảng này thể hiện rằng một môn học thuộc về một nhóm.
*   **Cách hoạt động:** Để tìm tất cả các môn học mà sinh viên có thể chọn trong một nhóm, bạn sẽ truy vấn bảng này bằng cách lọc theo `ID_OPTIONAL_GROUP`. Tất cả các `ID_SUBJECT` được trả về chính là danh sách các môn học trong nhóm đó.
*   **Các cột:**
    *   `ID_OPTIONAL_GROUP` (VARCHAR(20)): Mã của Nhóm môn tự chọn.
    *   `ID_SUBJECT` (VARCHAR(8)): Mã của một môn học thuộc về nhóm đó.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Đây là một bảng quan hệ, tạo ra mối liên kết nhiều-nhiều giữa `OPTIONAL_GROUP` và `SUBJECT`.
    *   Khóa chính của bảng này là một cặp cột: `(ID_OPTIONAL_GROUP, ID_SUBJECT)`.
    *   Cột `ID_OPTIONAL_GROUP` là khóa ngoại, liên kết tới bảng `OPTIONAL_GROUP`.
    *   Cột `ID_SUBJECT` là khóa ngoại, liên kết tới bảng `SUBJECT`.
