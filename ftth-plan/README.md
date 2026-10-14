# FTTH Phố Đông – thiết kế phối quang (Tháp A + B)

| File | Dùng để |
|---|---|
| `FTTH_PhoDong_PhoiQuang.xlsx` | Sổ vận hành: tổng quan PON, sơ đồ trục, danh mục tủ, bảng sợi trục, bảng ODF-PM, 644 thuê bao, tra cứu, quỹ công suất, vật tư, quy trình |
| `ftth_viewer.html` | Công cụ xem trực quan (mở bằng trình duyệt, chạy offline): tìm căn hộ → đường quang tới PON, giả lập sự cố, tô màu theo PON/tủ/splitter/trạng thái |
| `model.py` | Cấu hình duy nhất (số hộ/tầng, tầng đặt tủ, nhóm trục, số splitter). Sửa rồi chạy `python3 build_xlsx.py && python3 build_html.py` |

Kiến trúc: ONU –1FO– splitter 1:16 (tủ) – cáp trục 24FO (4 ống × 6 sợi; 8FO/tủ) – ODF 48FO (hầm B1) – splitter 1:4 (dùng 3, dự phòng 1) – PON. Số căn/tầng lấy từ bản vẽ (`homes_from_drawing.json`), tổng 676 căn, 48 splitter 1:16.
