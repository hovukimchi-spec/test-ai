"""Danh mục sự cố tuyến quang: từ dây nhảy PON (OLT) tới đầu fast connector cắm modem căn hộ.
Phạm vi (scope) khớp loại phần tử chọn trong app: pon / spl / cab / tr / apt."""

INCIDENTS = [
 # ---------------- PON ----------------
 dict(id='P1', scope='pon', seg='OLT: cổng PON và module quang SFP', title='Cổng PON / SFP trên OLT hỏng hoặc phát yếu',
  symptoms='Toàn bộ ONU của PON mất tín hiệu (LOS) cùng một lúc; OLT báo PON port down hoặc Tx power thấp; các PON khác bình thường.',
  check='Xem trạng thái và DDM của SFP trên OLT (Tx power, nhiệt độ, dòng bias). Đo công suất phát bằng OPM tại đầu dây nhảy, so với số đo lúc nghiệm thu.',
  temp='Thay SFP dự phòng đúng chuẩn (GPON/XGS-PON, class B+/C+). Nếu cổng PON hỏng: dời dây nhảy sang cổng PON trống của OLT, cấu hình lại profile và ghi lại PON mới.',
  fix='Thay SFP hoặc card PON (bảo hành/RMA). Cập nhật bảng đấu nối PON ↔ cổng vào ODF-96.',
  prevent='Dự trữ ít nhất 2 SFP mỗi loại. Ghi Tx power chuẩn khi nghiệm thu, đặt ngưỡng cảnh báo DDM.', prio='P1', eta='15-30 phút'),
 dict(id='P2', scope='pon', seg='Dây nhảy PON: OLT → ODF-96 (cổng vào)', title='Dây nhảy OLT → ODF-96 hoặc adapter cổng vào bị bẩn, gập, hỏng',
  symptoms='Toàn bộ ONU của PON mất hoặc chập chờn; Tx power OLT bình thường nhưng công suất tại cổng vào ODF-96 thấp hoặc không có; thường xảy ra sau thao tác tại rack (rút nhầm, uốn gập).',
  check='Đo OPM tại đầu dây nhảy phía ODF-96. Vệ sinh đầu SC/APC bằng bút vệ sinh, soi end-face bằng kính hiển vi. Kiểm tra bán kính uốn; dùng VFL xem rò sáng.',
  temp='Thay ngay dây nhảy SC/APC dự phòng (đầu xanh lá, không dùng UPC). Vệ sinh adapter.',
  fix='Thay adapter ODF-96 nếu hỏng; chỉnh lại đường đi dây, giữ bán kính uốn ≥ 30 mm; dán nhãn hai đầu.',
  prevent='Nhãn hai đầu (PON-k ↔ A/B-số cổng), khay quản lý cáp, chỉ dùng APC với APC.', prio='P1', eta='10-20 phút'),
 dict(id='P3', scope='pon', seg='Splitter 1:4 tại phòng máy', title='Splitter 1:4 hỏng hoặc suy hao tăng',
  symptoms='Toàn bộ ONU của PON mất, hoặc Rx của mọi ONU thuộc PON giảm bất thường (hơn 3 dB so với chuẩn); OLT và dây nhảy bình thường.',
  check='Đo công suất tại cổng vào splitter và từng cổng ra; chênh lệch kỳ vọng khoảng 7,3 dB. Có ánh sáng vào mà ra không có hoặc yếu bất thường thì nghi splitter.',
  temp='Thay splitter 1:4 dự phòng, cắm lại đúng 4 cổng ra theo bảng cổng.',
  fix='Thay hẳn, đo Rx một số ONU mẫu, cập nhật số seri và ngày thay.',
  prevent='Dự trữ 1-2 splitter 1:4. Lưu số đo chuẩn (công suất vào/ra) lúc nghiệm thu.', prio='P1', eta='20-40 phút'),
 # ---------------- SPL (1 splitter 1:16 / 1 nhánh) ----------------
 dict(id='S4', scope='spl', seg='Dây nhảy ODF-96 (cổng ra) → ODF-48', title='Dây nhảy hoặc adapter giữa ODF-96 và ODF-48 hỏng',
  symptoms='Cả nhóm ONU thuộc cùng một splitter 1:16 (cùng tủ, cùng tầng) mất đồng loạt; các nhánh khác của PON vẫn bình thường.',
  check='Tra mã splitter trong app/Excel để biết cổng ODF-96 và coupler ODF-48. Đo OPM hai đầu dây nhảy; vệ sinh và soi end-face.',
  temp='Thay dây nhảy dự phòng. Hoặc chuyển nhánh sang cổng ra thứ 4 (dự phòng) của cùng splitter 1:4 nếu PON còn cổng đó, để loại trừ cổng hỏng.',
  fix='Thay adapter/dây nhảy, cập nhật bảng dây nhảy.',
  prevent='Nhãn hai đầu từng dây nhảy; không cắm rút các dây khác khi chưa cần.', prio='P2', eta='10-20 phút'),
 dict(id='S5', scope='spl', seg='Cáp trục: 1 sợi (coupler ODF-48 → đầu vào splitter tại tủ)', title='Một sợi trục bị gãy, mối hàn hoặc pigtail hỏng',
  symptoms='Cả nhóm ONU của một splitter 1:16 mất; các splitter khác trên cùng cáp trục vẫn bình thường (khác với đứt cả cáp).',
  check='OTDR từ ODF-48 đo đúng sợi đó (dùng dây phóng đủ dài) để xác định khoảng cách. Dùng VFL tại tủ và đo OPM tại đầu vào splitter tủ.',
  temp='Chuyển sang sợi dự phòng trong dải 8FO của cùng tủ: đổi coupler ở ODF-48 và cổng vào splitter ở tủ; ghi lại số sợi mới.',
  fix='Hàn lại mối hàn hoặc thay pigtail; sửa xong có thể trả về sợi cũ. Cập nhật bảng sợi trục.',
  prevent='Giữ sợi dự phòng không dùng; lưu OTDR chuẩn từng sợi lúc nghiệm thu.', prio='P2', eta='30-90 phút'),
 dict(id='S9', scope='spl', seg='Tủ: splitter 1:16', title='Splitter 1:16 hỏng, đầu vào bẩn hoặc cổng ra hỏng',
  symptoms='ONU của một splitter mất toàn bộ (hoặc vài cổng cùng chết nếu hỏng một phần); Rx các ONU còn lại thấp bất thường.',
  check='Đo OPM đầu vào splitter (kỳ vọng khoảng -5 đến -8 dBm theo tính toán) và từng cổng ra (chênh khoảng 13,8 dB). Vệ sinh adapter đầu vào.',
  temp='Thay bằng splitter dự phòng mang theo. Nếu chỉ một cổng ra hỏng: chuyển căn hộ đó sang cổng trống cùng splitter và ghi lại cổng mới.',
  fix='Thay splitter, ghi seri và ngày; đo lại Rx ONU mẫu.',
  prevent='Đậy nắp bụi mọi cổng chưa dùng; tủ có khóa và niêm phong.', prio='P2', eta='20-45 phút'),
 # ---------------- CAB (cả tủ) ----------------
 dict(id='C7', scope='cab', seg='Cáp nhánh 8FO: tủ → tủ hub (hộp nối tại hub)', title='Đứt cáp nhánh 8FO hoặc hỏng mối hàn tại hub',
  symptoms='Toàn bộ căn hộ của một tủ (14-48 hộ, 1-5 splitter) mất; các tủ khác cùng cáp trục bình thường; nhiều PON mất một phần.',
  check='OTDR từ ODF-48 trên từng sợi của tủ đó để biết khoảng cách điểm đứt; mở hộp nối tại hub kiểm tra mối hàn.',
  temp='Không có đường dự phòng vật lý. Nếu hỏng mối hàn: hàn lại ngay. Nếu cự ly ngắn: kéo cáp tạm nối trực tiếp.',
  fix='Hàn nối hoặc thay đoạn cáp 8FO, đo OTDR nghiệm thu, cập nhật hồ sơ.',
  prevent='Cáp đi trong ống/thang cáp, hộp nối có khóa; lưu OTDR chuẩn.', prio='P1', eta='1-3 giờ'),
 dict(id='C8', scope='cab', seg='Tủ phối quang (vật lý)', title='Tủ bị phá hoại, vào nước hoặc cháy',
  symptoms='Mất toàn bộ căn hộ của tủ kèm dấu hiệu hư hại vật lý (cửa mở, nước, mùi cháy).',
  check='Chụp ảnh hiện trường; kiểm tra từng splitter, adapter, pigtail; đo OPM trên cáp trục tại tủ.',
  temp='Dựng tạm bằng splitter mang theo, cắm lại các cáp 1FO theo bảng cổng (cáp 1FO đặt cố định nên chỉ cần cắm đúng cổng đã quy hoạch).',
  fix='Thay tủ/splitter, hàn lại pigtail, khóa và niêm phong, cập nhật seri.',
  prevent='Khóa tủ, niêm phong, kiểm tra định kỳ; giữ kỹ thuật viên có bảng cổng bản in và bản điện tử.', prio='P1', eta='2-4 giờ'),
 # ---------------- TR (cả cáp trục) ----------------
 dict(id='T6', scope='tr', seg='Cáp trục 24FO (ODF-48 → tủ)', title='Đứt cáp trục 24FO',
  symptoms='Mất đồng loạt nhiều tủ trên cùng một cáp trục (khoảng 90-131 hộ); nhiều PON mất các nhánh đi trên trục đó; OLT báo ONU LOS theo từng nhóm splitter.',
  check='OTDR 1-2 sợi trục từ ODF-48 xác định khoảng cách tới điểm đứt, đối chiếu với chiều dài tuyến; kiểm tra khu vực có thi công, khoan, cháy; hộp nối tại hub.',
  temp='Không có tuyến dự phòng. Hàn nối nhanh bằng măng-xông hoặc hộp nối tạm tại điểm đứt; ưu tiên sợi của cụm tầng đông hộ. Nếu hư dài: kéo cáp tạm theo tuyến khác.',
  fix='Thay đoạn cáp, hàn đủ 24 sợi, đo OTDR nghiệm thu và cập nhật hồ sơ.',
  prevent='Đi cáp trong ống/thang cáp kín; khóa hộp kỹ thuật; lưu OTDR chuẩn từng sợi để so sánh.', prio='P1', eta='2-6 giờ'),
 # ---------------- APT (1 căn hộ) ----------------
 dict(id='H11', scope='apt', seg='Cáp 1FO: tủ → hộp BOX căn hộ', title='Cáp 1FO bị đứt hoặc gập (đặt cố định trong ống)',
  symptoms='Một ONU mất tín hiệu hoặc Rx rất thấp; các ONU cùng splitter bình thường.',
  check='Đo OPM tại cổng splitter ở tủ (có ánh sáng) và tại hộp BOX căn hộ. Dùng VFL từ tủ tìm điểm rò sáng; OTDR có dây phóng cho đoạn ngắn.',
  temp='Cáp đặt cố định nên không có đường khác. Chuyển sang cổng trống chỉ giải quyết lỗi cổng splitter, không giải quyết đứt cáp.',
  fix='Hàn nối cáp 1FO (mối hàn nóng chảy + ống co) tại điểm đứt hoặc kéo thay cáp trong ống nếu còn chỗ.',
  prevent='Dán nhãn hai đầu; bán kính uốn tại hộp BOX; không bó cáp quá chặt.', prio='P3', eta='1-2 giờ'),
 dict(id='H12', scope='apt', seg='Hộp BOX → fast connector → modem', title='Đầu fast connector hoặc ổ BOX tại căn hộ hỏng',
  symptoms='Modem báo LOS hoặc Rx dưới -27 dBm nhưng cáp 1FO tốt; thường xảy ra sau lắp đặt hoặc di dời modem.',
  check='Đo OPM tại fast connector; soi và vệ sinh đầu; thử dây nhảy từ BOX tới modem.',
  temp='Cắm dây nhảy SC/APC dự phòng thẳng từ BOX vào modem; vệ sinh đầu cắm.',
  fix='Cắt và đấu lại fast connector (SC/APC), kiểm tra suy hao đầu cắm ≤ 0,5 dB; thay ổ BOX nếu nứt.',
  prevent='Dùng fast connector chất lượng; đo Rx sau khi lắp; đậy nắp bụi; dặn khách không bẻ gập dây.', prio='P3', eta='20-40 phút'),
 dict(id='H13', scope='apt', seg='Tủ: cổng splitter của căn hộ (cắm nhầm hoặc nhãn sai)', title='Cắm nhầm cổng hoặc dán nhãn sai tại tủ',
  symptoms='Một căn hộ mất hoặc OLT hiện ONU ở sai splitter so với bảng; thường xảy ra sau thao tác tại tủ.',
  check='Đối chiếu nhãn cáp 1FO hai đầu với bảng cổng. Cắm VFL tại hộp BOX căn hộ rồi xem sợi nào sáng trong tủ.',
  temp='Cắm lại đúng cổng theo bảng.',
  fix='Dán lại nhãn hai đầu, ghi lại cổng thực tế vào bảng (nếu phải đổi cổng, ghi vào nhật ký).',
  prevent='Quy hoạch cổng cố định cho từng căn hộ và in bảng cổng dán trong cửa tủ.', prio='P3', eta='10-20 phút'),
 dict(id='H14', scope='apt', seg='Toàn tuyến 1 căn hộ: đầu nối bẩn hoặc uốn gấp', title='Suy hao cao, chưa mất hẳn (đầu nối bẩn, uốn gấp)',
  symptoms='ONU chập chờn, Rx khoảng -26 đến -30 dBm, lỗi FEC/BIP tăng; có lúc tự phục hồi.',
  check='Đo OPM ở các điểm: fast connector, hộp BOX, cổng splitter ở tủ để tìm đoạn mất nhiều nhất. Soi end-face từng đầu nối.',
  temp='Vệ sinh toàn bộ đầu nối trong tuyến; nắn lại cáp chỗ uốn gấp.',
  fix='Thay đầu nối hoặc đoạn cáp hỏng; đo lại đạt Rx trong khoảng -8 đến -25 dBm.',
  prevent='Vệ sinh đầu nối mỗi lần cắm rút; đo và lưu Rx chuẩn lúc lắp.', prio='P4', eta='20-60 phút'),
]

