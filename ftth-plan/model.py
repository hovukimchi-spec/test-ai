"""Mô hình phối quang FTTH chung cư Phố Đông (Tháp A + B).
Mọi cấu hình nằm ở đầu file; build_xlsx.py / build_html.py đọc từ đây."""
import math

# ---------------- CẤU HÌNH (sửa ở đây rồi chạy lại build.py) ----------------
FLOORS = ['23','22','21','20','19','18','17','16','15','14','12A','12','11','10','9','8','7','6','5','4','3','2','1']
HOMES_PER_FLOOR = {'A': {f: 14 for f in FLOORS}, 'B': {f: 14 for f in FLOORS}}
# Tầng đặt tủ (đọc từ sổ tay): tủ nằm ở tầng cao nhất của cụm và phục vụ các tầng bên dưới cho tới tủ kế tiếp
CABINET_FLOORS = {
    'A': ['23', '21', '18', '15', '12', '9', '7', '5', '2'],
    'B': ['23', '20', '17', '14', '11', '8', '5', '2'],
}
# Nhóm 3 tủ -> 1 cáp trục 24FO (tủ cuối nhóm = tủ "hub", nơi cáp trục về PM)
TRUNK_GROUPS = {
    'A': [['23', '21', '18'], ['15', '12', '9'], ['7', '5', '2']],
    'B': [['23', '20', '17'], ['14', '11', '8'], ['5', '2']],
}
TRUNK_FO = 24
FO_PER_CABINET = 8
CAB_SLOTS = 4          # số vị trí splitter 1:16 tối đa trong tủ
MIN_SPL = 3            # số splitter 1:16 lắp tối thiểu mỗi tủ
SPL_CAB = 16           # tỉ lệ splitter tủ
SPL_PM = 4             # tỉ lệ splitter PM
N_PON = 16
PM_FLOOR = '2'         # Phòng máy ở tầng 2 (theo sổ tay)

FIBER_COLORS = ['Xanh dương', 'Cam', 'Xanh lá', 'Nâu', 'Xám', 'Trắng', 'Đỏ', 'Đen', 'Vàng', 'Tím', 'Hồng', 'Xanh ngọc']
FIBER_HEX = ['#1f6fe5', '#f28c1e', '#2eaa4a', '#8a5a2b', '#8c959f', '#f5f5f5', '#e5303a', '#222222', '#f2d11e', '#8e44ad', '#f08bb5', '#19b6b0']
# -----------------------------------------------------------------------------

def fidx(f):  # chỉ số tầng từ dưới lên (12A = 13, bỏ qua tầng 13)
    return len(FLOORS) - FLOORS.index(f)

def fiber_color(n):  # n = 1..24
    return FIBER_COLORS[(n - 1) % 12]

def fiber_tube(n):
    return (n - 1) // 12 + 1

def build():
    cabinets, trunks, spls, homes = [], [], [], []
    for t in 'AB':
        cabfl = CABINET_FLOORS[t]
        # vùng phục vụ
        zones = {}
        for i, cf in enumerate(cabfl):
            start = FLOORS.index(cf)
            end = FLOORS.index(cabfl[i + 1]) if i + 1 < len(cabfl) else len(FLOORS)
            zones[cf] = FLOORS[start:end]
        for gi, grp in enumerate(TRUNK_GROUPS[t]):
            tid = f'TR-{t}{gi + 1}'
            trunks.append(dict(id=tid, tower=t, hub=grp[-1], cabs=[f'TU-{t}{f}' for f in grp], fo=TRUNK_FO))
            for slot, cf in enumerate(grp):
                hl = [(f, a) for f in zones[cf] for a in range(1, HOMES_PER_FLOOR[t][f] + 1)]
                n = len(hl)
                nspl = max(MIN_SPL, math.ceil(n / SPL_CAB))
                assert nspl <= CAB_SLOTS and nspl <= FO_PER_CABINET
                cabinets.append(dict(id=f'TU-{t}{cf}', tower=t, floor=cf, zone=zones[cf], trunk=tid,
                                     slot=slot + 1, nspl=nspl, homes=n,
                                     fiber_from=FO_PER_CABINET * slot + 1, fiber_to=FO_PER_CABINET * (slot + 1),
                                     hub=(cf == grp[-1])))
                # chia đều theo khối liên tiếp
                base, extra = divmod(n, nspl)
                pos = 0
                for s in range(nspl):
                    cnt = base + (1 if s < extra else 0)
                    spls.append(dict(id=f'TU-{t}{cf}/S{s + 1}', cab=f'TU-{t}{cf}', idx=s + 1,
                                     fiber=FO_PER_CABINET * slot + s + 1, trunk=tid, n=cnt))
                    for k, (f, a) in enumerate(hl[pos:pos + cnt]):
                        homes.append(dict(code=f'{t}-{f}-{a:02d}', tower=t, floor=f, apt=a,
                                          cab=f'TU-{t}{cf}', spl=f'TU-{t}{cf}/S{s + 1}', port=k + 1))
                    pos += cnt
    # gán PM: mỗi tháp bắt đầu ở splitter 1:4 mới
    pm_n = 0
    for t in 'AB':
        pm_n = math.ceil(pm_n / SPL_PM) * SPL_PM
        for sp in [s for s in spls if s['cab'][3] == t]:
            sp['pmspl'] = pm_n // SPL_PM + 1
            sp['pmout'] = pm_n % SPL_PM + 1
            sp['pon'] = sp['pmspl']
            pm_n += 1
    assert pm_n <= N_PON * SPL_PM, 'Không đủ cổng splitter 1:4 ở PM'
    sp_by = {s['id']: s for s in spls}
    for h in homes:
        s = sp_by[h['spl']]
        h.update(trunk=s['trunk'], fiber=s['fiber'], pmspl=s['pmspl'], pmout=s['pmout'], pon=s['pon'])
    return dict(cabinets=cabinets, trunks=trunks, spls=spls, homes=homes)

if __name__ == '__main__':
    d = build()
    print(len(d['cabinets']), 'tủ', len(d['spls']), 'splitter', len(d['homes']), 'căn hộ')
    for c in d['cabinets']: print(c['id'], c['zone'], c['homes'], c['nspl'], c['trunk'], c['fiber_from'], c['fiber_to'])
