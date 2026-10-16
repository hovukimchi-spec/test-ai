# Mạng ring CSG Nhà Bè

- `DE_XUAT_MO_HINH.md`: phác thảo mô hình, quy ước đã chốt, nhật ký các lần cập nhật.
- `extract_sources.py` + `parse_mx.py`: trích dữ liệu từ các file ghi tay (BBNT, ODF, MX, độ dài cáp, KML) vào `data/`.
- `data/cables.json`, `data/paths/*.json`: cáp vật lý và đường đi từng link (do người dùng mô tả / suy từ sơ đồ).
- `model.py`: cấu hình + `build()`; đồ thị core, truy vết, quỹ core, hồ sơ cáp.
- `build_xlsx.py` → `ring_network_NhaBe.xlsx`; `build_html.py` + `viewer_template.html` → `ring_network_viewer.html` (một file, offline).

## Liên kết Excel ↔ HTML
- **Lớp dữ liệu sửa được** nằm trong 4 sheet của Excel: `DL_Cáp` (mã cáp, chỉ số mét, chiều dài, gắn MX), `DL_Link` + `DL_Bước` (đường đi từng link), `DL_Nhãn MX` (nhãn hàn/hư từng core tại MX).
- `ring_network_viewer.html` chứa sẵn động cơ tính (`engine.js`, đã kiểm tra khớp 100% với `model.py`) và bản dữ liệu nhúng. Bấm **📂 Mở Excel** → HTML đọc 4 sheet DL_ và tính lại toàn bộ (truy vết core, quỹ core, hồ sơ cáp, ODF AGG…). Sửa trong HTML (tab **Cáp**: mã cáp/chỉ số/dài; tab **Măng xông**: chạm từng core để đặt nhãn/trạm/hư; nút “Đề xuất nhãn từ đường đi”) rồi **💾 Lưu Excel** → chỉ 4 sheet DL_ được ghi lại, các sheet khác giữ nguyên byte.
- Chrome/Edge máy tính & Android: lưu thẳng vào file đã mở. Trình duyệt không hỗ trợ (Safari/iPhone): “Lưu” tải file mới về, thay file cũ.
- Các sheet tính toán khác trong Excel (Quỹ core, Phối core…) **chỉ cập nhật khi dựng lại**: `python3 import_inputs.py <file.xlsx>` (ghi vào `data/`) rồi `python3 build_xlsx.py && python3 build_html.py`.
- `export_data.py` xuất `raw.json`/`expected.json` để kiểm thử động cơ JS so với Python.
Hoặc sửa trực tiếp các file nguồn gốc (sổ độ dài cáp, sơ đồ MX) rồi chạy `extract_sources.py <thư_mục>` + hai lệnh build.
