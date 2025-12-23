---
type: table_description
name: OPTIONAL_GROUP_PROGRAM
---
**Bảng: OPTIONAL_GROUP_PROGRAM (Áp dụng Nhóm tự chọn cho Chương trình đào tạo)**
*   **Mô tả nghiệp vụ:** Bảng này đóng vai trò áp dụng và cấu hình một Nhóm môn tự chọn cho một Chương trình đào tạo cụ thể. Nó trả lời câu hỏi: "Chương trình X, khóa Y cần hoàn thành nhóm tự chọn nào, vào học kỳ mấy, và với yêu cầu cụ thể là gì?". Bảng này cũng cho phép chia nhỏ yêu cầu của một nhóm tự chọn lớn ra nhiều học kỳ khác nhau.
*   **Các cột:**
    *   `ID_OPTIONAL_GROUP` (VARCHAR(20)): Mã của Nhóm môn tự chọn được áp dụng.
    *   `ID_PROGRAM` (VARCHAR(8)): Mã của chương trình đào tạo.
    *   `ADMISSION_YEAR` (INT): Khóa tuyển sinh của chương trình đào tạo.
    *   `SEMESTER` (INT): Học kỳ mà nhóm tự chọn này được xếp vào theo lộ trình.
    *   `CREDIT` (INT): Số tín chỉ yêu cầu cho nhóm này, áp dụng riêng cho học kỳ và chương trình đào tạo này.
    *   `SUBJECT` (INT): Số lượng môn học yêu cầu cho nhóm này, áp dụng riêng cho học kỳ và chương trình đào tạo này.
    *   `NOTE` (NVARCHAR(300)): Ghi chú thêm.
*   **Lưu ý quan trọng về các quy tắc:**
    *   **Quy tắc Điều kiện Tối thiểu:** Tương tự như bảng `OPTIONAL_GROUP`, yêu cầu cho nhóm tự chọn này thường sẽ dựa trên `CREDIT` (số tín chỉ tối thiểu) **hoặc** `SUBJECT` (số lượng môn học tối thiểu). Một trong hai cột này sẽ có giá trị và cột còn lại sẽ là NULL.
    *   **Quy tắc Ghi đè (Override):** Các cột `CREDIT` và `SUBJECT` trong bảng này có độ ưu tiên cao hơn. Nếu chúng có giá trị, chúng sẽ ghi đè lên các giá trị `MIN_CREDIT` và `MIN_SUBJECT` mặc định trong bảng `OPTIONAL_GROUP`.
    *   **Quy tắc Chia nhỏ yêu cầu:** Vì `SEMESTER` là một phần của khóa chính, bạn có thể tạo nhiều dòng cho cùng một `ID_OPTIONAL_GROUP` nhưng khác `SEMESTER`. Điều này cho phép chia nhỏ tổng yêu cầu của một nhóm ra nhiều học kỳ.
*   **Lưu ý quan trọng về mối quan hệ và khóa:**
    *   Khóa chính của bảng này là một bộ bốn cột: `(ID_OPTIONAL_GROUP, ID_PROGRAM, ADMISSION_YEAR, SEMESTER)`.
    *   Cặp cột `(ID_PROGRAM, ADMISSION_YEAR)` là khóa ngoại, liên kết tới bảng `PROGRAM`.
    *   Cột `ID_OPTIONAL_GROUP` là khóa ngoại, liên kết tới bảng `OPTIONAL_GROUP`.
