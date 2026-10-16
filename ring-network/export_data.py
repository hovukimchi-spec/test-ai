"""Xuất dữ liệu cho HTML (RAW = nền tĩnh + lớp sửa được) và kết quả kỳ vọng để kiểm thử động cơ JS.
Lớp sửa được (layer) có cùng cấu trúc với các sheet DL_* trong Excel."""
import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import model
HERE=model.HERE;DATA=model.DATA

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
        nodes=nodes,rings={k:dict(csg=v['csg']) for k,v in d['rings'].items()},segments=segs,
        closures=[{k:c[k] for k in('name','straight','lat','lon','desc')} for c in d['closures']],
        odf=[{k:o[k] for k in('node','port','dest','cable')} for o in d['odf']],odf_agg=d['odf_agg'],odf_core_map=d['odf_core_map'],
        mxcap=d['mx_cables'],mxcore=d['mx_cores'],mx_notes=d['mx_notes'],straight=model.STRAIGHT,
        issues=[list(i) for i in d['issues']])

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

if __name__=='__main__':
    d=model.build()
    out=sys.argv[1] if len(sys.argv)>1 else HERE
    json.dump(raw(d),open(os.path.join(out,'raw.json'),'w',encoding='utf-8'),ensure_ascii=False)
    json.dump(expected(d),open(os.path.join(out,'expected.json'),'w',encoding='utf-8'),ensure_ascii=False)
    print('xuất raw.json, expected.json ->',out)
