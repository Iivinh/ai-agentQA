---
type: table_description
name: PREREQUISITE_GROUP
---
**Bảng: PREREQUISITE_GROUP (Định nghĩa Nhóm môn tiên quyết)**
*   **Mô tả nghiệp vụ:** Bảng này đóng vai trò là danh mục, dùng để định nghĩa và đặt tên cho các **Nhóm môn tiên quyết**. Mỗi dòng trong bảng này đại diện cho một nhóm duy nhất.
*   **Lưu ý:** Bảng này chỉ định nghĩa "tên nhóm", nó **KHÔNG** chứa danh sách các môn học cụ thể thuộc về nhóm đó. Danh sách chi tiết các môn học được lưu trong bảng `PREREQUISITE_GROUP_SUBJECTS`.
*   **Các cột:**
    *   `ID_GROUP` (VARCHAR(30)): Mã định danh duy nhất cho mỗi Nhóm môn tiên quyết. Đây là khóa chính. Ví dụ: '28786_01_230305'.
    *   `NAME` (NVARCHAR(200)): Tên mô tả đầy đủ của nhóm, giúp dễ hiểu mục đích của nhóm. Ví dụ: 'Nhóm Khóa luận/Đồ án'.