SCOPE_LABEL = {'pon': 'Cả 1 PON', 'spl': 'Một splitter 1:16 (một tầng)', 'cab': 'Cả 1 tủ', 'tr': 'Cả 1 cáp trục 24FO', 'apt': 'Một căn hộ'}

DECISION = [
 ('Chỉ 1 ONU mất / yếu, các ONU cùng splitter bình thường', 'Cáp 1FO, fast connector, cổng splitter của căn hộ đó', 'H11, H12, H13, H14', 'Đo OPM tại fast connector, rồi tại cổng splitter ở tủ.'),
 ('Cả nhóm ≤ 16 ONU cùng 1 splitter 1:16 (cùng tầng) mất', 'Dây nhảy ODF-96 → ODF-48, sợi trục, splitter 1:16', 'S4, S5, S9', 'Đo tại cổng ra ODF-96; nếu có ánh sáng thì đo tiếp tại đầu vào splitter ở tủ.'),
 ('Cả 1 tủ (14-48 hộ) mất, các tủ khác bình thường', 'Cáp nhánh 8FO, hộp nối hub, bản thân tủ', 'C7, C8', 'OTDR các sợi của tủ từ ODF-48; xem hiện trường tủ.'),
 ('Nhiều tủ cùng 1 cáp trục (khoảng 90-131 hộ) mất', 'Cáp trục 24FO', 'T6', 'OTDR 1-2 sợi trục từ ODF-48, tìm điểm đứt.'),
 ('Cả 1 PON mất (≤ 56 hộ, nhiều tủ cùng PON)', 'SFP/cổng PON OLT, dây nhảy OLT → ODF-96, splitter 1:4', 'P1, P2, P3', 'Xem DDM của SFP, rồi đo tại cổng vào ODF-96, rồi tại 4 cổng ra splitter 1:4.'),
 ('Cả PON mất nhưng SFP, dây nhảy và splitter 1:4 đều tốt', 'ONU phát liên tục làm nghẽn PON (rogue ONU, nằm ngoài phạm vi tuyến quang nhưng triệu chứng giống mất PON)', 'Cô lập', 'Rút lần lượt từng dây nhảy cổng ra ODF-96; nhánh nào làm PON phục hồi thì tìm tiếp trong splitter đó.'),
 ('Nhiều PON mất cùng lúc', 'Card OLT, nguồn, uplink (ngoài phạm vi tuyến quang)', 'Ngoài phạm vi', 'Kiểm tra thiết bị OLT trước khi đi đo cáp.'),
 ('Nhiều ONU Rx thấp đồng loạt nhưng chưa mất', 'Đầu nối bẩn ở phòng máy, tăng suy hao ở tuyến chung', 'P2, P3, S4', 'Vệ sinh và đo từng đầu nối từ OLT xuống ODF-48.'),
]

