"""Trích dữ liệu từ các file nguồn người dùng ghi tay thành CSV/JSON trong data/.
Chạy: python3 -I extract_sources.py <thư_mục_chứa_file_nguồn>   (tên file như bản tải lên)
Các file nguồn là ghi chú thủ công — script chỉ trích nguyên văn, không sửa."""
import csv,glob,json,math,os,re,sys
import xml.etree.ElementTree as ET
import openpyxl

SRC=sys.argv[1];OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'data')
def find(pat):return glob.glob(os.path.join(SRC,pat))[0]
def w(name,header,rows):
    with open(os.path.join(OUT,name),'w',newline='',encoding='utf-8') as f:
        c=csv.writer(f);c.writerow(header);c.writerows(rows)

# ---------- KML: nút, MX, đường ----------
K='{http://www.opengis.net/kml/2.2}'
kml=ET.parse(find('*Nha_Be.xml')).getroot()
nm=lambda e:(e.find(K+'name').text or '').strip() if e.find(K+'name') is not None else ''
def pts(pm):return [tuple(map(float,x.split(',')[:2])) for x in pm.find('.//'+K+'coordinates').text.split()]
nodes={};kmx=[];lines={}
for f in kml.iter(K+'Folder'):
    if nm(f)=='Tap Diem':
        for pm in f.findall(K+'Placemark'):nodes[nm(pm)]=pts(pm)[0]
    if nm(f)=='MX':
        for pm in f.findall(K+'Placemark'):kmx.append((nm(pm),pts(pm)[0]))
    if nm(f)=='Tuyen lastmile':
        for sf in f.findall(K+'Folder'):
            for pm in sf.findall(K+'Placemark'):lines[nm(sf)+'|'+nm(pm)]=pts(pm)
json.dump(lines,open(os.path.join(OUT,'kml_lines.json'),'w'))
w('kml_mx_points.csv',['ten_kml','lon','lat'],[(n,c[0],c[1]) for n,c in kmx])

# ---------- BBNT: địa chỉ nút (từ bảng tuyến đã trích tay trong bbnt_segments.csv không có địa chỉ) ----------
# địa chỉ lấy từ ODF/MX nếu có; ở đây chỉ ghi toạ độ KML
def norm(n):
    n=n.upper();m=re.findall(r'\d+',n)[-1]
    return ('NBE'+m) if ('NBE' in n or n.startswith('AGG')) else 'HNB'+m.zfill(3)
w('nodes.csv',['id','loai','lon','lat'],[(norm(n),'AGG' if 'AGG' in n else 'CSG',c[0],c[1]) for n,c in sorted(nodes.items())])

# ---------- Độ dài cáp (Tổng Hợp) ----------
wb=openpyxl.load_workbook(find('*Nha__Be*.xlsx'),data_only=True);ws=wb['Tổng Hợp']
rows=[]
for r in range(2,ws.max_row+1):
    a,b=ws.cell(r,2).value,ws.cell(r,3).value
    if not a or not b:continue
    g=lambda c:ws.cell(r,c).value
    rows.append((str(a).strip(),str(b).strip(),g(4),g(5),g(6),g(7),g(12),g(13)))
w('cap_tong_hop.csv',['dau','cuoi','cs_dau','cs_cuoi','ma_cap','so_FO','dai_m','ghi_chu'],rows)
ws=wb['Sheet2']
w('vat_tu_odf_mx.csv',['loai','stt','ten_mx','dau_cap','thiet_ke_hoac_phat_sinh','ghi_chu'],
  [('mx_thiet_ke',ws.cell(r,1).value,ws.cell(r,2).value,ws.cell(r,3).value,ws.cell(r,4).value,ws.cell(r,5).value) for r in range(9,44) if ws.cell(r,2).value]+
  [('mx_phat_sinh',ws.cell(r,7).value,ws.cell(r,8).value,ws.cell(r,9).value,ws.cell(r,10).value,ws.cell(r,11).value) for r in range(9,18) if ws.cell(r,8).value])

# ---------- ODF CSG ----------
wb=openpyxl.load_workbook(find('*ODF.xlsx'));ws=wb['ODF CSG']
M={}
for m in ws.merged_cells.ranges:
    for r in range(m.min_row,m.max_row+1):
        for c in range(m.min_col,m.max_col+1):M[(r,c)]=(m.min_row,m.min_col)
val=lambda r,c:ws.cell(*M.get((r,c),(r,c))).value
odf=None;out=[]
for r in range(1,ws.max_row+1):
    b=ws.cell(r,2).value
    if isinstance(b,str) and b.startswith('ODF-'):odf=b.strip()
    p=ws.cell(r,4).value
    if odf and isinstance(p,int):
        note=val(r,6);note=(note or '').replace('\n',' / ').strip()
        out.append((odf,p,(val(r,5) or ''),note))
w('odf_csg.csv',['odf','cong','nhan_E','ghi_chu_goc'],out)
# ---------- ODF AGG ----------
ws=wb['ODF AGG'];M={}
for m in ws.merged_cells.ranges:
    for r in range(m.min_row,m.max_row+1):
        for c in range(m.min_col,m.max_col+1):M[(r,c)]=(m.min_row,m.min_col)
out=[]
for side,cols,name_col in (('trai',dict(p=4,dest=5,F=6,G=7,I=9,note=10,extra=None),2),('phai',dict(p=14,dest=16,F=17,G=18,I=19,note=22,extra=15),12)):
    odf=None
    for r in range(3,52):
        nb=val(r,name_col)
        if isinstance(nb,str) and nb.startswith('ODF'):odf=nb.replace('\n',' / ')
        p=ws.cell(r,cols['p']).value
        if not isinstance(p,int):continue
        g=lambda k:'' if cols[k] is None else (val(r,cols[k]) if val(r,cols[k]) is not None else '')
        out.append((side,odf,p,str(g('extra')),str(g('dest')).replace('\n',' / '),g('F'),g('G'),g('I'),str(g('note')).replace('\n',' / '),ws.cell(r,20).value if side=='phai' else '',ws.cell(r,21).value if side=='phai' else ''))
w('odf_agg.csv',['phia','odf','cong','cot_O','dich','cot1','cot2','cot3','ghi_chu','cot_T','cot_U'],out)

# ---------- Măng xông ----------
wb=openpyxl.load_workbook(find('*MX__NHA_BE.xlsx'),data_only=True)
out=[]
ws=wb['MX']
for m in ws.merged_cells.ranges:
    v=ws.cell(m.min_row,m.min_col).value
    if isinstance(v,str) and re.match(r'[\s/]*MX_',v):
        t=v.replace('\n',' / ').strip(' /')
        mm=re.search(r'\((\d+\.\d+),\s*(\d+\.\d+)\)',t)
        out.append((t.split(':')[0].strip(),t,mm.group(1) if mm else '',mm.group(2) if mm else '','MX'))
ws=wb['MX thẳng']
for r in range(1,ws.max_row+1):
    v=ws.cell(r,5).value
    if isinstance(v,str) and v.startswith('Vị Trí'):
        t=v.replace('\n',' / ');mm=re.search(r'(\d+\.\d+),\s*(\d+\.\d+)',t)
        name=ws.cell(r-1,5).value or ''
        out.append((str(name),t,mm.group(1) if mm else '',mm.group(2) if mm else '','MX thang'))
w('mx_dang_ky.csv',['ten','mo_ta','lat','lon','sheet'],out)
print('OK',len(out),'MX')
