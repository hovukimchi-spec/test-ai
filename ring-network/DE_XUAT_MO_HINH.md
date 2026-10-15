# Mô hình mạng ring CSG khu vực Nhà Bè — phác thảo & đề xuất

> Nguồn: BBNT 1605/2025 (37 tuyến 2FO, đo OTDR), ODF.xlsx, MX__NHA_BE.xlsx, "Độ dài cáp Nhà Bè.xlsx".
> Các file nguồn là ghi chú thủ công, có sai lệch; mọi mâu thuẫn được đánh dấu để xác nhận, chưa tự sửa.
> `data/bbnt_segments.csv` là bảng 37 đoạn trích nguyên từ BBNT (cột `ring_suy_ra` do suy luận từ chuỗi điểm đầu/cuối).

## 1. Cấu trúc suy ra
- 2 trạm cấp 1: **AGG-HCMNBE12** (VNPT Long Thới) và **AGG-HCMNBE22** (KDC Sài Gòn Mới).
- **8 ring**, mỗi ring xuất phát từ NBE12 và về NBE22 qua chuỗi CSG (dual-homing). Mỗi đoạn thuê 2FO (1 cặp).
- ~36 CSG HNBxxx. Ring 3 có nhánh cụt HNB094→HNB018. Ring 5 có HNB113 đấu qua HNB012 (theo ODF, không có trong BBNT).

| Ring | Chuỗi CSG | km HĐ | km đo | Chênh |
|---|---|---|---|---|
| R1 | 059–060–048 | 28,28 | 29,86 | +6% |
| R2 | 054–006–091 | 18,49 | 20,38 | +10% |
| R3 | 055–065–094 (+018) | 21,13 | 22,70 | +7% |
| R4 | 011–056–071–073 | 20,47 | 22,15 | +8% |
| R5 | 012–014–075 (+113) | 25,24 | 26,29 | +4% |
| R6 | 086–024–027–031–020 | 11,29 | 12,22 | +8% |
| R7 | 005–062–021–013 | 14,06 | 15,07 | +7% |
| R8 | 066–016–038 | 13,48 | 19,17 | +42% |
| Tổng | | 152,44 | 167,83 | +10% |

## 2. Phát hiện mâu thuẫn / bất thường (cần xác nhận)
1. **Đoạn 1 (NBE12→HNB066)**: HĐ 10,236 km, đo 15,404 km (+50%) — kéo cả ring R8 lên +42%. Nghi sai km hợp đồng hoặc tuyến đi vòng.
2. Nhiều đoạn CSG–CSG đo dài hơn HĐ 23–67% (đoạn 18, 21, 22, 26, 27, 32). Dài hơn có thể do slack ở măng xông, không phải sai.
3. **Đoạn 31 (HNB054→HNB006)** core #1 = 2,359 dB trên 1,433 km (~1,65 dB/km) trong khi core #2 = 0,336 dB. Nghi mối hàn/uốn cong; BBNT vẫn ghi "Đạt".
4. Lệch hai core: đoạn 34 (1,664 vs 3,069 dB; chênh 1,4 dB) và đoạn 9 (0,227 vs 0,604 dB) vẫn trong ngưỡng 2 dB. Chỉ đoạn 31 vượt (chênh 2,02 dB).
5. ~~Ngưỡng cho phép không nhất quán~~ — **đã rút lại**: sau khi bạn chốt quy ước (mục 7), cả 37 đoạn trong BBNT đều khớp ngưỡng theo chiều dài đo.
6. Đoạn 35 (HNB048→NBE22) dài 17,69 km, đoạn 33 dài 16,34 km: đây là các đoạn đóng vòng dài nhất, quyết định suy hao ring khi đứt/đảo hướng.
7. Số liệu độ dài cáp theo mét (file chiều dài) khác BBNT (vd HNB066–HNB016: Sheet1 ghi 500 m, BBNT 0,456 km HĐ / 0,501 km đo; HNB038–HNB016 ghi 600 m vs 0,517/0,618 km). Chưa rõ nguồn nào là chuẩn.
8. ODF AGG ghi nhiều giá trị OTDR theo ngày (10–11/2020) lệch nhau, một số ô ghi "hư"/"Hư" ở ODF-01 bên Nguyễn Bình: cần xác nhận cổng hỏng còn dùng được không (chưa đối chiếu từng cổng).
9. ODF CSG: nhiều chỗ ghi "To HNB027" ở cả HNB031 và HNB020 (copy-paste), HNB014/054/006/091/048/060/059 chưa ghi đầu cáp.
10. Tên MX trùng/nhầm: `MX_NVT_03A` xuất hiện 2 lần cùng toạ độ (nghi một cái là 03B); `MX_HTP-03B` lặp ở nhiều vị trí trong sơ đồ; một số sơ đồ ghi "chỉ số" trống.