TOOLS = ['Máy đo công suất quang (OPM) dải 1310/1490/1550 nm', 'Bút đo/VFL (đèn đỏ tìm điểm rò sáng)', 'OTDR kèm dây phóng 150-500 m, hai bước sóng 1310/1550 nm',
         'Kính soi đầu nối và bút/gạc vệ sinh SC/APC', 'Máy hàn nóng chảy, ống co, dao cắt sợi chuẩn xác, hộp/măng-xông nối',
         'Dự trữ: SFP (≥2 mỗi loại), splitter 1:4 (1-2), splitter 1:16 (2), dây nhảy SC/APC các độ dài, adapter, fast connector, pigtail, nhãn']

REFERENCE = [
 ('Công suất phát OLT (class B+)', '+1,5 đến +5 dBm'),
 ('Công suất thu ONU hợp lệ', '-8 đến -27 dBm (class B+; quá -8 là quá tải, dưới -27 là mất ổn định)'),
 ('Mức cảnh báo vàng / đỏ (đề xuất)', 'Vàng ≤ -25 dBm; Đỏ ≤ -27 dBm hoặc LOS'),
 ('Công suất tại đầu vào splitter 1:16 ở tủ (tính toán)', 'khoảng -5 đến -8 dBm'),
 ('Công suất thu ONU (tính toán, đường xấu nhất)', 'khoảng -19 đến -23 dBm'),
 ('Chênh lệch splitter 1:4 / 1:16 (điển hình)', '7,3 dB / 13,8 dB'),
 ('Suy hao mỗi đầu nối APC tốt', '≤ 0,3-0,5 dB'),
 ('Lưu ý', 'Các số tính toán chỉ để so sánh; luôn ghi số đo thực tế của từng ONU và từng sợi lúc nghiệm thu làm chuẩn.'),
]

