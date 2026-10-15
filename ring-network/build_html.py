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
cab={c['cap_id']:c for c in d['mx_cables']}
def cn(i):
    c=cab[i];return f"{c['o_goc']} {(c['ma_cap']+' ') if c['ma_cap'] else ''}{c['so_FO']}FO→{c['huong'] or '?'}"
def rng_(xs):
    xs=sorted(xs);out=[];st=pv=xs[0]
    for x in xs[1:]+[None]:
        if x is not None and x==pv+1:pv=x;continue
        out.append(f'{st}' if st==pv else f'{st}–{pv}')
        if x is not None:st=pv=x
    return ','.join(out)
mxd={}
for p in d['mx_pairs']:
    mxd.setdefault(p['mx'],{}).setdefault((p['label'],p['a'],p['b']),[]).append(p)
mxs={}
for m,g in mxd.items():
    rows=[]
    for (lab,a,b),ps in g.items():
        rows.append([lab,cn(a),rng_([p['core_a'] for p in ps]),cn(b),rng_([p['core_b'] for p in ps]),', '.join(sorted({p['station'] for p in ps if p['station']}))])
    mxs[m]=rows
mxcab={}
for c in d['mx_cables']:mxcab.setdefault(c['mx'],[]).append([c['o_goc'],cn(c['cap_id']),c['so_core_co_nhan']+'/'+c['so_core_ve']])
links={}
for lk in d['paths']:
    links[lk['id']]=dict(frm=lk['frm'],to=lk['to'],total=lk['total_m'],ref=lk['ref_m'],steps=[
      [s['cable'],s['name'],d['phys_cables'][s['cable']]['ma_cap'],s['cores'],s['len_m'],s['frm'],s['to']] for s in lk['steps'] if s['t']=='cable'])
cprof=[{k:p[k] for k in('id','ma_cap','fo','frm','to','len_m','cs_dau','cs_cuoi','run','hu','lab','lab_stations','free','effect')} for p in d['cable_profiles']]
data=dict(links=links,cprof=cprof,mxpairs=mxs,mxcab=mxcab,segments=segs,nodes=nodes,rings=rings,odf=odf,closures=[{k:c[k] for k in('name','straight','lat','lon','desc')} for c in d['closures']],
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
