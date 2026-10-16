"""Xuất dữ liệu cho HTML (RAW = nền tĩnh + lớp sửa được) và kết quả kỳ vọng để kiểm thử động cơ JS.
Lớp sửa được (layer) có cùng cấu trúc với các sheet DL_* trong Excel."""
import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import model
HERE=model.HERE;DATA=model.DATA

FIX=[
 ['CSG mất một hướng','Đứt/hỏng một đoạn kề','OTDR từ đầu trạm, đổi sang vị trí (tab OTDR → vị trí); báo thi công; theo dõi hướng còn lại'],
 ['CSG mất cả hai hướng','Hai đoạn cùng ring đứt cùng lúc hoặc trạm nhánh cụt','Dùng nút Giả lập sự cố để xác định; ưu tiên khôi phục đoạn có CSG cô lập'],
 ['Suy hao một đoạn cao','Uốn cong, mối hàn xấu, đầu nối bẩn','OTDR hai chiều, vệ sinh đầu nối ODF, kiểm tra khay hàn MX gần nhất'],
 ['Lệch hai core > 2 dB','Một core có mối hàn/đầu nối xấu','So sánh OTDR từng core (đoạn R2-02 đang chênh 2,02 dB)'],
 ['OTDR khác hẳn KML/hợp đồng','Đổi tuyến, dự trữ lớn hoặc ghi sai','Cập nhật tuyến thực tế (HNB066, HNB005 đã đổi tuyến)']]

def layer(d):
    cables=[]
    for c in d['phys_cables'].values():
        cables.append(dict(id=c['id'],name=c['name'],fo=c['fo'],frm=c['frm'],to=c['to'],len_m=c['len_m'],so_row=c.get('so_row') or '',ma_cap=c['ma_cap'],
                           cs_dau=c['cs_dau'],cs_cuoi=c['cs_cuoi'],src=c['src'],so_dau_cuoi=c.get('so_dau_cuoi',''),ends='; '.join(f'{k}={v}' for k,v in c['ends'].items())))
    links=[];steps=[]
    for f in sorted(os.listdir(os.path.join(DATA,'paths'))):
        if not f.endswith('.json'):continue
        P=json.load(open(os.path.join(DATA,'paths',f),encoding='utf-8'))
        for lk in P['links']:
            links.append(dict(id=lk['id'],ring=P['ring'],frm=lk['frm'],to=lk['to'],odf_otdr_m='/'.join(map(str,lk.get('odf_otdr_m') or [])),bbnt_otdr_m=lk.get('bbnt_otdr_m') or '',
                              rerouted=1 if lk.get('rerouted') else 0,complete=0 if lk.get('complete') is False else 1,design_cables=','.join(lk.get('design_cables',[])),note=lk.get('note','')))
            for i,st in enumerate(lk['steps'],1):
                row=dict(link=lk['id'],seq=i,t=st['t'],at=st.get('at',''),name=st.get('name',''),cable=st.get('cable',''),cores=','.join(map(str,st.get('cores',[]))),odf_ref=st.get('odf_ref',''),
                         note=st.get('note',''),a_cable=st.get('a_cable',''),cores_a=','.join(map(str,st.get('cores_a',[]))),b_cable=st.get('b_cable',''),cores_b=','.join(map(str,st.get('cores_b',[]))),
                         subst=';'.join(f'{k}:{v}' for k,v in (st.get('subst') or {}).items()),nominal_b=','.join(map(str,st.get('nominal_b') or [])))
                steps.append(row)
    ov=d.get('overrides',{})
    labels=[dict(mx=r['mx'],cable=r['cable'],core=r['core'],nhan=r.get('nhan',''),tram=r.get('tram',''),hu=1 if r.get('hu') else 0) for r in ov.get('mx_labels',[])]
    return dict(cables=cables,links=links,steps=steps,labels=labels)

def static(d):
    segs=[]
    for s in d['segments']:
        x={k:s[k] for k in('id','ring','seq','bbnt','a','z','kind','km_hd','km_otdr','km_kml','db1','db2','km_ref','db_ref','allow','delta','margin','roadside','rerouted','ok_core','ok_loss')}
        x['polyline']=[[round(a,5),round(b,5)] for a,b in s['polyline']];segs.append(x)
    nodes=[{k:v[k] for k in('id','type','lat','lon','ring','role') if k in v} for v in d['nodes'].values()]
    return dict(config=dict(drop_max_m=model.CONFIG['drop_max_m'],drop_min_fo=model.CONFIG['drop_min_fo']),
        nodes=nodes,rings={k:dict(csg=v['csg'],segs=v['segs']) for k,v in d['rings'].items()},segments=segs,
        closures=[{k:c[k] for k in('name','straight','lat','lon','desc')} for c in d['closures']],
        odf=[{k:o[k] for k in('node','port','dest','cable')} for o in d['odf']],odf_agg=d['odf_agg'],odf_core_map=d['odf_core_map'],
        mxcap=d['mx_cables'],mxcore=d['mx_cores'],mx_notes=d['mx_notes'],straight=model.STRAIGHT,
        issues=[list(i) for i in d['issues']],fix=FIX)

def raw(d):return dict(static=static(d),layer=layer(d))

