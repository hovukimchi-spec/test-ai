import colorsys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import DataBarRule, CellIsRule, FormulaRule
import model as M

D = M.build()
cabs, trunks, spls, homes = D['cabinets'], D['trunks'], D['spls'], D['homes']
NH = len(homes)
STATUS = ['Chưa lắp', 'Đã đấu nối', 'Hoạt động', 'Sự cố']

S_TQ, S_SD, S_TU, S_ST, S_ODF, S_TB, S_TC, S_QC, S_VT, S_VH = (
    'Tổng quan', 'Sơ đồ trục', 'Tủ phối quang', 'Sợi trục', 'ODF-PM & PON', 'Thuê bao', 'Tra cứu',
    'Quỹ công suất', 'Vật tư', 'Vận hành')
q = lambda s: "'" + s + "'"

NAVY, BLUE, GREY, LIGHT = '1F3A5F', '2F6FDE', 'F2F4F7', 'EAF1FF'
thin = Side(style='thin', color='C8CDD4')
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
F = 'Arial'

def fill(h): return PatternFill('solid', start_color=h.lstrip('#'), end_color=h.lstrip('#'))
def hue(i, n, s=0.55, l=0.82):
    r, g, b = colorsys.hls_to_rgb(i / n, l, s)
    return '%02X%02X%02X' % (int(r * 255), int(g * 255), int(b * 255))

def title(ws, text, sub=None, width=10):
    ws['A1'] = text; ws['A1'].font = Font(name=F, size=16, bold=True, color=NAVY)
    if sub:
        ws['A2'] = sub; ws['A2'].font = Font(name=F, size=10, italic=True, color='5B6573')
    ws.sheet_view.showGridLines = False

def header(ws, row, cols, col0=1, h=30):
    for i, c in enumerate(cols):
        x = ws.cell(row=row, column=col0 + i, value=c)
        x.font = Font(name=F, bold=True, color='FFFFFF', size=10)
        x.fill = fill(NAVY); x.border = BORDER
        x.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[row].height = h

def body(ws, r, c, v, bold=False, center=False, fmt=None, bg=None, color='000000', wrap=False):
    x = ws.cell(row=r, column=c, value=v)
    x.font = Font(name=F, size=10, bold=bold, color=color)
    x.border = BORDER
    x.alignment = Alignment(horizontal='center' if center else 'left', vertical='center', wrap_text=wrap)
    if fmt: x.number_format = fmt
    if bg: x.fill = fill(bg)
    return x

def widths(ws, ws_w):
    for i, w in enumerate(ws_w, 1): ws.column_dimensions[L(i)].width = w

wb = Workbook()
wsT = wb.active; wsT.title = S_TQ
wsD = wb.create_sheet(S_SD); wsC = wb.create_sheet(S_TU); wsK = wb.create_sheet(S_ST)
wsO = wb.create_sheet(S_ODF); wsH = wb.create_sheet(S_TB); wsS = wb.create_sheet(S_TC)
wsQ = wb.create_sheet(S_QC); wsV = wb.create_sheet(S_VT); wsG = wb.create_sheet(S_VH)

# =============== THUÊ BAO ===============
cols = ['Mã căn hộ', 'Tháp', 'Tầng', 'Căn', 'Tủ phối quang', 'Splitter 1:16', 'Cổng splitter', 'Cáp trục', 'Sợi trục (1-24)',
        'Màu sợi', 'Splitter PM 1:4', 'Cổng ra 1:4', 'PON', 'Trạng thái', 'Serial ONU / Ghi chú', 'Ngày lắp', 'Đường quang (tự ghép)']
