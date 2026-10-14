"""Mô hình phối quang FTTH chung cư Phố Đông (Tháp A + B).
Mọi cấu hình nằm ở đầu file; build_xlsx.py / build_html.py đọc từ đây."""
import json, math, os

# ---------------- CẤU HÌNH (sửa ở đây rồi chạy lại build) ----------------
FLOORS = ['23','22','21','20','19','18','17','16','15','14','12A','12','11','10','9','8','7','6','5','4','3','2','1']
# Số căn/tầng = số BOX lớn nhất trên mỗi dòng của bản vẽ (trích tự động từ PDF -> homes_from_drawing.json)
HOMES_PER_FLOOR = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'homes_from_drawing.json')))
# Tầng đặt tủ (đọc từ sổ tay): tủ ở tầng cao nhất của cụm, phục vụ các tầng bên dưới tới tủ kế tiếp
CABINET_FLOORS = {
    'A': ['23', '21', '18', '15', '12', '9', '7', '5', '2'],
    'B': ['23', '20', '17', '14', '11', '8', '5', '2'],
}
# Nhóm tủ -> 1 cáp trục 24FO (liệt kê từ trên xuống; tủ cuối = tủ hub, thấp nhất)
TRUNK_GROUPS = {
    'A': [['23', '21', '18'], ['15', '12', '9'], ['7', '5', '2']],
    'B': [['23', '20', '17'], ['14', '11', '8'], ['5', '2']],
}
# ODF 48FO ở Phòng máy: mỗi ODF hàn 2 cáp trục 24FO (khay TRÁI = tháp A, khay PHẢI = tháp B)
ODFS = [('ODF-02', 'TR-A3', 'TR-B3'), ('ODF-08/09', 'TR-A2', 'TR-B2'), ('ODF-17/18', 'TR-A1', 'TR-B1')]
TRUNK_FO = 24
FO_PER_CABINET = 8
CAB_SLOTS = 4          # vị trí splitter 1:16 tối đa trong tủ
SPL_CAB = 16
SPL_PM = 4             # splitter 1:4 ở PM
PM_USED = 3            # mỗi splitter 1:4: dùng 3 cổng, dự phòng cổng thứ 4
N_PON = 16
PM_FLOOR_IDX = 0       # Phòng máy ở tầng hầm B1 (chỉ số tầng 0; tầng 1 = 1)
TUBE_COLORS = ['Xanh dương', 'Cam', 'Xanh lá', 'Nâu']                       # 4 ống đệm
FIBER_COLORS = ['Xanh dương', 'Cam', 'Xanh lá', 'Nâu', 'Xám', 'Trắng']      # 6 màu sợi / ống
FIBER_HEX = ['#1f6fe5', '#f28c1e', '#2eaa4a', '#8a5a2b', '#8c959f', '#f5f5f5']
TRAY_ROWS, TRAY_COLS = 4, 6
# -----------------------------------------------------------------------------

def fidx(f):  # chỉ số tầng từ dưới lên (12A = 13, bỏ qua tầng 13)
    return len(FLOORS) - FLOORS.index(f)

def fiber_color(n): return FIBER_COLORS[(n - 1) % 6]
def fiber_tube(n): return (n - 1) // 6 + 1
def tube_color(n): return TUBE_COLORS[fiber_tube(n) - 1]
def coupler(n):
    """Vị trí coupler trên khay: hàng 1 = dưới cùng, cột 1 = trái; đếm từ dưới lên, từ trái qua."""
    return (n - 1) // TRAY_COLS + 1, (n - 1) % TRAY_COLS + 1

