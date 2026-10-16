# Mạng ring CSG Nhà Bè

- `DE_XUAT_MO_HINH.md`: phác thảo mô hình, quy ước đã chốt, nhật ký các lần cập nhật.
- `extract_sources.py` + `parse_mx.py`: trích dữ liệu từ các file ghi tay (BBNT, ODF, MX, độ dài cáp, KML) vào `data/`.
- `data/cables.json`, `data/paths/*.json`: cáp vật lý và đường đi từng link (do người dùng mô tả / suy từ sơ đồ).
- `model.py`: cấu hình + `build()`; đồ thị core, truy vết, quỹ core, hồ sơ cáp.
- `build_xlsx.py` → `ring_network_NhaBe.xlsx`; `build_html.py` + `viewer_template.html` → `ring_network_viewer.html` (một file, offline).

## Cập nhật thông tin
Excel và HTML là file sinh ra, **không tự đồng bộ**. Cách cập nhật:
1. Mở sheet `Nhập mã cáp` (mã cáp, chỉ số mét, độ dài) và `Nhập nhãn MX` (nhãn core măng xông) trong Excel, điền ô vàng.
2. `python3 import_inputs.py <file.xlsx>` → ghi `data/overrides.json`.
3. `python3 build_xlsx.py && python3 build_html.py` → dựng lại cả hai.
Hoặc sửa trực tiếp các file nguồn gốc (sổ độ dài cáp, sơ đồ MX) rồi chạy `extract_sources.py <thư_mục>` + hai lệnh build.