def expected(d):
    return dict(
      paths=[dict(id=lk['id'],total_m=lk['total_m'],ref_m=lk['ref_m'],design_m=lk['design_m'],checks=[[s['at'],s['check'],s['check_detail']] for s in lk['steps'] if s['t']=='mx'],
                  ports=[s.get('ports') for s in lk['steps'] if s['t']=='odf']) for lk in d['paths']],
      ledger=[[r['cable'],r['core'],r['status'],r['labels'],r['stations'],r['other']] for r in d['ledger']],
      conflicts=[list(c) for c in d['ledger_conflicts']],
      profiles=[{k:p[k] for k in('id','run','hu','other','lab','lab_stations','free','effect','kind','rule','n_links','used_cores','lost')} for p in d['cable_profiles']],
      station=[[r['station'],r['cable'],r['core'],r['kind'],r['dest'],r['links'],r['srcs'],r['text'],r['odf_ports'],r['port_note']] for r in d['station_cores']],
      agg=[[r['station'],r['odf'],r['port'],r['core'],r['kind'],r['end'],r['links'],r['srcs']] for r in d['agg_odf']],
      pairs=len(d['mx_pairs']),warn=len(d['mx_warn']),
      aggcheck=[[c[0],c[1],c[2],c[3],c[5]] for c in model.agg_check(d)])

def _ints(t):
    out=[]
    for x in str(t or '').replace(';',',').split(','):
        x=x.strip()
        if not x:continue
        if '-' in x:
            a,b=x.split('-',1);out+=list(range(int(a),int(b)+1))
        else:out.append(int(float(x)))
    return out
def _s(v):
    if v is None:return ''
    if isinstance(v,float) and v==int(v):v=int(v)
    return str(v).strip()

def layer_to_data(L,ring_meta):
    """Ngược lại của layer(): từ các bảng DL_* (list dict) -> cables.json, paths/Rn.json, overrides.mx_labels."""
    cables=[]
    for r in L['cables']:
        ends={}
        for part in _s(r.get('ends')).split(';'):
            if '=' in part:
                k,v=part.split('=',1);ends[k.strip()]=v.strip()
        c=dict(id=_s(r['id']),name=_s(r.get('name')),fo=int(float(r['fo'])),frm=_s(r.get('frm')),to=_s(r.get('to')),len_m=int(float(r['len_m'])) if _s(r.get('len_m')) else 0,
               src=_s(r.get('src')),ends=ends)
        if _s(r.get('so_row')):c['so_row']=int(float(r['so_row']))
        for k in('ma_cap','cs_dau','cs_cuoi'):
            if _s(r.get(k)):c[k]=_s(r[k])
        cables.append(c)
    steps={}
    for r in L['steps']:steps.setdefault(_s(r['link']),[]).append(r)
    rings={}
    for r in L['links']:
        lk=dict(id=_s(r['id']),frm=_s(r['frm']),to=_s(r['to']))
        o=[int(float(x)) for x in _s(r.get('odf_otdr_m')).split('/') if x.strip()]
        if o:lk['odf_otdr_m']=o
        if _s(r.get('bbnt_otdr_m')):lk['bbnt_otdr_m']=int(float(r['bbnt_otdr_m']))
        if _s(r.get('rerouted')) not in('','0'):lk['rerouted']=True
        if _s(r.get('complete')) in('0','False','false'):lk['complete']=False
        dc=[x.strip() for x in _s(r.get('design_cables')).split(',') if x.strip()]
        if dc:lk['design_cables']=dc
        if _s(r.get('note')):lk['note']=_s(r['note'])
        lk['steps']=[]
        for st in sorted(steps.get(lk['id'],[]),key=lambda x:int(float(x['seq']))):
            t=_s(st['t']);x=dict(t=t)
            if t=='odf':
                x['at']=_s(st['at']);x['name']=_s(st.get('name'));x['cores']=_ints(st.get('cores'))
                if _s(st.get('odf_ref')):x['odf_ref']=_s(st['odf_ref'])
            elif t=='cable':
                x['cable']=_s(st['cable']);x['cores']=_ints(st.get('cores'))
            else:
                x['at']=_s(st['at']);x['a_cable']=_s(st['a_cable']);x['cores_a']=_ints(st.get('cores_a'));x['b_cable']=_s(st['b_cable']);x['cores_b']=_ints(st.get('cores_b'))
                if _s(st.get('subst')):
                    x['subst']={a.split(':')[0].strip():int(a.split(':')[1]) for a in _s(st['subst']).split(';') if ':' in a}
                if _s(st.get('nominal_b')):x['nominal_b']=_ints(st['nominal_b'])
            x['note']=_s(st.get('note'))
            lk['steps'].append(x)
        rings.setdefault(_s(r['ring']),[]).append(lk)
    labels=[]
    for r in L['labels']:
        if not _s(r.get('mx')):continue
        labels.append(dict(mx=_s(r['mx']),cable=_s(r['cable']),core=int(float(r['core'])),nhan=_s(r.get('nhan')),tram=_s(r.get('tram')),hu=1 if _s(r.get('hu')) not in('','0') else 0))
    return cables,rings,labels

if __name__=='__main__':
    d=model.build()
    out=sys.argv[1] if len(sys.argv)>1 else HERE
    json.dump(raw(d),open(os.path.join(out,'raw.json'),'w',encoding='utf-8'),ensure_ascii=False)
    json.dump(expected(d),open(os.path.join(out,'expected.json'),'w',encoding='utf-8'),ensure_ascii=False)
    print('xuất raw.json, expected.json ->',out)