## 3. Mô hình dữ liệu đề xuất (một file `model.py`, mọi thứ đọc từ đây)
- **Node**: id (AGG-HCMNBE12, CSG-HNB066...), loại (AGG/CSG/MX), toạ độ, địa chỉ.
- **Cable**: id, mã cáp (Postef 2019, Focal 2020...), số sợi, kiểu (treo/tròn/ngầm), năm. *Tách "cáp vật lý" khỏi "đoạn dịch vụ"*: một đoạn BBNT thường đi qua nhiều cáp nối bằng MX (ví dụ "MX thẳng"). Độ dài từng cáp lấy từ file chiều dài, tổng cộng so với OTDR.
- **Closure (MX)**: id (MX_LVL-01...), vị trí, toạ độ, danh sách cáp vào/ra, bản đồ hàn: (cáp A, sợi, ống/màu) ↔ (cáp B, sợi), ghi chú "thẳng" hay "phối" (rẽ ra CSG).
- **Segment (đơn vị dịch vụ)**: ring, điểm đầu, điểm cuối, 2 sợi (core #1/#2), chuỗi cáp+MX đi qua, km HĐ, km OTDR, dB đo.
- **ODF port**: node, ODF-xx, cổng, sợi cáp, ghi chú, trạng thái (dùng/trống/hư/khách hàng khác như TTC, Vinanet).
- **Ring**: thứ tự node, hướng, đầu AGG, nhánh rẽ.
- **Circuit**: các dịch vụ thuê ngoài (DWDM Vinanet, TTC Long An...) đi qua sợi dự phòng, để tránh đụng sợi ring.

## 4. Đề xuất điều chỉnh so với cách ghi thủ công hiện tại
1. **Một khoá duy nhất cho mọi thứ**: chuẩn hoá tên (`CSG-HNB066`, `MX-LVL-01`, `ODF-HNB066-01`, `CAB-…`). Hiện cùng một MX có 3 tên (MX_HTP-03, MX_HTP-03A/B, "MX nhập đài").
2. **Tách sợi theo cặp**: mỗi đoạn ring = 2 sợi cố định (ví dụ F1–F2); sợi còn lại là dự phòng/khách hàng khác. Trong sơ đồ MX hiện chỉ gán nhãn A–E, cần chuyển sang bảng hàn có cấu trúc.
3. **Thay "cs" (chỉ số mét đầu cáp) thành bảng chỉ số 2 đầu của từng cáp**, để đổi OTDR ↔ vị trí thực địa ra đúng đoạn và MX gần nhất. Cần cho cả hai đầu, hiện nhiều ô trống.
4. **Tính độ dài quang từ cáp + slack**: đo OTDR − tổng cáp vật lý = slack ước tính tại từng MX; đưa vào ngưỡng cảnh báo (>25%).
5. **Quỹ suy hao tự tính**: 0,35 dB/km (1310) hoặc 0,25 dB/km (1550), 0,1 dB/mối hàn, 0,5 dB/đầu nối + margin 3 dB; cảnh báo khi đo > tính hoặc lệch core#1/#2 > 0,5 dB. (Tham số này là giả định, cần bạn xác nhận.)
6. **Giả lập đứt cáp theo ring**: đứt đoạn k → xác định CSG nào còn link về AGG nào; suy hao luôn tính theo từng đoạn giữa hai trạm liền kề (mỗi trạm có SFP riêng), không cộng dồn (xem mục 9).
7. **Cảnh báo kiểu dữ liệu**: trạng thái cổng ODF dùng danh sách chọn (dùng/trống/hư/mượn), không ghi chữ tự do.

## 5. Cần bạn xác nhận
- Ring có thực sự là vòng kép NBE12↔NBE22 (như suy ra) và R3/R5 có nhánh rẽ như trên?
- Nguồn chuẩn khi sai lệch: BBNT (đo), file chiều dài, hay ODF? Đề xuất: BBNT cho chiều dài đoạn, file chiều dài cho từng cáp, ODF cho cổng.
- Bảo vệ ring dùng giao thức gì (ERPS/MPLS)? Các cặp sợi ring là 2FO/đoạn đúng không?
- Tham số quỹ suy hao (dB/km, mối hàn, đầu nối) và quy ước màu sợi/ống (A–E trong sơ đồ MX nghĩa là gì: ring hay nhóm dịch vụ?).

## 6. Quy ước đã chốt (từ người dùng)
- Có đúng **8 ring**. Ring = các sợi cáp vật lý. Bảo vệ **1+1**: mỗi CSG nhận tín hiệu từ 2 trạm cấp 1 qua **2 cặp 2FO** (hai hướng).
- Ràng buộc vật lý: hai cặp FO của cùng một CSG **không đi chung sợi/cáp, chung lề, chung đường** (path diversity). Mô hình cần kiểm tra ràng buộc này.
- Nhãn trong sơ đồ MX: **cùng nhãn = cùng nhóm hàn với nhau**.
  - Nhãn A xuất hiện 8 sợi ở mỗi đầu cáp: hàn theo thứ tự, A1↔A1, A2↔A2...
  - Cùng nhãn ở hai đầu cáp khác số sợi (vd 12FO có 2 sợi B, 6FO có 2 sợi B): sợi B nhỏ hàn sợi B nhỏ theo thứ tự tăng dần.
  - Số sợi cùng nhãn hai đầu khác nhau → cảnh báo.

## 7. Quy ước suy hao đã chốt (từ người dùng)
- Ngưỡng theo chiều dài tuyến, ứng với SFP 10/40/80 km của MobiFone: **< 10 km: 12,1 dB; 10–40 km: 17 dB; > 40 km: 27 dB.**
- Lệch suy hao giữa hai core chấp nhận **≤ 2 dB**.
- Kết quả kiểm tra BBNT theo quy ước: cả 37 đoạn khớp ngưỡng; chỉ **đoạn 31 (HNB054→HNB006)** có lệch core 2,02 dB (vượt nhẹ 2 dB).
- Suy hao tính **theo từng đoạn giữa hai trạm liền kề** (CSG–CSG hoặc CSG–AGG), không cộng dồn cả ring, vì mỗi trạm có SFP thu/phát riêng về hai hướng (xem mục 9).
- Ví dụ "khác lề": `MX_NVT_03A` và `MX_NVT_03B` là hai măng xông ở hai bên lề đường (file ghi nhầm trùng tên); đấu hai hướng cần tách như vậy.
- Một số CSG là trạm cấp 3 (last-mile), **chỉ có một hướng đến**, triển khai cùng đợt, không bảo vệ 1+1.
- Ghi chú DWDM, VNN, TTC trong ODF/MX là **quỹ core trống cho đối tác** dùng trên một đoạn nào đó; mô hình gắn "đối tác" vào sợi và đoạn.

## 8. Đối chiếu với KML `Nha_Be.kml` (vị trí & khoảng cách)
Tệp: `data/segments_geo.csv` (chiều dài từng đoạn theo KML), `data/ban_do_8_ring.svg|png` (bản đồ 8 ring).

**KML chứa**: thư mục `Lastmile Nha Be` (32 điểm: 2 AGG + 30 CSG; 17 điểm MX; 8 thư mục tuyến = 8 ring, 38 đoạn gồm cả nhánh HNB018 và HNB113) và một nhóm khác `34 LINK MBF` (AGG-HCMNBE11/NBE21, 33 trạm CSG khác, 34 link) cùng các điểm lẻ (HNB072, HNB134, NB Kim Long, Riverside).
Đánh số Folder 1–8 trùng đúng R1–R8 đã suy ra, khớp nhãn "ring n" trong ODF AGG.

**Chiều dài**: nhìn chung OTDR ≈ 1,07–1,10 × chiều dài vẽ trên KML (slack hợp lý). Các đoạn lệch:
| Đoạn | HĐ | OTDR | KML | Nhận xét |
|---|---|---|---|---|
| 1 NBE12→066 | 10,24 | 15,40 | 14,35 | số HĐ sai (KML & OTDR cùng ~14–15 km) |
| 5 NBE12→005 | 10,86 | 11,10 | 15,05 | KML dài hơn OTDR 4 km: nghi vẽ sai tuyến |
| 3 016→038 | 0,52 | 0,62 | 0,27 | OTDR gấp 2,3× KML: dư cáp lớn hoặc vẽ sai |
| 18 014→075, 32 006→091 | 0,52 / 0,96 | 0,86 / 1,61 | 0,41 / 0,78 | OTDR ≈ 2× KML |
| 22 056→071 | 0,83 | 1,33 | 1,28 | số HĐ sai |
| 2 066→016 | 0,46 | 0,50 | 0,69 | OTDR ngắn hơn KML: vẽ chưa chuẩn |
Giá trị HĐ **0,827 km lặp 5 lần** (đoạn 7, 8, 12, 22, 26) và 1,086 lặp 2 lần: nhiều khả năng là số điền mẫu, không phải số đo.
Toạ độ AGG-NBE22 trong BBNT (10,69881) lệch KML (10,685521): BBNT chép nhầm vĩ độ của HNB038.

**Kiểm tra "không cùng đường" (so sánh hình học KML, dung sai 20 m)**: tuyến vẽ tay nên chỉ là cảnh báo cần xác nhận thực địa.
- Cáp NBE12→HNB059 (R1) trùng ~0,65–0,95 km với đoạn HNB060→048 và HNB048→NBE22 của cùng ring.
- R1 (048→NBE22) và R2 (091→NBE22) **chạy chung ~14 km** về NBE22; cả hai đều chung hành lang với tuyến NBE12→054/059 phía nam.
- Các ring phía bắc (R3, R4, R5, R7, R8): các đoạn từ NBE12 và về NBE22 chung hành lang 5–13 km (đường Long Thới ↔ Lê Văn Lương).
(Đã điều chỉnh nhận định sau khi bạn giải thích: các ring dùng chung cáp là được phép; xem mục 9.)

## 9. Quy tắc bảo vệ đã chốt & phân tích đứt một đoạn
**Quy ước**
- Bảo vệ tính **trong phạm vi từng ring, từ AGG đến AGG**. Các ring **được phép đi chung cáp/hành lang** với nhau: một sự cố trên cáp chung chỉ làm mỗi ring mất một đoạn, các CSG vẫn còn tín hiệu từ một AGG.
- **Điều cần tránh**: một CSG không còn link nào về bất kỳ AGG. Chỉ xảy ra khi cùng một ring mất ≥ 2 đoạn trong một sự cố (hai hướng của ring chung cáp/hành lang với nhau), hoặc với trạm nhánh cụt (HNB018, HNB113: chỉ có một hướng).
- Nhóm kênh của **HNB066 và HNB005 đã chuyển sang đường khác thiết kế** nên chiều dài thực tăng. Đoạn 1 (NBE12→066) và đoạn 5 (NBE12→005) dùng chiều dài KML cộng slack (~8%) khi tính quỹ suy hao.
- **BBNT chỉ mang tính chất con số thống nhất**, không phải kết quả đo đáng tin tuyệt đối. Nguồn tham chiếu vật lý: KML + slack; BBNT dùng đối soát hợp đồng.

**Quỹ suy hao (người dùng đính chính)**: mỗi trạm có SFP thu/phát về hai hướng, nên quỹ suy hao tính riêng cho **từng đoạn giữa hai trạm liền kề**, không cộng dồn chiều dài ring. Khi một đoạn đứt, các đoạn còn lại giữ nguyên suy hao và ngưỡng (theo chiều dài từng đoạn). Do đó bảng "đường mới dài nhất khi đứt cáp" tôi đưa trước đó **không áp dụng và đã bỏ**. Đoạn dài nhất là #35 (HNB048→NBE22, 17,7 km đo; KML 16,1 km): nhóm 10–40 km, ngưỡng 17 dB, suy hao đo 8,1 dB.
Việc cần kiểm tra khi giả lập đứt: (1) mỗi CSG còn ít nhất một link về một AGG; (2) trạm nhánh cụt mất kết nối; (3) từng đoạn so với ngưỡng theo chiều dài của chính nó.

## 10. Đường đi theo lề đường (người dùng bổ sung, thay thế bản ghi trước)
Cách hiểu đúng: "1 sợi cáp" = **một cáp vật lý gồm nhiều core** (6–24 core trong dự án này); mỗi link dùng **2 core**. "Hai lề" = **hai hướng của một ring đi hai phía lề đường khác nhau** (khác lề), chứ không phải tách hai core của một đoạn.
- **R2 (054–006–091)**: AGG → MX1 → HNB054 → MX1 → MX2 → HNB006 → MX2 → **lề trái** → MX_NVT_03A → HNB091 → MX_NVT_03B → **lề phải** → MX → cáp về AGG.
- **R1 (059–060–048)**: AGG → **lề trái** → MX_NVT_03A → lề trái → HNB059 → lề trái → HNB060 → **lề phải** → HNB048 → lề phải → MX_NVT_03B → cáp về AGG.
- **R6**: HNB020→HNB031 cũng đi hai lề.
- `MX_NVT_03A`/`03B` là hai măng xông ở hai bên lề, qua đó cáp chuyển từ lề này sang lề kia (tên trùng trong file MX là do ghi nhầm).
- Hệ quả: đây chính là điều kiện vật lý "hai hướng không chung lề". Trong mô hình mỗi cáp có thuộc tính `lề` (trái/phải) và hai hướng của một CSG phải khác lề; đoạn đứt trên một lề chỉ ảnh hưởng hướng đi theo lề đó.
- Đã xác nhận: "nb51" là gõ nhầm của HNB054; MX1 = MX_NVT_01, MX2 = MX_NVT_02A/02B.
- **Cáp trục lề trái từ AGG (NBE12) đi qua MX_NVT_01 → MX_NVT_02A → MX_NVT_03A là một cáp dùng chung**: R2 dùng một số core của cáp này cho HNB054 và HNB006, R1 dùng core khác của cùng cáp để đi tới MX_NVT_03A rồi tiếp tục sang HNB059. Đây là trường hợp "các ring chạy chung cáp" được phép (mục 9): mỗi link dùng 2 core riêng, bảng hàn tại từng MX quyết định core nào rẽ vào CSG, core nào đi thẳng.

## 11. Bảng phối core tại măng xông (trọng tâm)
Nguồn: sheet `MX` của file MX__NHA_BE.xlsx, đọc bằng `parse_mx.py` (kết quả trong `data/mx_cap.csv`, `mx_core.csv`, `mx_ghi_chu.csv`).
- Cách đọc sơ đồ: mỗi cáp là hàng/cột số core; chữ ngay sát = nhãn nhóm hàn; **cùng nhãn hàn với nhau, core nhỏ hàn core nhỏ**; tên trạm (HNBxxx) ghi sát nhãn = trạm có link đi qua nhóm core đó; ô màu = màu sợi.
- Kết quả: 21 măng xông trong sơ đồ, 70 đầu cáp, 794 core, **176 cặp hàn** suy ra; số core mỗi nhãn ở các đầu cáp khớp nhau ở hầu hết măng xông (kiểm tra tự động, các chỗ lệch nằm ở `Cảnh báo phối core`).
- Chưa có nhãn (người dùng chưa ghi): MX_NVT_01, MX_NB-02/03/04, MX_HTP-03B, MX_DST (một phần), NVT_03A/03B (tiêu đề copy mẫu "Hướng vào trạm HNB006").
- Màu sợi/ống: giả định 6 sợi mỗi ống (xanh dương, cam, xanh lá, nâu, xám, trắng), khớp ô màu trong sơ đồ; chưa kiểm tra với cáp 24FO.
- Chưa làm: lần theo từng link ring từ CSG này qua các măng xông đến CSG kia (cần nối đầu cáp giữa các măng xông).

## 12. Lần đường đi một link (thử với R2 = 054–006–091)
Mô tả của người dùng được mã hoá ở `data/paths/R2.json`; `model.load_paths` tính tổng độ dài cáp và đối chiếu từng mối hàn với bảng phối core suy ra từ sơ đồ MX (sheet `Đường đi link`).
- Cặp core của HNB054 trên ODF-02 (hướng NVT) tại NBE12 là 1-2, khớp ghi chú ODF AGG ("HNB054 ring 2", cổng 1-2).
- Tổng độ dài cáp cộng theo sổ cáp khớp OTDR: R2-01 980 m (ODF AGG ghi 982/988 m), R2-02 1430 m (BBNT 1433 m), R2-03 1610 m (BBNT 1607 m).
- Mối hàn khớp sơ đồ MX: NVT_02A 1,2↔1,2 (nhãn A); NVT_02B 1,2↔1,2 (nhãn A). Mối hàn NVT_02A 3,4↔5,2 cùng nhóm core (nhãn D) nhưng thứ tự khác quy tắc nhỏ-nhỏ (cần xác nhận thứ tự chéo).
- Chưa có nhãn trong sơ đồ: NVT_01, NVT_03A, NVT_03B, MX nhập đài Long Thới–NVT.
- Link R2-04 (HNB091 → NBE22) mới mô tả đến NVT_02B; chờ phần còn lại.

## 13. Hoàn chỉnh link HNB091 → NBE22 và quỹ core
- Core hư thay thế: tại NVT_02A thiết kế ban đầu 3↔1, 4↔2 (nhãn D); core 1 hư (sơ đồ ghi "HƯ") nên thực tế 3↔5, 4↔2. Quy tắc nhỏ-nhỏ vẫn đúng; mô hình ghi riêng "thiết kế" và "phát sinh" (`subst` trong `data/paths/R2.json`).
- Link R2-04 (HNB091 → NBE22) đã đi đến ODF-02 NBE22: tổng cáp 16 023 m so với OTDR ghi trên ODF AGG 16 028 m (lệch 5 m). Nhãn khớp sơ đồ MX tại NVT_02B (A), LVL-05 (1,2↔19,20, nhãn D), NB-01 (19,20↔1,2, nhãn B). Các MX còn lại (NVT_03B, NB-02/03/04, HTP-03B) chưa có nhãn nên mối hàn được dựng từ mô tả.
- `data/cables.json`: 17 cáp vật lý (đã dùng trong R2) kèm chiều dài và đầu cáp tương ứng trong sơ đồ MX. MX thẳng giữa NB-04 và HTP-03B là giả định theo sổ cáp (777 + 640 m).
- Quỹ core (`model.core_ledger`): mỗi core ở trạng thái dùng cho link nào / hư / có nhãn chưa gán link / trống. Gợi ý loại trừ: HNB048 dùng cùng tuyến với HNB091 ở core kế tiếp (trục NVT_02B→LVL-05 core 3,4; cáp 24FO TPKL core 21,22).

## 14. Ring R1 và hồ sơ cáp phục vụ xử lý sự cố
- R1 (059–060–048) đã lần đủ 4 link: đoạn dùng chung dùng cặp 3,4; cáp 6FO chạy riêng dùng 1,2. Tổng cáp khớp OTDR: R1-01 4668/4672 m, R1-02 3086/3082, R1-03 4405/4410, R1-04 17 153/17 153 m (ODF AGG).
- MX thẳng HTP xác nhận: hết đoạn 600 m từ SG mới trên đường HTP (10.680424, 106.748376).
- Mỗi cáp vật lý có mã nội bộ (C01…C21), mã cáp theo sổ (`ma_cap`), chỉ số mét hai đầu, dòng sổ cáp; `model.cable_profiles` liệt kê core đang chạy / hư / có nhãn chưa gán / trống và hệ quả khi đứt (sheet `Hồ sơ cáp`, `Tra cứu cáp`; tab "Cáp" trong HTML).
- Cáp chưa có mã trong sổ (cần bổ sung): C05, C06, C09, C12–C16.
- Quan sát: cáp vào trạm C03 (HNB054) và C05 (HNB006) mang cả hai cặp link của trạm đó (1,2 và 3,4) nên một lần đứt cô lập trạm; các cáp trục chung (C01, C02, C09–C17) mang đồng thời link R1 và R2 (mỗi ring chỉ mất một hướng).

## 15. Quy tắc cáp vào trạm và cân đối cáp
- Cáp vào trạm từ MX trục gần trạm (< 300 m) được chấp nhận với điều kiện ≥ 12FO (cấu hình `drop_max_m`, `drop_min_fo`). Cáp dùng chung mang nhiều link được phép, chấp nhận sự cố nhiều tuyến cùng lúc, nhưng cần cân đối giữa các cáp.
- Sheet `Cân đối cáp`: loại cáp (vào trạm / trục / riêng tới trạm / giữa hai trạm), số link và số ring mỗi cáp, tỷ lệ core dùng, kiểm tra quy tắc. Hiện C03, C05, C17 đạt; 8 cáp trục dùng chung (C01, C02, C04, C06, C09–C16) đều mang R1+R2 (2 link mỗi cáp).
- Mã cáp lấy từ sổ độ dài; cáp chưa có mã trong sổ (C05, C06, C09, C12–C16 ↔ dòng 55, 57, 64, 18–22) được để trống, không điền suy đoán.