PLANNING = [
 'KHUYẾN NGHỊ: QUY HOẠCH CỐ ĐỊNH CỔNG CHO TỪNG CĂN HỘ, đấu sẵn tất cả cáp 1FO vào đúng cổng ngay khi nghiệm thu. Khi khách đăng ký chỉ cần đăng ký ONU trên OLT, không phải ra tủ cắm lần lượt.',
 'Lý do 1: cáp 1FO từ tủ tới từng căn hộ đã đặt cố định, nên mỗi căn hộ đã gắn với một đầu cáp; quy hoạch cổng chỉ là chọn cổng cho đầu cáp đó và không phụ thuộc thứ tự khách đăng ký.',
 'Lý do 2: tra cứu và xử lý sự cố chắc chắn: từ mã căn hộ biết ngay tủ, splitter, cổng, PON (đúng bảng trong Excel/app); khi mất nhóm ONU trên OLT biết ngay nhóm đó là splitter nào, tầng nào.',
 'Lý do 3: đo công suất (Rx) và OTDR chuẩn cho toàn bộ căn hộ ngay một lần khi nghiệm thu, thay vì đo rời rạc từng lần kích hoạt; sau này chỉ cần so sánh với số chuẩn.',
 'Lý do 4: tránh sai sót do cắm lần lượt: người cắm sau không biết cổng nào dành cho căn hộ nào, dễ cắm nhầm, nhãn lệch, bảng không còn khớp thực tế. Splitter thụ động nên đấu sẵn không tốn thêm công suất và không làm giảm tải PON.',
 'Quy ước cổng: mỗi splitter 1:16 chỉ phục vụ 1 tầng; cổng 1,2,3... tương ứng box 01,02,03... của tầng đó (tầng có hơn 16 box chia đều cho nhiều splitter, vd tầng 3 tháp A 20 box: S1 box 01-10, S2 box 11-20). Bảng này nằm ở sheet Thuê bao (cột Splitter 1:16 và Cổng splitter).',
 'Cổng dự phòng: mỗi splitter còn trống 0-6 cổng (tổng toàn hệ thống khoảng 124 cổng). Dùng để chuyển căn hộ khi một cổng splitter bị hỏng; khi chuyển phải cập nhật bảng và ghi nhật ký.',
 'Nhãn: dán nhãn hai đầu mỗi cáp 1FO (mã căn hộ, ví dụ A-18-05 và TU-A18/S2-p3); in bảng cổng dán mặt trong cửa tủ; ghi mã căn hộ vào mô tả ONU trên OLT để cảnh báo hiển thị đúng căn hộ.',
 'Khi nào không nên đấu sẵn: chỉ khi cần tiết kiệm đầu nối/adapter chưa mua hoặc tủ chưa đủ splitter. Khi đó vẫn giữ nguyên quy hoạch cổng, chỉ cắm dần theo đúng cổng đã định (không cắm theo thứ tự đăng ký).',
]

