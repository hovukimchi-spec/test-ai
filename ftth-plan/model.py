"""Mô hình phối quang FTTH chung cư Phố Đông (Tháp A + B).
Mọi cấu hình nằm ở đầu file; build_xlsx.py / build_html.py đọc từ đây."""
import json, math, os

# ---------------- CẤU HÌNH (sửa ở đây rồi chạy lại build) ----------------
FLOORS = ['23','22','21','20','19','18','17','16','15','14','12A','12','11','10','9','8','7','6','5','4','3','2','1']
# Số căn/tầng = số BOX lớn nhất trên mỗi dòng của bản vẽ (trích tự động từ PDF -> homes_from_drawing.json)
HOMES_PER_FLOOR = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'homes_from_drawing.json')))
# Tủ: tên theo tầng đặt (theo sổ tay thi công) -> các tầng tủ gom (theo bản vẽ gốc: mỗi ODF phục vụ dòng box của tầng đặt ODF + dòng trên + dòng dưới)
CABINET_ZONES = {
    'A': {'23': ['23'], '21': ['22', '21', '20'], '18': ['19', '18', '17'], '15': ['16', '15', '14'], '12': ['12A', '12', '11'],
          '9': ['10', '9', '8'], '7': ['7', '6', '5'], '5': ['4', '3'], '2': ['2', '1']},
    'B': {'23': ['23', '22'], '20': ['21', '20', '19'], '17': ['18', '17', '16'], '14': ['15', '14', '12A'], '11': ['12', '11', '10'],
          '8': ['9', '8', '7'], '5': ['6', '5', '4'], '2': ['3', '2', '1']},
}
# Đánh số cáp trục: TR-x1 = tầng thấp. Mỗi nhóm liệt kê từ trên xuống; tủ cuối nhóm = tủ hub (thấp nhất, sợi 1-8)
TRUNK_GROUPS = {
    'A': [['7', '5', '2'], ['15', '12', '9'], ['23', '21', '18']],
    'B': [['5', '2'], ['14', '11', '8'], ['23', '20', '17']],
}
# ODF 48FO ở Phòng máy, xếp chồng từ THẤP lên CAO; mỗi ODF: khay TRÁI = tháp A, khay PHẢI = tháp B
ODFS = [('ODF-02', 'TR-A1', 'TR-B1'), ('ODF-08/09', 'TR-A2', 'TR-B2'), ('ODF-17/18', 'TR-A3', 'TR-B3')]
# Đối chiếu: ODF trong bản vẽ gốc (tên ODF, tầng đặt, các tầng gom)
DRAWING_ODF = {
    'A': [('ODF24FO-09', '23', ['23']), ('ODF96FO-08', '21', ['22', '21', '20']), ('ODF96FO-07', '18', ['19', '18', '17']),
          ('ODF96FO-06', '15', ['16', '15', '14']), ('ODF96FO-05', '12', ['12A', '12', '11']), ('ODF96FO-04', '9', ['10', '9', '8']),
          ('ODF96FO-03', '6', ['7', '6', '5']), ('ODF96FO-02', '4', ['4', '3']), ('ODF96FO-01', '2', ['2', '1'])],
    'B': [('ODF96FO-17', '23', ['23', '22']), ('ODF96FO-16', '20', ['21', '20', '19']), ('ODF96FO-15', '17', ['18', '17', '16']),
          ('ODF96FO-14', '14', ['15', '14', '12A']), ('ODF96FO-13', '11', ['12', '11', '10']), ('ODF96FO-12', '8', ['9', '8', '7']),
          ('ODF96FO-11', '5', ['6', '5', '4']), ('ODF96FO-10', '2', ['3', '2', '1'])],
}
TRUNK_FO = 24
FO_PER_CABINET = 8
CAB_SLOTS = 4          # số vị trí splitter 1:16 chuẩn của tủ
MAX_SPL = 5            # tối đa cho phép (cần tủ 5 vị trí) khi muốn mỗi splitter chỉ phục vụ 1 tầng
SPL_CAB = 16
SPL_PM = 4             # splitter 1:4 ở PM
PM_USED = 3            # mỗi splitter 1:4: dùng 3 cổng, dự phòng cổng thứ 4
N_PON = 16
PM_FLOOR_IDX = 0       # Phòng máy ở tầng hầm B1 (chỉ số tầng 0; tầng 1 = 1)
TUBE_COLORS = ['Xanh dương', 'Cam', 'Xanh lá', 'Nâu']                       # 4 ống đệm
FIBER_COLORS = ['Xanh dương', 'Cam', 'Xanh lá', 'Nâu', 'Xám', 'Trắng']      # 6 màu sợi / ống
FIBER_HEX = ['#1f6fe5', '#f28c1e', '#2eaa4a', '#8a5a2b', '#8c959f', '#f5f5f5']
TRAY_ROWS, TRAY_COLS = 4, 6
# ODF 96FO ở PM chia 2 nửa: TRÁI = tháp A, PHẢI = tháp B. Mỗi nửa 4 hàng × 12 cột = 48 cổng, đếm từ dưới lên, trái qua phải (mỗi nửa đếm lại từ 1).
# Splitter 1:4 thứ k của mỗi nửa (k = 1..8): đầu vào -> cổng 36+k (37-44, hàng trên cùng, nối OLT bằng dây nhảy); 4 đầu ra -> cổng 4k-3..4k (nối ODF 48FO bằng dây nhảy)
ODF96_ROWS, ODF96_COLS = 4, 12
IN_LOCAL = ODF96_COLS * 3    # 36
PON_PER_TOWER = 8            # PON 1-8 = tháp A, PON 9-16 = tháp B
# -----------------------------------------------------------------------------

