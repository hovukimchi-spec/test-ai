# FTTH Phố Đông – thiết kế phối quang (Tháp A + B)

| File | Dùng để |
|---|---|
| `FTTH_PhoDong_PhoiQuang.xlsx` | Sổ vận hành: tổng quan PON, sơ đồ trục, danh mục tủ, bảng sợi trục, bảng ODF-PM, 644 thuê bao, tra cứu, quỹ công suất, vật tư, quy trình |
| `ftth_viewer.html` | Công cụ xem trực quan (mở bằng trình duyệt, chạy offline): tìm căn hộ → đường quang tới PON, giả lập sự cố, tô màu theo PON/tủ/splitter/trạng thái |
| `model.py` | Cấu hình duy nhất (số hộ/tầng, tầng đặt tủ, nhóm trục, số splitter). Sửa rồi chạy `python3 build_xlsx.py && python3 build_html.py` |

Kiến trúc: ONU –1FO– splitter 1:16 (tủ) – cáp trục 24FO (4 ống × 6 sợi; 8FO/tủ) – ODF 48FO (hầm B1) – splitter 1:4 (dùng 3, dự phòng 1) – PON. Số căn/tầng lấy từ bản vẽ (`homes_from_drawing.json`), tổng 676 căn, 48 splitter 1:16.

## Đối chiếu sổ tay ↔ bản vẽ gốc
Xem sheet "Đối chiếu bản vẽ". Tháp B khớp 8/8; tháp A lệch 2 tủ (sổ tay 7F/5F, bản vẽ gốc ODF ở 6F/4F). Cụm gom tầng lấy từ bản vẽ gốc.

## Phòng máy (hầm B1)
OLT PON-k → dây nhảy → ODF-96FO cổng 64+k (vào splitter 1:4) · 4 đầu ra splitter → ODF-96FO cổng 4k-3…4k (dùng 3, cổng 4 dự phòng) → dây nhảy → ODF-48FO trục (ODF-02 → ODF-08/09 → ODF-17/18, xếp từ thấp lên cao). ODF-96: 4 hàng × 24 cột, đếm từ dưới lên, trái qua phải.
