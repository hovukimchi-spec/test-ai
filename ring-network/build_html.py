"""Dựng ring_network_viewer.html (một file, offline, không thư viện). Chạy: python3 build_html.py"""
import os,sys,json
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
import model
d=model.build()
segs=[]
for s in d['segments']:
    x={k:s[k] for k in('id','ring','seq','bbnt','a','z','kind','km_hd','km_otdr','km_kml','db1','db2','km_ref','db_ref','allow','delta','margin','roadside','rerouted')}
    x['polyline']=[[round(a,5),round(b,5)] for a,b in s['polyline']]
    if s['db_ref'] is None:x['status']='Chưa đo'
    else:x['status']='Đạt' if s['ok_loss'] and s['ok_core'] else 'Cảnh báo'
    segs.append(x)
nodes={k:{kk:v[kk] for kk in('id','type','lat','lon','ring','role') if kk in v} for k,v in d['nodes'].items()}
rings={k:dict(csg=v['csg'],segs=v['segs']) for k,v in d['rings'].items()}
odf=[{k:o[k] for k in('node','port','dest','cable')} for o in d['odf']]
data=dict(segments=segs,nodes=nodes,rings=rings,odf=odf,closures=[{k:c[k] for k in('name','straight','lat','lon','desc')} for c in d['closures']],
          issues=[list(i) for i in d['issues']],fix=[
 ['CSG mất một hướng','Đứt/hỏng một đoạn kề','OTDR từ đầu trạm, đổi sang vị trí (tab OTDR → vị trí); báo thi công; theo dõi hướng còn lại'],
 ['CSG mất cả hai hướng','Hai đoạn cùng ring đứt cùng lúc hoặc trạm nhánh cụt','Dùng nút Giả lập sự cố để xác định; ưu tiên khôi phục đoạn có CSG cô lập'],
 ['Suy hao một đoạn cao','Uốn cong, mối hàn xấu, đầu nối bẩn','OTDR hai chiều, vệ sinh đầu nối ODF, kiểm tra khay hàn MX gần nhất'],
 ['Lệch hai core > 2 dB','Một core có mối hàn/đầu nối xấu','So sánh OTDR từng core (đoạn R2-02 đang chênh 2,02 dB)'],
 ['OTDR khác hẳn KML/hợp đồng','Đổi tuyến, dự trữ lớn hoặc ghi sai','Cập nhật tuyến thực tế (HNB066, HNB005 đã đổi tuyến)']])
tpl=open(os.path.join(HERE,'viewer_template.html'),encoding='utf-8').read()
out=os.path.join(HERE,'ring_network_viewer.html')
open(out,'w',encoding='utf-8').write(tpl.replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':'))))
print('saved',out,os.path.getsize(out)//1024,'KB')