def stats(data):
    """Số hộ ảnh hưởng (min, trung bình, max) theo phạm vi, tính từ dữ liệu thiết kế."""
    import collections
    homes, spls = data['homes'], data['spls']
    def mm(vals):
        vals = list(vals); return (min(vals), round(sum(vals) / len(vals)), max(vals))
    c_pon = collections.Counter(h['pon'] for h in homes)
    c_cab = collections.Counter(h['cab'] for h in homes)
    c_tr = collections.Counter(h['trunk'] for h in homes)
    return {'apt': (1, 1, 1), 'spl': mm(s['n'] for s in spls), 'cab': mm(c_cab.values()), 'tr': mm(c_tr.values()), 'pon': mm(c_pon.values())}

def spare(data):
    cabs, spls, homes = data['cabinets'], data['spls'], data['homes']
    import model as M
    return {
        'Cổng ra 1:4 dự phòng trên ODF-96 (cổng thứ 4 của PON chưa dùng)': M.N_PON * M.SPL_PM - len(spls),
        'Cổng splitter 1:16 còn trống (dùng chuyển căn hộ khi hỏng cổng)': sum(M.SPL_CAB for _ in spls) - len(homes),
        'Sợi dự phòng trong dải 8FO của các tủ (đổi sợi khi sợi hỏng)': sum(M.FO_PER_CABINET - c['nspl'] for c in cabs),
        'Sợi trục chưa cấp cho tủ nào (cáp trục có ít hơn 3 tủ)': len(data['trunks']) * M.TRUNK_FO - len(cabs) * M.FO_PER_CABINET,
        'Vị trí splitter 1:16 trống trong tủ': sum(c['slots'] - c['nspl'] for c in cabs),
    }
