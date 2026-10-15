# Mạng ring CSG Nhà Bè

- `DE_XUAT_MO_HINH.md`: phác thảo mô hình, quy ước đã chốt, mâu thuẫn dữ liệu.
- `extract_sources.py`: trích dữ liệu từ các file ghi tay (BBNT, ODF, MX, độ dài cáp, KML) vào `data/`.
- `model.py`: cấu hình + `build()`; quy ước suy hao theo từng đoạn, mô phỏng đứt cáp, quy tắc nhãn hàn (`splice_pairs`).
- `build_xlsx.py` → `ring_network_NhaBe.xlsx` (công thức sống; tham số ở sheet "Tham số").
- `build_html.py` + `viewer_template.html` → `ring_network_viewer.html` (một file, offline): bản đồ ring, giả lập đứt cáp, OTDR → vị trí, ODF.

Dựng lại: `python3 build_xlsx.py && python3 build_html.py` (cần openpyxl).
Chưa có: bảng hàn từng khay của măng xông, số core đối tác, chỉ số mét hai đầu từng cáp.