header(wsH, 1, cols, h=36)
H0, H1 = 2, NH + 1
for i, h in enumerate(homes):
    r = i + 2
    vals = [h['code'], h['tower'], h['floor'], h['apt'], h['cab'], h['spl'], h['port'], h['trunk'], h['fiber'],
            M.fiber_color(h['fiber']), f"S4-{h['pmspl']:02d}", h['pmout'], f"PON-{h['pon']:02d}", 'Chưa lắp', None, None]
    for c, v in enumerate(vals, 1):
        body(wsH, r, c, v, center=c not in (1, 15), bg=('FFFFFF' if i // 14 % 2 == 0 else GREY))
    body(wsH, r, 17, f'=M{r}&" > "&K{r}&"/"&L{r}&" > "&H{r}&"#"&I{r}&" > "&E{r}&" > "&F{r}&" p"&G{r}')
    wsH.cell(row=r, column=16).number_format = 'dd/mm/yyyy'
widths(wsH, [12, 6, 6, 6, 12, 15, 9, 10, 10, 12, 12, 9, 9, 13, 24, 12, 52])
wsH.freeze_panes = 'B2'
wsH.auto_filter.ref = f'A1:Q{H1}'
dv = DataValidation(type='list', formula1='"' + ','.join(STATUS) + '"', allow_blank=False)
wsH.add_data_validation(dv); dv.add(f'N2:N{H1}')
rng = f'N2:N{H1}'
for txt, col in [('Hoạt động', 'C6EFCE'), ('Đã đấu nối', 'FFEB9C'), ('Sự cố', 'FFC7CE')]:
    wsH.conditional_formatting.add(rng, CellIsRule(operator='equal', formula=[f'"{txt}"'], fill=fill(col)))
HR = lambda col: f"{q(S_TB)}!${col}$2:${col}${H1}"

# =============== QUỸ CÔNG SUẤT (tham số) ===============
title(wsQ, 'Quỹ công suất quang & tham số chia', 'Ô xanh nhạt là tham số có thể sửa; các ô còn lại tự tính.')
widths(wsQ, [3, 46, 14, 40])
header(wsQ, 3, ['Tham số chia', 'Giá trị', 'Ghi chú'], col0=2, h=22)
P = [('Tỉ lệ splitter PM (1:N)', M.SPL_PM, 'Tại phòng máy'), ('Tỉ lệ splitter tủ (1:N)', M.SPL_CAB, 'Tại tủ tầng'),
     ('Tỉ lệ chia tổng / cổng PON', '=C4*C5', 'tức 1:64'), ('Số cổng PON', M.N_PON, '16 splitter 1:4 ↔ 16 PON')]
for i, (a, b, c) in enumerate(P):
    r = 4 + i
    body(wsQ, r, 2, a); body(wsQ, r, 3, b, center=True, bg=(LIGHT if not str(b).startswith('=') else None)); body(wsQ, r, 4, c)
header(wsQ, 9, ['Thông số công suất (GPON Class B+ mặc định)', 'Giá trị', 'Ghi chú'], col0=2, h=22)
P2 = [('Công suất phát OLT tối thiểu (dBm)', 1.5, 'Class B+: +1.5 ~ +5'), ('Độ nhạy thu ONU (dBm)', -28, 'Class B+: -28'),
      ('Quỹ công suất (dB)', '=C10-C11', 'Tx - Rx'), ('Biên dự phòng yêu cầu (dB)', 3, 'Lão hoá, uốn cong, vệ sinh đầu nối'),
      ('Suy hao sợi 1310nm (dB/km)', 0.35, ''), ('Chiều dài cáp trục tối đa (m)', 150, 'PM → tầng cao nhất, ước tính'),
      ('Chiều dài cáp thuê bao 1FO tối đa (m)', 60, 'Căn hộ xa nhất → tủ')]
for i, (a, b, c) in enumerate(P2):
    r = 10 + i
    body(wsQ, r, 2, a); body(wsQ, r, 3, b, center=True, bg=(LIGHT if not str(b).startswith('=') else None)); body(wsQ, r, 4, c)
header(wsQ, 19, ['Hạng mục suy hao (đường xấu nhất)', 'Số lượng', 'Suy hao đơn vị (dB)', 'Tổng (dB)'], col0=2, h=22)
wsQ.column_dimensions['E'].width = 14
LOSS = [('Splitter 1:4 (PM)', 1, 7.3), ('Splitter 1:16 (tủ)', 1, 13.8), ('Cặp đầu nối SC/APC', 6, 0.5),
        ('Mối hàn nóng chảy', 4, 0.1), ('Sợi quang (km)', '=(C15+C16)/1000', '=C14'), ('Dự phòng uốn cong / vệ sinh (dB)', 1, 1.0)]
for i, (a, n, u) in enumerate(LOSS):
    r = 20 + i
    body(wsQ, r, 2, a); body(wsQ, r, 3, n, center=True, bg=LIGHT if not str(n).startswith('=') else None, fmt='0.000' if str(n).startswith('=') else None)
    body(wsQ, r, 4, u, center=True, bg=LIGHT if not str(u).startswith('=') else None); body(wsQ, r, 5, f'=C{r}*D{r}', center=True, fmt='0.00')
body(wsQ, 26, 2, 'TỔNG SUY HAO', bold=True); body(wsQ, 26, 3, None); body(wsQ, 26, 4, None); body(wsQ, 26, 5, '=SUM(E20:E25)', True, True, '0.00')
body(wsQ, 27, 2, 'MARGIN CÒN LẠI (dB)', bold=True); body(wsQ, 27, 3, None); body(wsQ, 27, 4, None); body(wsQ, 27, 5, '=C12-E26', True, True, '0.00')
body(wsQ, 28, 2, 'KẾT LUẬN', bold=True); body(wsQ, 28, 3, None); body(wsQ, 28, 4, None)
body(wsQ, 28, 5, '=IF(E27>=C13,"ĐẠT","XEM LẠI")', True, True)
wsQ.conditional_formatting.add('E28', CellIsRule(operator='equal', formula=['"ĐẠT"'], fill=fill('C6EFCE')))
wsQ.conditional_formatting.add('E28', CellIsRule(operator='equal', formula=['"XEM LẠI"'], fill=fill('FFC7CE')))
wsQ['B30'] = ('Lưu ý: nếu dùng PON Class C+ hoặc XGS-PON thì sửa Tx/Rx ở trên. Đo thực tế bằng OPM/OTDR sau khi thi công; '
              'công suất thu tại ONU nên nằm trong -8 … -27 dBm.')
wsQ['B30'].font = Font(name=F, size=9, italic=True, color='5B6573'); wsQ['B30'].alignment = Alignment(wrap_text=True, vertical='top')
wsQ.merge_cells('B30:E31')

# =============== ODF-PM & PON ===============
title(wsO, 'Bảng đấu nối tại Phòng máy: PON → Splitter 1:4 → ODF → Cáp trục', 'Mỗi cổng ra của splitter 1:4 nhảy vào 1 sợi cáp trục, tới 1 splitter 1:16 trong tủ.')
cols = ['PON', 'Splitter PM 1:4', 'Cổng ra', 'Cổng ODF (cáp trục/sợi)', 'Màu sợi', 'Tủ đích', 'Splitter 1:16 đích', 'Số căn hộ', 'Hoạt động', 'Trạng thái cổng']
header(wsO, 4, cols, h=30)
sp_by_pm = {(s['pmspl'], s['pmout']): s for s in spls}
r = 5
for pon in range(1, M.N_PON + 1):
    for out in range(1, M.SPL_PM + 1):
        s = sp_by_pm.get((pon, out))
        bg = 'FFFFFF' if pon % 2 else GREY
        body(wsO, r, 1, f'PON-{pon:02d}', True, True, bg=bg); body(wsO, r, 2, f'S4-{pon:02d}', center=True, bg=bg); body(wsO, r, 3, out, center=True, bg=bg)
        if s:
            vals = [f"{s['trunk']}/{s['fiber']:02d}", M.fiber_color(s['fiber']), s['cab'], s['id']]
            for c, v in enumerate(vals, 4): body(wsO, r, c, v, center=True, bg=bg)
            body(wsO, r, 8, f"=COUNTIF({HR('F')},G{r})", center=True, bg=bg)
            body(wsO, r, 9, f"=COUNTIFS({HR('F')},G{r},{HR('N')},\"Hoạt động\")", center=True, bg=bg)
            body(wsO, r, 10, 'Đã dùng', center=True, bg=bg)
        else:
            for c in range(4, 8): body(wsO, r, c, '—', center=True, bg=bg)
            body(wsO, r, 8, 0, center=True, bg=bg); body(wsO, r, 9, 0, center=True, bg=bg); body(wsO, r, 10, 'Dự phòng', center=True, bg=bg, color='7A7A7A')
        r += 1
OD1 = r - 1
widths(wsO, [10, 14, 9, 22, 12, 12, 18, 10, 10, 14])
wsO.freeze_panes = 'A5'; wsO.auto_filter.ref = f'A4:J{OD1}'
wsO.conditional_formatting.add(f'J5:J{OD1}', CellIsRule(operator='equal', formula=['"Dự phòng"'], fill=fill('EDEDED')))
OR = lambda col: f"{q(S_ODF)}!${col}$5:${col}${OD1}"

# =============== SỢI TRỤC ===============
title(wsK, 'Bảng sợi cáp trục (6 cáp × 24FO)', 'Mã màu theo chuẩn TIA-598: ống đệm 1 = xanh dương (sợi 1-12), ống đệm 2 = cam (sợi 13-24).')
header(wsK, 4, ['Cáp trục', 'Sợi', 'Ống đệm', 'Màu sợi', 'Cáp nhánh 8FO #', 'Tủ', 'Splitter 1:16', 'Splitter PM', 'PON', 'Trạng thái'], h=30)
cab_by = {c['id']: c for c in cabs}
spl_by_fiber = {(s['trunk'], s['fiber']): s for s in spls}
r = 5
for t in trunks:
    for fnum in range(1, M.TRUNK_FO + 1):
        sub = (fnum - 1) // M.FO_PER_CABINET + 1
        cabid = t['cabs'][sub - 1] if sub <= len(t['cabs']) else None
        s = spl_by_fiber.get((t['id'], fnum))
        tube = M.fiber_tube(fnum)
        bg = 'FFFFFF' if (r // 24) % 2 == 0 else GREY
        vals = [t['id'], fnum, 'Xanh dương' if tube == 1 else 'Cam', M.fiber_color(fnum), sub, cabid or '(chưa cấp)']
        for c, v in enumerate(vals, 1): body(wsK, r, c, v, center=True, bg=bg)
        if s:
            body(wsK, r, 7, s['id'], center=True, bg=bg); body(wsK, r, 8, f"S4-{s['pmspl']:02d}/{s['pmout']}", center=True, bg=bg)
            body(wsK, r, 9, f"PON-{s['pon']:02d}", center=True, bg=bg); body(wsK, r, 10, 'Đang dùng', center=True, bg='DFF3E3')
        else:
            for c in (7, 8, 9): body(wsK, r, c, '—', center=True, bg=bg)
            body(wsK, r, 10, 'Dự phòng' if cabid else 'Chưa cấp', center=True, bg='EDEDED', color='7A7A7A')
        r += 1
widths(wsK, [10, 6, 12, 12, 14, 12, 16, 12, 10, 12]); wsK.freeze_panes = 'A5'; wsK.auto_filter.ref = f'A4:J{r - 1}'

# =============== TỦ PHỐI QUANG ===============
title(wsC, 'Danh mục tủ phối quang (17 tủ)', 'Số hộ / sử dụng / hoạt động tự cập nhật từ sheet "Thuê bao".')
cols = ['Mã tủ', 'Tháp', 'Tầng đặt', 'Các tầng phục vụ', 'Số căn hộ', 'Splitter 1:16 lắp', 'Vị trí trống', 'Số cổng khả dụng',
        '% sử dụng cổng', 'Hoạt động', 'Cáp trục', 'Dải sợi (8FO)', 'Vai trò', 'PON cấp nguồn']
header(wsC, 4, cols, h=36)
for i, c in enumerate(cabs):
    r = 5 + i
    bg = hue(i, len(cabs), 0.5, 0.9)
    pons = sorted({f"PON-{s['pon']:02d}" for s in spls if s['cab'] == c['id']})
    vals = [c['id'], c['tower'], c['floor'], ', '.join(c['zone']), f"=COUNTIF({HR('E')},A{r})", c['nspl'],
            M.CAB_SLOTS - c['nspl'], f'=F{r}*{M.SPL_CAB}', f'=E{r}/H{r}', f"=COUNTIFS({HR('E')},A{r},{HR('N')},\"Hoạt động\")",
            c['trunk'], f"{c['fiber_from']}-{c['fiber_to']}", 'HUB (cáp trục 24FO về PM)' if c['hub'] else 'Tủ nhánh (cáp 8FO về hub)', ', '.join(pons)]
    for k, v in enumerate(vals, 1): body(wsC, r, k, v, center=k not in (4, 13, 14), bg=bg if k == 1 else None, bold=(k == 1), fmt='0%' if k == 9 else None)
widths(wsC, [11, 6, 9, 20, 10, 12, 9, 11, 11, 10, 10, 12, 28, 18])
wsC.freeze_panes = 'B5'
wsC.conditional_formatting.add('I5:I21', DataBarRule(start_type='num', start_value=0, end_type='num', end_value=1, color='5B9BD5'))
wsC.conditional_formatting.add('I5:I21', CellIsRule(operator='greaterThan', formula=['0.95'], font=Font(color='C00000', bold=True)))
body(wsC, 22, 1, 'Tổng', True, True)
for c in range(2, 15): body(wsC, 22, c, None)
for col in 'EFGHJ': body(wsC, 22, ord(col) - 64, f'=SUM({col}5:{col}21)', True, True)
body(wsC, 22, 9, '=E22/H22', True, True, '0%')

# =============== SƠ ĐỒ TRỤC ===============
title(wsD, 'Sơ đồ trục thông tầng – Tháp A & Tháp B (số hoá từ sổ tay)',
      'Mỗi tủ đặt ở tầng đậm màu, phục vụ các tầng cùng màu bên dưới. Cột "Trục" = cáp trục 24FO chạy dọc hộp kỹ thuật xuống Phòng Máy.')
blocks = {'A': 2, 'B': 12}
hdr = ['Tầng', 'Trục 1', 'Trục 2', 'Trục 3', 'Tủ', 'Số hộ', 'PON', 'Splitter']
trunk_colors = {0: '2F6FDE', 1: 'E8710A', 2: '1E9E5A'}
wsD.column_dimensions['A'].width = 2
for t, c0 in blocks.items():
    for k, w in enumerate([7, 6, 6, 6, 18, 7, 12, 9]): wsD.column_dimensions[L(c0 + k)].width = w
    wsD.merge_cells(start_row=4, start_column=c0, end_row=4, end_column=c0 + 7)
    x = wsD.cell(row=4, column=c0, value=f'THÁP {t}'); x.font = Font(name=F, bold=True, size=13, color='FFFFFF'); x.fill = fill(NAVY); x.alignment = Alignment(horizontal='center')
    header(wsD, 5, hdr, col0=c0, h=22)
    tcabs = [c for c in cabs if c['tower'] == t]
    tr_list = [x for x in trunks if x['tower'] == t]
    for fi, fl in enumerate(M.FLOORS):
        r = 6 + fi
        body(wsD, r, c0, f'{fl}F', True, True, bg=GREY)
        cab = next(c for c in tcabs if fl in c['zone'])
        ci = tcabs.index(cab)
        bg = hue(ci, len(tcabs), 0.55, 0.86)
        is_cab = (cab['floor'] == fl)
        for k, tr in enumerate(tr_list):
            top = min(M.FLOORS.index(c['floor']) for c in cabs if c['id'] in tr['cabs'])
            cell = body(wsD, r, c0 + 1 + k, None, center=True)
            cell.border = Border(left=Side(style='thin', color='FFFFFF'), right=Side(style='thin', color='FFFFFF'))
            if M.FLOORS.index(fl) >= top:
                cell.fill = fill(trunk_colors[k])
                if is_cab and cab['id'] in tr['cabs']:
                    cell.value = '●'; cell.font = Font(name=F, color='FFFFFF', bold=True, size=11)
        tcell = body(wsD, r, c0 + 4, f"{cab['id']}  ({cab['nspl']}×1:16)" if is_cab else '│ ' + cab['id'], True if is_cab else False, True,
                     bg=bg if is_cab else None, color='000000' if is_cab else '808080')
        if not is_cab: tcell.fill = fill(hue(ci, len(tcabs), 0.35, 0.95))
        body(wsD, r, c0 + 5, M.HOMES_PER_FLOOR[t][fl], center=True)
        pons = sorted({s['pon'] for s in spls if s['cab'] == cab['id']})
        body(wsD, r, c0 + 6, ('PON-' + ','.join(f'{p:02d}' for p in pons)) if is_cab else '', center=True, bg=bg if is_cab else None)
        body(wsD, r, c0 + 7, f"{cab['homes']} hộ" if is_cab else '', center=True, bg=bg if is_cab else None)
    r = 6 + len(M.FLOORS)
    wsD.merge_cells(start_row=r, start_column=c0, end_row=r, end_column=c0 + 7)
    x = wsD.cell(row=r, column=c0, value='◄ PHÒNG MÁY (tầng 2): ODF + 16 splitter 1:4 + OLT 16 PON')
    x.font = Font(name=F, bold=True, color='FFFFFF'); x.fill = fill('44546A'); x.alignment = Alignment(horizontal='center')
    for k, tr in enumerate(tr_list):
        wsD.cell(row=r + 1, column=c0 + 1 + k, value=tr['id'][3:]).font = Font(name=F, size=8, bold=True, color=trunk_colors[k])
        wsD.cell(row=r + 1, column=c0 + 1 + k).alignment = Alignment(horizontal='center')
for rr in range(6, 6 + len(M.FLOORS)): wsD.row_dimensions[rr].height = 18
wsD.cell(row=6 + len(M.FLOORS) + 3, column=2, value='Chú giải: ● = tủ trên trục; 3 màu xanh/cam/lục = 3 cáp trục 24FO của mỗi tháp (mỗi cáp chia 3×8FO cho 3 tủ). Tầng 13 không có (12A thay thế).').font = Font(name=F, size=9, italic=True)

# =============== TỔNG QUAN ===============
title(wsT, 'Hệ thống phối quang FTTH – Chung cư Phố Đông (Tháp A + B)', 'Kiến trúc: ONU căn hộ ─1FO─ Splitter 1:16 (tủ) ─ cáp trục 24FO (8FO/tủ) ─ ODF PM ─ Splitter 1:4 ─ PON  ⇒  1:64 / PON')
widths(wsT, [3, 26, 14, 14, 14, 14, 14, 14, 14, 26, 14])
kpi = [('Tổng căn hộ', f'=COUNTA({HR("A")})'), ('Hoạt động', f'=COUNTIF({HR("N")},"Hoạt động")'),
       ('Đã đấu nối', f'=COUNTIF({HR("N")},"Đã đấu nối")'), ('Sự cố', f'=COUNTIF({HR("N")},"Sự cố")'),
       ('Số tủ', f'=COUNTA({q(S_TU)}!A5:A21)'), ('Splitter 1:16', f"={q(S_TU)}!F22"),
       ('Cổng 1:4 dùng / 64', f'=COUNTIF({OR("J")},"Đã dùng")'), ('Margin quang (dB)', f"={q(S_QC)}!E27")]
for i, (k, v) in enumerate(kpi):
    r, c = 4 + (i // 4) * 3, 2 + (i % 4) * 2
    wsT.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + 1)
    wsT.merge_cells(start_row=r + 1, start_column=c, end_row=r + 1, end_column=c + 1)
    a = wsT.cell(row=r, column=c, value=k); a.font = Font(name=F, size=9, color='5B6573'); a.fill = fill(LIGHT); a.alignment = Alignment(horizontal='center')
    wsT.cell(row=r, column=c + 1).fill = fill(LIGHT)
    b = wsT.cell(row=r + 1, column=c, value=v); b.font = Font(name=F, size=18, bold=True, color=NAVY); b.fill = fill(LIGHT); b.alignment = Alignment(horizontal='center')
    wsT.cell(row=r + 1, column=c + 1).fill = fill(LIGHT)
    wsT.row_dimensions[r + 1].height = 30
wsT['H8'].number_format = '0.0'
header(wsT, 11, ['PON', 'Splitter 1:4', 'Nhánh dùng', 'Căn hộ', 'Hoạt động', 'Tải thiết kế / 64', 'Cảnh báo'], col0=2, h=30)
for p in range(1, M.N_PON + 1):
    r = 11 + p
    body(wsT, r, 2, f'PON-{p:02d}', True, True); body(wsT, r, 3, f'S4-{p:02d}', center=True)
    body(wsT, r, 4, f"=COUNTIFS({OR('A')},B{r},{OR('J')},\"Đã dùng\")", center=True)
    body(wsT, r, 5, f"=COUNTIF({HR('M')},B{r})", center=True)
    body(wsT, r, 6, f"=COUNTIFS({HR('M')},B{r},{HR('N')},\"Hoạt động\")", center=True)
    body(wsT, r, 7, f"=E{r}/{q(S_QC)}!$C$6", center=True, fmt='0%')
    body(wsT, r, 8, f'=IF(E{r}=0,"Trống",IF(G{r}>0.9,"Gần đầy","OK"))', center=True)
wsT.conditional_formatting.add('G12:G27', DataBarRule(start_type='num', start_value=0, end_type='num', end_value=1, color='5B9BD5'))
wsT.conditional_formatting.add('H12:H27', CellIsRule(operator='equal', formula=['"Gần đầy"'], fill=fill('FFC7CE')))
wsT.conditional_formatting.add('H12:H27', CellIsRule(operator='equal', formula=['"Trống"'], fill=fill('EDEDED')))
body(wsT, 28, 2, 'Tổng', True, True)
for c in (3, 7, 8): body(wsT, 28, c, None)
for c, col in [(4, 'D'), (5, 'E'), (6, 'F')]: body(wsT, 28, c, f'=SUM({col}12:{col}27)', True, True)
# bảng tháp
header(wsT, 11, ['Tháp', 'Căn hộ', 'Hoạt động'], col0=10, h=30)
for i, t in enumerate('AB'):
    r = 12 + i
    body(wsT, r, 10, f'Tháp {t}', True, True)
    body(wsT, r, 11, f'=COUNTIF({HR("B")},"{t}")', center=True); body(wsT, r, 12, f'=COUNTIFS({HR("B")},"{t}",{HR("N")},"Hoạt động")', center=True)
wsT.column_dimensions['L'].width = 12
wsT['J16'] = 'Cách dùng nhanh'; wsT['J16'].font = Font(name=F, bold=True, color=NAVY)
for i, t in enumerate(['1. Tra đường quang 1 căn hộ → sheet "Tra cứu".', '2. Khách mới: tìm căn hộ ở "Thuê bao", đổi Trạng thái,',
                       '    ghi serial ONU. Dashboard tự cập nhật.', '3. Mất tín hiệu hàng loạt → xem "Vận hành" (cây xử lý sự cố).',
                       '4. Xem hình tổng thể → mở file ftth_viewer.html.']):
    wsT.cell(row=17 + i, column=10, value=t).font = Font(name=F, size=10)

# =============== TRA CỨU ===============
title(wsS, 'Tra cứu đường quang', 'Chọn mã căn hộ ở ô vàng (gõ hoặc chọn từ danh sách).')
widths(wsS, [3, 30, 40, 4, 22, 14, 14, 14, 14])
body(wsS, 4, 2, 'MÃ CĂN HỘ', True); c = body(wsS, 4, 3, 'A-18-05', True, True, bg='FFF2A8'); 
dv2 = DataValidation(type='list', formula1=f"={q(S_TB)}!$A$2:$A${H1}", allow_blank=False); wsS.add_data_validation(dv2); dv2.add('C4')
m = f"MATCH($C$4,{HR('A')},0)"
items = [('Tháp', 'B'), ('Tầng', 'C'), ('Căn', 'D'), ('Tủ phối quang', 'E'), ('Splitter 1:16 tại tủ', 'F'), ('Cổng splitter', 'G'),
         ('Cáp trục', 'H'), ('Sợi trục', 'I'), ('Màu sợi', 'J'), ('Splitter PM 1:4', 'K'), ('Cổng ra 1:4', 'L'), ('PON', 'M'), ('Trạng thái', 'N'), ('Serial / Ghi chú', 'O'), ('Đường quang', 'Q')]
for i, (lab, col) in enumerate(items):
    r = 5 + i
    body(wsS, r, 2, lab); body(wsS, r, 3, f'=IFERROR(INDEX({HR(col)},{m})&"","Không tìm thấy")', True)
wsS.merge_cells(start_row=4, start_column=5, end_row=4, end_column=9)
x = wsS.cell(row=4, column=5, value='TỦ → SPLITTER'); x.font = Font(name=F, bold=True, color='FFFFFF'); x.fill = fill(NAVY); x.alignment = Alignment(horizontal='center')
body(wsS, 5, 5, 'Chọn tủ:', True); body(wsS, 5, 6, 'TU-A18', True, True, bg='FFF2A8')
dv3 = DataValidation(type='list', formula1=f"={q(S_TU)}!$A$5:$A$21", allow_blank=False); wsS.add_data_validation(dv3); dv3.add('F5')
header(wsS, 6, ['Splitter', 'Căn hộ', 'Hoạt động', 'Còn trống', 'PON'], col0=5, h=22)
for s in range(1, M.CAB_SLOTS + 1):
    r = 6 + s
    body(wsS, r, 5, f'=$F$5&"/S{s}"', center=True)
    body(wsS, r, 6, f"=COUNTIF({HR('F')},E{r})", center=True)
    body(wsS, r, 7, f"=COUNTIFS({HR('F')},E{r},{HR('N')},\"Hoạt động\")", center=True)
    body(wsS, r, 8, f'=IF(F{r}=0,"chưa lắp",{M.SPL_CAB}-F{r})', center=True)
    body(wsS, r, 9, f"=IFERROR(INDEX({HR('M')},MATCH(E{r},{HR('F')},0))&\"\",\"—\")", center=True)

# =============== VẬT TƯ ===============
title(wsV, 'Dự toán vật tư (ước tính – chỉnh tham số xanh nhạt)', 'Chiều dài chỉ là ước tính theo chiều cao tầng; cần đo thực tế.')
widths(wsV, [3, 42, 12, 12, 38])
header(wsV, 3, ['Tham số', 'Giá trị', '', 'Ghi chú'], col0=2, h=22)
for i, (a, b, c) in enumerate([('Chỉ số tầng Phòng Máy', M.fidx(M.PM_FLOOR), 'tầng 2'), ('Chiều cao tầng (m)', 3.3, ''),
                               ('Đi ngang trong tầng kỹ thuật (m)', 40, 'mỗi cáp'), ('Dự phòng chiều dài (%)', 0.15, ''),
                               ('Chiều dài TB cáp 1FO/căn hộ (m)', 35, 'căn hộ → tủ')]):
    r = 4 + i; body(wsV, r, 2, a); body(wsV, r, 3, b, center=True, bg=LIGHT, fmt='0%' if i == 3 else None); body(wsV, r, 4, None); body(wsV, r, 5, c)
header(wsV, 10, ['Cáp trục / nhánh', 'Loại', 'Chiều dài (m)', 'Ghi chú'], col0=2, h=22)
r = 11
for t in trunks:
    hub_idx = M.fidx(t['hub'])
    body(wsV, r, 2, f"{t['id']} (PM → tủ hub {t['hub']}F)"); body(wsV, r, 3, '24FO', center=True)
    body(wsV, r, 4, f"=ROUNDUP((({hub_idx}-$C$4)*$C$5+$C$6)*(1+$C$7),0)", center=True); body(wsV, r, 5, 'Cáp trục chính'); r += 1
for t in trunks:
    hub = t['cabs'][-1]
    for cid in t['cabs'][:-1]:
        d = M.fidx(cab_by[cid]['floor']) - M.fidx(cab_by[hub]['floor'])
        body(wsV, r, 2, f'{cid} → {hub}'); body(wsV, r, 3, '8FO', center=True)
        body(wsV, r, 4, f"=ROUNDUP(({d}*$C$5+10)*(1+$C$7),0)", center=True); body(wsV, r, 5, 'Cáp nhánh trong hộp kỹ thuật'); r += 1
VE = r - 1
r += 1
header(wsV, r, ['Hạng mục', 'Số lượng', 'Đơn vị', 'Ghi chú'], col0=2, h=22); r += 1
bom = [('Tủ phối quang (4 vị trí splitter)', f"=COUNTA({q(S_TU)}!A5:A21)", 'tủ', ''),
       ('Splitter 1:16 PLC (lắp ngay)', f"={q(S_TU)}!F22", 'bộ', ''),
       ('Splitter 1:16 PLC (dự phòng 1 vị trí/tủ)', f"={q(S_TU)}!G22", 'bộ', 'tùy chọn mua sau'),
       ('Splitter 1:4 PLC (PM)', M.N_PON, 'bộ', 'khay rack 19"'),
       ('Cáp quang 24FO', f'=SUMIF($C$11:$C${VE},"24FO",$D$11:$D${VE})', 'm', ''),
       ('Cáp quang 8FO', f'=SUMIF($C$11:$C${VE},"8FO",$D$11:$D${VE})', 'm', ''),
       ('Cáp thuê bao 1FO (drop)', f"=COUNTA({HR('A')})*$C$8", 'm', 'tính theo TB / căn hộ'),
       ('ODF 144FO (PM) hoặc 6×ODF 24FO', 6, 'bộ', '1 ODF/cáp trục 24FO'),
       ('Patch cord SC/APC (PM: PON↔1:4 + 1:4↔ODF)', f"={M.N_PON}+COUNTIF({OR('J')},\"Đã dùng\")", 'sợi', ''),
       ('Pigtail SC/APC (đầu trục + tại tủ + thuê bao)', f"=144+COUNTA({q(S_TU)}!A5:A21)*{M.CAB_SLOTS}*2+COUNTA({HR('A')})", 'sợi', 'ước tính thô'),
       ('Mối hàn (ước tính)', f"=C{r + 9}", 'mối', 'tính xấp xỉ bằng số pigtail'),
       ('Nhãn cáp/tủ/cổng', 800, 'cái', '')]
for a, b, c_, d in bom:
    body(wsV, r, 2, a); body(wsV, r, 3, b, center=True, fmt='#,##0'); body(wsV, r, 4, c_, center=True); body(wsV, r, 5, d); r += 1

# =============== VẬN HÀNH ===============
title(wsG, 'Quy ước & quy trình vận hành')
widths(wsG, [3, 120])
text = [
 ('QUY ƯỚC ĐẶT TÊN', None),
 ('Căn hộ: <Tháp>-<Tầng>-<Căn>  vd A-18-05.  Tủ: TU-<Tháp><Tầng> vd TU-A18.  Splitter 1:16: TU-A18/S2.  Cáp trục: TR-A1 (3 cáp/tháp).', 1),
 ('PM: PON-01…16 ↔ splitter 1:4 "S4-01…16" ↔ cổng ODF "TR-A1/07" (cáp/sợi).  Ghi nhãn cả 2 đầu mọi sợi và mọi cổng.', 1),
 ('Màu sợi (TIA-598): 1 Xanh dương, 2 Cam, 3 Xanh lá, 4 Nâu, 5 Xám, 6 Trắng, 7 Đỏ, 8 Đen, 9 Vàng, 10 Tím, 11 Hồng, 12 Xanh ngọc; 13-24 lặp lại ở ống đệm cam.', 1),
 ('Cáp trục 24FO tại tủ hub: sợi 1-8 → tủ trên cùng (cáp nhánh 8FO), 9-16 → tủ giữa, 17-24 → tủ hub. Trong mỗi tủ, splitter Sk dùng sợi thứ k trong dải của tủ.', 1),
 ('QUY TRÌNH CẤP MỚI 1 KHÁCH', None),
 ('1) Tra căn hộ ở sheet "Tra cứu" → biết tủ, splitter, cổng.   2) Kéo 1FO từ BOX căn hộ về tủ, đấu vào đúng cổng splitter, dán nhãn mã căn hộ.', 1),
 ('3) Đo công suất tại ONU (-8…-27 dBm).   4) Cập nhật Trạng thái = Hoạt động, ghi serial ONU, ngày lắp.   5) Kiểm tra % tải PON ở Tổng quan (<90%).', 1),
 ('XỬ LÝ SỰ CỐ (từ trên xuống)', None),
 ('• Mất 1 căn hộ: kiểm tra ONU/dây nhảy → cổng splitter tủ → cáp 1FO.', 1),
 ('• Mất cả 1 splitter (≤16 hộ, cùng cổng PON-xx/S4-yy/z): sợi trục của splitter đó, adapter ODF PM hoặc patch cord 1:4→ODF.', 1),
 ('• Mất cả 1 tủ (khoảng 28-42 hộ): sợi cáp nhánh 8FO / mối hàn ở hub.  Mất cả 1 cụm 3 tủ (~112-126 hộ): cáp trục 24FO TR-xx.', 1),
 ('• Mất toàn bộ 1 PON (≤64 hộ, nhiều tủ khác nhau): SFP/cổng OLT hoặc splitter 1:4 tương ứng.', 1),
 ('• Công cụ: OPM (đo công suất), VFL (tìm đứt/uốn), OTDR từ PM với tia 1310/1550 qua splitter thì đo từng nhánh, bắt đầu từ ODF.', 1),
 ('GIẢ ĐỊNH CẦN XÁC NHẬN (sửa trong model.py rồi chạy lại)', None),
 ('• 14 căn hộ/tầng/tháp (bản vẽ ghi "x14"); tầng 1-2 có thể có shophouse – cập nhật số thực tế.   • Mã căn hộ A-18-05 do mình đặt; thay bằng mã thật nếu có.', 1),
 ('• Tủ đặt ở tầng cao nhất của cụm và phục vụ các tầng bên dưới (theo sổ tay).   • Mỗi tủ lắp 3 splitter 1:16, còn 1 vị trí dự phòng; tủ 28 hộ vẫn lắp 3 để chia tải đều.', 1),
 ('• Phòng máy ở tầng 2; tầng 13 không có (12A).   • Thuê bao sau này cần >1FO/căn: dùng 4 cổng dự phòng/splitter (≈6 cổng trống mỗi splitter).', 1),
]
r = 3
for t_, lvl in text:
    c = wsG.cell(row=r, column=2, value=t_)
    if lvl is None:
        c.font = Font(name=F, bold=True, color='FFFFFF'); c.fill = fill(NAVY); r += 1
    else:
        c.font = Font(name=F, size=10); c.alignment = Alignment(wrap_text=True, vertical='top'); wsG.row_dimensions[r].height = 30; r += 1

for ws, col in [(wsT, NAVY), (wsD, '2F6FDE'), (wsC, '2F6FDE'), (wsK, '2F6FDE'), (wsO, '2F6FDE'), (wsH, '1E9E5A'), (wsS, 'E8710A'), (wsQ, '8E44AD'), (wsV, '8E44AD'), (wsG, '8C959F')]:
    ws.sheet_properties.tabColor = col
wsD.sheet_view.zoomScale = 90
for ws in (wsT, wsD, wsC, wsK, wsO, wsH, wsS, wsQ, wsV, wsG):
    ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
wb.save('FTTH_PhoDong_PhoiQuang.xlsx')
print('ok')
