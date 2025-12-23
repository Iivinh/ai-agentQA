---
type: table_description
name: OPTIONAL_GROUP
---
**Bảng: OPTIONAL_GROUP (Định nghĩa Nhóm môn tự chọn)**
*   **Mô tả nghiệp vụ:** Bảng này dùng để định nghĩa các **Nhóm môn học tự chọn**. Mỗi nhóm là một tập hợp các môn học mà sinh viên có thể lựa chọn để tích lũy tín chỉ hoặc hoàn thành một yêu cầu cụ thể của chương trình đào tạo.
*   **Lưu ý:** Bảng này chỉ định nghĩa "tên nhóm" và "điều kiện hoàn thành nhóm" (số tín chỉ hoặc số môn học tối thiểu). Danh sách các môn học cụ thể thuộc nhóm được lưu trong bảng `OPTIONAL_GROUP_SUBJECT`.
*   **Các cột:**
    *   `ID_OPTIONAL_GROUP` (VARCHAR(20)): Mã định danh duy nhất cho mỗi Nhóm môn tự chọn. Đây là khóa chính. Ví dụ: 'TC_KHXH'.
    *   `NAME` (NVARCHAR(200)): Tên mô tả đầy đủ của nhóm. Ví dụ: 'Nhóm Tự chọn Khoa học Xã hội'.
    *   `MIN_CREDIT` (INT): Số tín chỉ **tối thiểu** mà sinh viên phải tích lũy từ các môn học thuộc nhóm này để được công nhận là đã hoàn thành yêu cầu của nhóm. Có thể có giá trị NULL nếu điều kiện dựa trên số lượng môn học.
    *   `MIN_SUBJECT` (INT): Số lượng môn học **tối thiểu** mà sinh viên phải hoàn thành từ nhóm này. Có thể có giá trị NULL nếu điều kiện dựa trên số tín chỉ.
*   **Lưu ý quan trọng về quy tắc:**
    *   Thông thường, một nhóm sẽ có điều kiện dựa trên `MIN_CREDIT` **hoặc** `MIN_SUBJECT`. Một trong hai cột này sẽ có giá trị và cột còn lại sẽ là NULL.
