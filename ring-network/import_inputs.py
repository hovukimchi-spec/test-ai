"""Đọc lại các ô nhập tay trong ring_network_NhaBe.xlsx (sheet 'Nhập mã cáp', 'Nhập nhãn MX') vào data/overrides.json.
Sau đó chạy: python3 build_xlsx.py && python3 build_html.py  để dựng lại Excel + HTML.
Chạy: python3 import_inputs.py <file.xlsx>
Ô trống = giữ nguyên; override được cộng dồn qua các lần chạy."""
import json,os,sys
import openpyxl
HERE=os.path.dirname(os.path.abspath(__file__));P=os.path.join(HERE,'data','overrides.json')
ov=json.load(open(P,encoding='utf-8')) if os.path.exists(P) else {}
wb=openpyxl.load_workbook(sys.argv[1],data_only=True)
n1=n2=0
if 'Nhập mã cáp' in wb.sheetnames:
    ws=wb['Nhập mã cáp'];cab=ov.setdefault('cables',{})
    for r in range(5,ws.max_row+1):
        cid=ws.cell(r,1).value
        if not cid:continue
        for col,key in ((6,'ma_cap'),(7,'cs_dau'),(8,'cs_cuoi'),(9,'len_m')):
            v=ws.cell(r,col).value
            if v not in (None,''):
                if key=='len_m':v=int(float(v))
                cab.setdefault(cid,{})[key]=str(v).strip() if key!='len_m' else v;n1+=1
if 'Nhập nhãn MX' in wb.sheetnames:
    ws=wb['Nhập nhãn MX'];rows=ov.setdefault('mx_labels',[])
    key=lambda x:(x['mx'],x['cable'],x['core'])
    cur={key(x):x for x in rows}
    for r in range(5,ws.max_row+1):
        mx,cab,core,prop,tram,chot,nhap=[ws.cell(r,c).value for c in (1,2,4,5,6,7,8)]
        if not mx or not (chot or nhap):continue
        lab=(str(nhap).strip() if nhap else prop)
        cur[(mx,cab,int(core))]=dict(mx=mx,cable=cab,core=int(core),nhan=lab,tram=tram or '');n2+=1
    ov['mx_labels']=list(cur.values())
json.dump(ov,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('đã nhập',n1,'ô cáp,',n2,'dòng nhãn MX ->',P)