def build():
    cabinets, trunks, spls, homes = [], [], [], []
    odf_of = {}
    for name, ta, tb in ODFS:
        odf_of[ta] = (name, 'Trái'); odf_of[tb] = (name, 'Phải')
    for t in 'AB':
        cabfl = CABINET_FLOORS[t]
        zones = {}
        for i, cf in enumerate(cabfl):
            start = FLOORS.index(cf)
            end = FLOORS.index(cabfl[i + 1]) if i + 1 < len(cabfl) else len(FLOORS)
            zones[cf] = FLOORS[start:end]
        for gi, grp in enumerate(TRUNK_GROUPS[t]):
            tid = f'TR-{t}{gi + 1}'
            odf, tray = odf_of[tid]
            trunks.append(dict(id=tid, tower=t, hub=grp[-1], cabs=[f'TU-{t}{f}' for f in grp], fo=TRUNK_FO, odf=odf, tray=tray))
            for slot, cf in enumerate(reversed(grp)):      # từ dưới lên: tủ hub = sợi 1-8
                hl = [(f, a) for f in reversed(zones[cf]) for a in range(1, HOMES_PER_FLOOR[t][f] + 1)]
                n = len(hl)
                nspl = math.ceil(n / SPL_CAB)
                assert nspl <= CAB_SLOTS and nspl <= FO_PER_CABINET, (t, cf, n)
                cabinets.append(dict(id=f'TU-{t}{cf}', tower=t, floor=cf, zone=zones[cf], trunk=tid, slot=slot + 1, nspl=nspl, homes=n,
                                     fiber_from=FO_PER_CABINET * slot + 1, fiber_to=FO_PER_CABINET * (slot + 1), hub=(cf == grp[-1])))
                pos = 0
                for s in range(nspl):                       # đổ đầy từng splitter 16 cổng, từ dưới lên
                    cnt = min(SPL_CAB, n - pos)
                    spls.append(dict(id=f'TU-{t}{cf}/S{s + 1}', cab=f'TU-{t}{cf}', idx=s + 1, fiber=FO_PER_CABINET * slot + s + 1,
                                     trunk=tid, n=cnt, odf=odf, tray=tray))
                    for k, (f, a) in enumerate(hl[pos:pos + cnt]):
                        homes.append(dict(code=f'{t}-{f}-{a:02d}', tower=t, floor=f, apt=a, cab=f'TU-{t}{cf}', spl=f'TU-{t}{cf}/S{s + 1}', port=k + 1))
                    pos += cnt
    # thứ tự cấp cổng PM: theo ODF từ dưới lên (02 -> 08/09 -> 17/18), khay trái (A) rồi phải (B), sợi tăng dần
    order = []
    for name, ta, tb in ODFS:
        for tid in (ta, tb):
            order += sorted([s for s in spls if s['trunk'] == tid], key=lambda s: s['fiber'])
    n = 0
    for sp in order:
        pon = n // PM_USED + 1
        loc = n % PM_USED + 1
        sp.update(pon=pon, pmspl=pon, pmloc=loc, pmout=(pon - 1) * SPL_PM + loc)
        n += 1
    assert n <= N_PON * PM_USED, f'Cần {n} cổng 1:4, PM chỉ có {N_PON * PM_USED}'
    spls.sort(key=lambda s: (s['cab'][3], FLOORS.index(s['cab'][4:]), s['idx']))
    sp_by = {s['id']: s for s in spls}
    for h in homes:
        s = sp_by[h['spl']]
        h.update({k: s[k] for k in ('trunk', 'fiber', 'pmspl', 'pmloc', 'pmout', 'pon', 'odf', 'tray')})
    homes.sort(key=lambda h: (h['tower'], FLOORS.index(h['floor']), h['apt']))
    cabinets.sort(key=lambda c: (c['tower'], FLOORS.index(c['floor'])))
    return dict(cabinets=cabinets, trunks=trunks, spls=spls, homes=homes)

if __name__ == '__main__':
    d = build()
    print(len(d['cabinets']), 'tủ', len(d['spls']), 'splitter', len(d['homes']), 'căn hộ')
    for c in d['cabinets']: print(c['id'], c['zone'], c['homes'], c['nspl'], c['trunk'], c['fiber_from'], c['fiber_to'])
    from collections import Counter
    print(sorted(Counter(h['pon'] for h in d['homes']).items()))
