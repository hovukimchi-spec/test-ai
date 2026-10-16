"""Đọc lại lớp dữ liệu sửa được trong ring_network_NhaBe.xlsx (4 sheet DL_Cáp, DL_Link, DL_Bước, DL_Nhãn MX — cũng là
những sheet mà ring_network_viewer.html mở/lưu) và ghi vào data/cables.json, data/paths/Rn.json, data/overrides.json.
Sau đó chạy: python3 build_xlsx.py && python3 build_html.py   để dựng lại toàn bộ Excel + HTML.
Chạy: python3 import_inputs.py <file.xlsx>"""
import json,os,sys
import openpyxl
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from export_data import layer_to_data
def sheet(wb,name):
    ws=wb[name];rows=list(ws.iter_rows(values_only=True));h=[str(x) for x in rows[0]]
    return [dict(zip(h,r)) for r in rows[1:] if any(v not in(None,'') for v in r)]
def main(path):
    wb=openpyxl.load_workbook(path,data_only=True)
    L=dict(cables=sheet(wb,'DL_Cáp'),links=sheet(wb,'DL_Link'),steps=sheet(wb,'DL_Bước'),labels=sheet(wb,'DL_Nhãn MX'))
    cables,rings,labels=layer_to_data(L,None)
    D=os.path.join(HERE,'data')
    json.dump(cables,open(os.path.join(D,'cables.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for rid,links in rings.items():
        p=os.path.join(D,'paths',rid+'.json');meta=json.load(open(p,encoding='utf-8'))
        meta['links']=links;json.dump(meta,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(dict(mx_labels=labels),open(os.path.join(D,'overrides.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print('đã nhập',len(cables),'cáp,',sum(len(v) for v in rings.values()),'link,',len(L['steps']),'bước,',len(labels),'dòng nhãn MX')
if __name__=='__main__':main(sys.argv[1])
