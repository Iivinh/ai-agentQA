import json

# Chuỗi JSON bạn nhận được từ Gemini (dưới dạng text)
json_string_from_gemini = r"""
{
  "sql_query": "DECLARE @TargetSubjectID VARCHAR(8);\nSELECT @TargetSubjectID = ID_SUBJECT FROM SUBJECT WHERE NAME = N'Cấu trúc dữ liệu và giải thuật';\n\n-- Strict Prerequisites\nSELECT\n    N'Tiên quyết CỨNG' AS LoaiDieuKien,\n    S_prereq.NAME AS MonHocDieuKien,\n    S_prereq.ID_SUBJECT AS MaMonHocDieuKien,\n    NULL AS TenNhom\nFROM SUBJECT_STRICT_PREREQUISITE AS SSP\nJOIN SUBJECT AS S_prereq ON SSP.ID_SUBJECT_STRICT_PREREQUISITE = S_prereq.ID_SUBJECT\nWHERE SSP.ID_SUBJECT = @TargetSubjectID\n\nUNION ALL\n\n-- Soft Prerequisites\nSELECT\n    N'Học trước (Tiên quyết MỀM)' AS LoaiDieuKien,\n    S_prereq.NAME AS MonHocDieuKien,\n    S_prereq.ID_SUBJECT AS MaMonHocDieuKien,\n    NULL AS TenNhom\nFROM SUBJECT_SOFT_PREREQUISITE AS SSP\nJOIN SUBJECT AS S_prereq ON SSP.ID_SUBJECT_SOFT_PREREQUISITE = S_prereq.ID_SUBJECT\nWHERE SSP.ID_SUBJECT = @TargetSubjectID\n\nUNION ALL\n\n-- Parallel Subjects\nSELECT\n    N'Song hành' AS LoaiDieuKien,\n    S_prereq.NAME AS MonHocDieuKien,\n    S_prereq.ID_SUBJECT AS MaMonHocDieuKien,\n    NULL AS TenNhom\nFROM SUBJECT_PARALLEL AS SP\nJOIN SUBJECT AS S_prereq ON SP.ID_SUBJECT_PARALLEL = S_prereq.ID_SUBJECT\nWHERE SP.ID_SUBJECT = @TargetSubjectID\n\nUNION ALL\n\n-- Group Strict Prerequisites\nSELECT\n    N'Nhóm Tiên quyết CỨNG' AS LoaiDieuKien,\n    S_prereq.NAME AS MonHocDieuKien,\n    S_prereq.ID_SUBJECT AS MaMonHocDieuKien,\n    PG.NAME AS TenNhom\nFROM GROUP_SUBJECT_STRICT_PREREQUISITE AS GSSP\nJOIN PREREQUISITE_GROUP AS PG ON GSSP.ID_GROUP = PG.ID_GROUP\nJOIN PREREQUISITE_GROUP_SUBJECTS AS PGS ON GSSP.ID_GROUP = PGS.ID_GROUP\nJOIN SUBJECT AS S_prereq ON PGS.ID_SUBJECT = S_prereq.ID_SUBJECT\nWHERE GSSP.ID_SUBJECT = @TargetSubjectID;"
}
"""

# Phân tích JSON thành dictionary của Python
# THÊM .strip() VÀO ĐÂY!
plan = json.loads(json_string_from_gemini.strip())

# Lấy ra câu lệnh SQL
sql_command = plan['sql_query']

# In ra câu lệnh SQL
print("--- Phân tích JSON thành công! ---")
print("Câu lệnh SQL để thực thi:")
print(sql_command)