def fidx(f):  # chỉ số tầng từ dưới lên (12A = 13, bỏ qua tầng 13)
    return len(FLOORS) - FLOORS.index(f)

def fiber_color(n): return FIBER_COLORS[(n - 1) % 6]
def fiber_tube(n): return (n - 1) // 6 + 1
def tube_color(n): return TUBE_COLORS[fiber_tube(n) - 1]
def pos96(p):
    """Vị trí cổng p (1-48) trong một nửa ODF 96FO: (hàng từ dưới, cột từ trái)."""
    return (p - 1) // ODF96_COLS + 1, (p - 1) % ODF96_COLS + 1

def coupler(n):
    """Vị trí coupler trên khay: hàng 1 = dưới cùng, cột 1 = trái; đếm từ dưới lên, từ trái qua."""
    return (n - 1) // TRAY_COLS + 1, (n - 1) % TRAY_COLS + 1

def build():
    cabinets, trunks, spls, homes = [], [], [], []
    odf_of = {}
    for name, ta, tb in ODFS:
        odf_of[ta] = (name, 'Trái'); odf_of[tb] = (name, 'Phải')
    for t in 'AB':
        zones = CABINET_ZONES[t]
        assert sorted(sum(zones.values(), []), key=FLOORS.index) == FLOORS, 'Các cụm phải phủ đủ mọi tầng'
        for gi, grp in enumerate(TRUNK_GROUPS[t]):
            tid = f'TR-{t}{gi + 1}'
            odf, tray = odf_of[tid]
            trunks.append(dict(id=tid, tower=t, hub=grp[-1], cabs=[f'TU-{t}{f}' for f in grp], fo=TRUNK_FO, odf=odf, tray=tray))
            for slot, cf in enumerate(reversed(grp)):      # từ dưới lên: tủ hub = sợi 1-8
                n = sum(HOMES_PER_FLOOR[t][f] for f in zones[cf])
                # Mỗi splitter chỉ phục vụ 1 tầng (cáp 1FO tới căn hộ đã đặt cố định theo tầng); tầng >16 hộ chiếm nhiều splitter.
                # Nếu cách này vượt số vị trí splitter của tủ thì đổ đầy liên tiếp từ dưới lên.
                aligned = sum(math.ceil(HOMES_PER_FLOOR[t][f] / SPL_CAB) for f in zones[cf])
                groups = []   # mỗi phần tử = danh sách (tầng, căn) của 1 splitter
                if aligned <= MAX_SPL:
                    for f in reversed(zones[cf]):
                        hl_f = [(f, a) for a in range(1, HOMES_PER_FLOOR[t][f] + 1)]
                        k_ = math.ceil(len(hl_f) / SPL_CAB); base_, extra_ = divmod(len(hl_f), k_); pos_ = 0   # chia đều cho các splitter của tầng
                        for j in range(k_):
                            sz = base_ + (1 if j < extra_ else 0); groups.append(hl_f[pos_:pos_ + sz]); pos_ += sz
                    mode = 'tầng'
                else:
                    hl = [(f, a) for f in reversed(zones[cf]) for a in range(1, HOMES_PER_FLOOR[t][f] + 1)]
                    for i in range(0, len(hl), SPL_CAB): groups.append(hl[i:i + SPL_CAB])
                    mode = 'liên tiếp'
                nspl = len(groups)
                assert nspl <= MAX_SPL and nspl <= FO_PER_CABINET, (t, cf, n)
                cabinets.append(dict(id=f'TU-{t}{cf}', tower=t, floor=cf, zone=zones[cf], trunk=tid, slot=slot + 1, nspl=nspl, homes=n,
                                     fiber_from=FO_PER_CABINET * slot + 1, fiber_to=FO_PER_CABINET * (slot + 1), hub=(cf == grp[-1]), split_mode=mode, slots=max(CAB_SLOTS, nspl)))
                for si, g in enumerate(groups):
                    spls.append(dict(id=f'TU-{t}{cf}/S{si + 1}', cab=f'TU-{t}{cf}', idx=si + 1, fiber=FO_PER_CABINET * slot + si + 1,
                                     trunk=tid, n=len(g), odf=odf, tray=tray, floors=sorted({f for f, _ in g}, key=FLOORS.index)))
                    for k, (f, a) in enumerate(g):
                        homes.append(dict(code=f'{t}-{f}-{a:02d}', tower=t, floor=f, apt=a, cab=f'TU-{t}{cf}', spl=f'TU-{t}{cf}/S{si + 1}', port=k + 1))
    # Cấp cổng PM tách riêng từng tháp: tháp A -> PON 1-8, tháp B -> PON 9-16; theo trục từ thấp lên cao (TR-x1 -> x3), sợi tăng dần.
    # Mỗi PON dùng 3 cổng 1:4; nếu tháp cần nhiều hơn 8x3 thì dùng thêm cổng thứ 4 của các PON cuối.
    for ti, t in enumerate('AB'):
        order = sorted([s_ for s_ in spls if s_['cab'][3] == t], key=lambda s_: (s_['trunk'], s_['fiber']))
        cap = PON_PER_TOWER
        extra = max(0, len(order) - cap * PM_USED)
        assert extra <= cap, f'Tháp {t} cần {len(order)} cổng, tối đa {cap * SPL_PM}'
        counts = [PM_USED] * cap
        for i in range(extra): counts[cap - 1 - i] += 1
        if len(order) < cap * PM_USED:
            rest = len(order); counts = []
            for _ in range(cap):
                c = min(PM_USED, rest); counts.append(c); rest -= c
        pos = 0
        for k, c in enumerate(counts, 1):
            for loc in range(1, c + 1):
                sp = order[pos]; pos += 1
                pon = ti * cap + k
                sp.update(pon=pon, pmspl=pon, pmloc=loc, pmhalf=t, pmk=k, pmout=(k - 1) * SPL_PM + loc, pmin=IN_LOCAL + k)
        assert pos == len(order)
    spls.sort(key=lambda s: (s['cab'][3], FLOORS.index(s['cab'][4:]), s['idx']))
    sp_by = {s['id']: s for s in spls}
    for h in homes:
        s = sp_by[h['spl']]
        h.update({k: s[k] for k in ('trunk', 'fiber', 'pmspl', 'pmloc', 'pmhalf', 'pmk', 'pmout', 'pmin', 'pon', 'odf', 'tray')})
    homes.sort(key=lambda h: (h['tower'], FLOORS.index(h['floor']), h['apt']))
    cabinets.sort(key=lambda c: (c['tower'], FLOORS.index(c['floor'])))
    return dict(cabinets=cabinets, trunks=trunks, spls=spls, homes=homes)

if __name__ == '__main__':
    d = build()
    print(len(d['cabinets']), 'tủ', len(d['spls']), 'splitter', len(d['homes']), 'căn hộ')
    for c in d['cabinets']: print(c['id'], c['zone'], c['homes'], c['nspl'], c['trunk'], c['fiber_from'], c['fiber_to'])
    from collections import Counter
    print(sorted(Counter(h['pon'] for h in d['homes']).items()))
