"""Đọc bảng nghiệm thu cổng ODF (cap_core_nghiem_thu.xlsx) -> data/odf_nghiem_thu.json.
Mỗi dòng một link: ODF + cặp cổng hai đầu, km và suy hao nghiệm thu. Cổng ODF CSG lấy theo bảng này (thực tế thi công);
hai đầu AGG có thể đã thay đổi nên chỉ để đối chiếu. Chạy: python3 -I import_nghiem_thu.py <file.xlsx>"""
import openpyxl,json,re,os,sys
def main(path):
    ws=openpyxl.load_workbook(path,data_only=True).active;out=[]
    f=lambda v:float(v) if v not in(None,'') else None
    for r in ws.iter_rows(min_row=2,values_only=True):
        if not r[0]:continue
        names=re.findall(r'(?:HCM)?(NBE\d+|HNB\d+)',str(r[0]))
        out.append(dict(stt=int(r[1]),frm=names[0],to=names[1],odf_frm=str(r[6]).strip(),ports_frm=[int(r[7]),int(r[8])],odf_to=str(r[11]).strip(),ports_to=[int(r[12]),int(r[13])],km=f(r[14]),db1=f(r[15]),db2=f(r[16])))
    p=os.path.join(os.path.dirname(os.path.abspath(__file__)),'data','odf_nghiem_thu.json')
    json.dump(out,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1);print('đã ghi',len(out),'dòng ->',p)
if __name__=='__main__':main(sys.argv[1])
