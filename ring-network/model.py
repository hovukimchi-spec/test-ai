"""Mô hình mạng ring CSG Nhà Bè. Mọi thứ khác (Excel, HTML) đọc từ build().
Nguồn dữ liệu: data/*.csv (trích bởi extract_sources.py từ các file ghi tay) + cấu hình dưới đây.
Quy ước đã chốt với người dùng nằm trong CONFIG và DE_XUAT_MO_HINH.md."""
import csv,json,math,os,re
HERE=os.path.dirname(os.path.abspath(__file__));DATA=os.path.join(HERE,'data')

CONFIG=dict(
    # ngưỡng suy hao theo chiều dài MỘT đoạn giữa hai trạm liền kề (SFP 10/40/80 km của MBF)
    thresholds=[(10,12.1),(40,17.0),(math.inf,27.0)],
    core_delta_max=2.0,        # chênh suy hao tối đa giữa 2 core
    slack_est=1.08,            # hệ số cáp dự trữ ước tính: km thực ≈ km KML × hệ số
    ratio_warn=(0.9,1.5),      # cảnh báo khi OTDR/KML ngoài khoảng này
    hd_warn=0.2,               # cảnh báo khi |OTDR-HĐ|/HĐ > 20%
    link_cores=2,              # mỗi link dùng 2 core
    port_per_dir=6,            # ODF CSG: mỗi hướng dùng tối đa 6 cổng (theo file ODF)
    aggs=('NBE12','NBE22'),
    drop_max_m=300,            # cáp vào trạm từ MX trục gần trạm: < 300 m được chấp nhận
    drop_min_fo=12,            # với điều kiện dùng cáp lớn, từ 12FO trở lên
)
def threshold(km):
    for lim,db in CONFIG['thresholds']:
        if km<lim:return db
    return CONFIG['thresholds'][-1][1]

# Ring: thứ tự đoạn BBNT từ NBE12 sang NBE22; spur = nhánh cụt (last-mile, 1 hướng)
RINGS={
 'R1':dict(csg=['HNB059','HNB060','HNB048'],segs=[34,37,36,35],spurs=[]),
 'R2':dict(csg=['HNB054','HNB006','HNB091'],segs=[30,31,32,33],spurs=[]),
 'R3':dict(csg=['HNB055','HNB065','HNB094'],segs=[25,26,27,28],spurs=[29]),
 'R4':dict(csg=['HNB011','HNB056','HNB071','HNB073'],segs=[20,21,22,23,24],spurs=[]),
 'R5':dict(csg=['HNB012','HNB014','HNB075'],segs=[16,17,18,19],spurs=[]),   # HNB113: tuyến đã huỷ
 'R6':dict(csg=['HNB086','HNB024','HNB027','HNB031','HNB020'],segs=[10,11,12,13,14,15],spurs=[]),
 'R7':dict(csg=['HNB005','HNB062','HNB021','HNB013'],segs=[5,6,7,8,9],spurs=[]),
 'R8':dict(csg=['HNB066','HNB016','HNB038'],segs=[1,2,3,4],spurs=[]),
}
# lề đường theo lời người dùng (trục lề trái dùng chung cáp: NBE12→NVT01→NVT02A→NVT03A)
ROADSIDE={34:'trái',37:'trái',36:'phải',35:'phải',30:'trái (trục NVT)',31:'trái (trục NVT)',32:'trái',33:'phải',14:'hai lề (chưa rõ chi tiết)'}
# đoạn đã đổi tuyến so với thiết kế: dùng km KML × slack khi tính quỹ suy hao
REROUTED={1,5}
# đối tác dùng core trống (từ ghi chú ODF AGG)
PARTNERS=[('DWDM Vinanet','ODF-01 NBE22, MX_HTP-03A','ngưng từ 16/05/2025'),
          ('TTC (gói Long An)','ODF-02 NBE22 / ODF Nguyễn Bình','CG23; một số cổng ghi "hủy"/"dùng đến MX NB-NVT"'),
          ('MTC Vinanet (VNN)','ODF-01 Nguyễn Bình, phối cáp ngoài MX NB-NVT','')]

def _csv(name):
    with open(os.path.join(DATA,name),encoding='utf-8') as f:return list(csv.DictReader(f))
def _f(x):
    try:return float(str(x).replace(',','.'))
    except:return None
def norm(n):
    n=n.upper();m=re.findall(r'\d+',n)[-1]
    return ('NBE'+m) if ('NBE' in n or n.startswith('AGG')) else 'HNB'+m.zfill(3)

def hav(a,b):
    R=6371.0088;la1,lo1,la2,lo2=map(math.radians,[a[1],a[0],b[1],b[0]])
    h=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*R*math.asin(math.sqrt(h))

def splice_pairs(ends,with_flag=False):
    """Quy ước nhãn hàn (người dùng): cùng nhãn = cùng nhóm hàn; trong một nhãn, sợi nhỏ hàn sợi nhỏ.
    ends: {tên_đầu_cáp: ['A','A','B',...]} (nhãn của sợi 1..n; '' = không hàn).
    Trả (cặp, cảnh_báo): cặp = [(nhãn, đầu1, sợi1, đầu2, sợi2)]."""
    pairs=[];warn=[];labels=sorted({l for v in ends.values() for l in v if l and l!='HƯ'})
    for lab in labels:
        pos={e:[i+1 for i,l in enumerate(v) if l==lab] for e,v in ends.items() if lab in v}
        names=list(pos)
        if len(names)==1:warn.append(f'nhãn {lab}: chỉ có ở một đầu cáp ({names[0]})');continue
        if len(names)>2:warn.append(f'nhãn {lab}: có ở {len(names)} đầu cáp, cần chỉ định cặp');continue
        a,b=names
        if len(pos[a])!=len(pos[b]):warn.append(f'nhãn {lab}: số sợi khác nhau ({a}:{len(pos[a])} vs {b}:{len(pos[b])})')
        bal=len(pos[a])==len(pos[b])
        pairs+= [((lab,a,x,b,y,bal) if with_flag else (lab,a,x,b,y)) for x,y in zip(pos[a],pos[b])]
    return pairs,warn

def build():
    nodes={r['id']:dict(id=r['id'],type=r['loai'],lon=float(r['lon']),lat=float(r['lat'])) for r in _csv('nodes.csv')}
    bb={int(r['stt']):r for r in _csv('bbnt_segments.csv')}
    geo={int(r['stt']):r for r in _csv('segments_geo.csv')}
    lines=json.load(open(os.path.join(DATA,'kml_lines.json')))
    kml={}
    for k,p in lines.items():
        t=re.findall(r'AGG-HCMNBE\d+|AGG-HNB\d+|CSG-HNB\d+|HNB\d+',k.split('|',1)[1].replace(' ',''))
        kml[frozenset((norm(t[0]),norm(t[1])))]=(p,k.split('|')[0])
    segments=[];ring_of={}
    for rid,r in RINGS.items():
        chain=['NBE12']+r['csg']+['NBE22']
        for i,sid in enumerate(r['segs']):
            b=bb[sid];g=geo[sid]
            a_,z_=chain[i],chain[i+1]
            km_hd,km_otdr,km_kml=_f(b['km_hop_dong']),_f(b['km_do_OTDR']),_f(g['km_KML'])
            d1,d2=_f(b['dB_core1']),_f(b['dB_core2'])
            km_ref=km_kml*CONFIG['slack_est'] if sid in REROUTED else km_otdr
            db_max=max(d1,d2)*(km_ref/km_otdr if sid in REROUTED else 1)
            seg=dict(id=f'{rid}-{i+1:02d}',ring=rid,seq=i+1,bbnt=sid,a=a_,z=z_,kind='ring',
                     km_hd=km_hd,km_otdr=km_otdr,km_kml=km_kml,db1=d1,db2=d2,allow_bbnt=_f(b['dB_cho_phep']),
                     km_ref=round(km_ref,3),db_ref=round(db_max,3),roadside=ROADSIDE.get(sid,''),
                     rerouted=sid in REROUTED,polyline=kml[frozenset((a_,z_))][0])
            seg['allow']=threshold(km_ref);seg['delta']=round(abs(d1-d2),3);seg['margin']=round(seg['allow']-db_max,2)
            seg['ok_core']=seg['delta']<=CONFIG['core_delta_max'];seg['ok_loss']=db_max<=seg['allow']
            segments.append(seg);ring_of[sid]=rid
        for sp in r['spurs']:
            if sp==29:
                b=bb[29];g=geo[29];a_,z_='HNB094','HNB018'
                km_otdr=_f(b['km_do_OTDR']);d1,d2=_f(b['dB_core1']),_f(b['dB_core2'])
                seg=dict(id=f'{rid}-S1',ring=rid,seq=99,bbnt=29,a=a_,z=z_,kind='nhánh cụt',km_hd=_f(b['km_hop_dong']),km_otdr=km_otdr,
                         km_kml=_f(g['km_KML']),db1=d1,db2=d2,allow_bbnt=_f(b['dB_cho_phep']),km_ref=km_otdr,db_ref=max(d1,d2),roadside='',rerouted=False,polyline=kml[frozenset((a_,z_))][0])
            else:
                p=kml[frozenset(('HNB012','HNB113'))][0];km=sum(hav(p[i],p[i+1]) for i in range(len(p)-1))
                seg=dict(id=f'{rid}-S1',ring=rid,seq=99,bbnt=None,a='HNB012',z='HNB113',kind='nhánh cụt',km_hd=None,km_otdr=None,km_kml=round(km,3),
                         db1=None,db2=None,allow_bbnt=None,km_ref=round(km*CONFIG['slack_est'],3),db_ref=None,roadside='',rerouted=False,polyline=p)
            seg['allow']=threshold(seg['km_ref']);seg['delta']=None if seg['db1'] is None else round(abs(seg['db1']-seg['db2']),3)
            seg['margin']=None if seg['db_ref'] is None else round(seg['allow']-seg['db_ref'],2)
            seg['ok_core']=None if seg['delta'] is None else seg['delta']<=CONFIG['core_delta_max']
            seg['ok_loss']=None if seg['db_ref'] is None else seg['db_ref']<=seg['allow']
            segments.append(seg)
    # nút
    for rid,r in RINGS.items():
        for n in r['csg']:nodes[n]['ring']=rid;nodes[n]['role']='ring'
        for n in r['spurs']:
            if isinstance(n,str):nodes[n]['ring']=rid;nodes[n]['role']='nhánh cụt (cấp 3)'
    nodes['HNB113']['ring']='R5';nodes['HNB113']['role']='đã huỷ tuyến (không dùng)'
    nodes['HNB018']['ring']='R3';nodes['HNB018']['role']='nhánh cụt (cấp 3)'
    # ODF CSG
    odf=[]
    for r in _csv('odf_csg.csv'):
        note=r['ghi_chu_goc'];m=re.match(r'\s*(?:To\s*:?\s*)?(AGG-NBE\d+|HNB\d+|MX[_\w\- ]+?)(?:\s*/|$)',note)
        dest=norm(m.group(1)) if m and not m.group(1).startswith('MX') else (m.group(1).strip() if m else '')
        fo=re.search(r'(\d+)\s*F[O0]',note,re.I);cs=re.search(r'cs\s*(\d+)',note,re.I)
        odf.append(dict(node=r['odf'].replace('ODF-',''),port=int(r['cong']),label=r['nhan_E'],dest=dest,cable=note,fo=fo.group(1) if fo else '',cs=cs.group(1) if cs else ''))
    odf_agg=_csv('odf_agg.csv')
    closures=[];seen={}
    for r in _csv('mx_dang_ky.csv'):
        name=r['ten'].strip();
        if name in seen and name=='MX_NVT_03A':name='MX_NVT_03B'      # người dùng xác nhận: ghi nhầm trùng tên
        elif name in seen and name.startswith('MX_HTP-03'):continue
        elif name in seen:name=name+' (2)'
        seen[name]=1
        if name.startswith('Thẳng HTP'):name='MX thẳng HTP'
        closures.append(dict(name=name,straight=r['sheet']!='MX',lat=_f(r['lat']),lon=_f(r['lon']),desc=r['mo_ta']))
    cables=_csv('cap_tong_hop.csv')
    mxc=_csv('mx_cap.csv');mxo=_csv('mx_core.csv')
    cab={c['cap_id']:c for c in mxc}
    pairs=[];mxwarn=[]
    for mx in dict.fromkeys(c['mx'] for c in mxc):
        ids=[c['cap_id'] for c in mxc if c['mx']==mx];ends={};info={}
        for i in ids:
            rows=[r for r in mxo if r['cap_id']==i];n=max(int(r['core']) for r in rows);ends[i]=['']*n
            for r in rows:ends[i][int(r['core'])-1]=r['nhan']
            info[i]={int(r['core']):r for r in rows}
        pr,wr=splice_pairs(ends,True)
        for lab,a,x,b,y,bal in pr:
            ra,rb=info[a][x],info[b][y]
            pairs.append(dict(mx=mx,label=lab,a=a,core_a=x,color_a=ra['mau_soi'],tube_a=ra['ong'],b=b,core_b=y,color_b=rb['mau_soi'],tube_b=rb['ong'],station=ra['tram'] or rb['tram'],balanced=bal))
        mxwarn+=[(mx,w) for w in wr]
        for i in ids:
            if not any(ends[i]):mxwarn.append((mx,f"{cab[i]['o_goc']}: chưa ghi nhãn core (chưa có dữ liệu phối)"))
    d=dict(config=CONFIG,mx_cables=mxc,mx_cores=mxo,mx_pairs=pairs,mx_warn=mxwarn,mx_notes=_csv('mx_ghi_chu.csv'),nodes=nodes,rings=RINGS,segments=segments,odf=odf,odf_agg=odf_agg,closures=closures,cables=cables,partners=PARTNERS,
           vat_tu=_csv('vat_tu_odf_mx.csv'))
    d['issues']=detect_issues(d)
    d['paths']=load_paths(d)
    d['ledger'],d['ledger_conflicts']=core_ledger(d)
    d['cable_profiles']=cable_profiles(d)
    d['station_cores']=station_core_table(d)
    d['agg_odf']=agg_odf_table(d)
    return d

def simulate_cut(d,seg_ids):
    """Đứt các đoạn (id) cùng lúc: trả {CSG: AGG còn tới được hoặc None}, và danh sách CSG mất kết nối."""
    cut=set(seg_ids);res={}
    for rid,r in RINGS.items():
        chain=['NBE12']+r['csg']+['NBE22'];segs=[s for s in d['segments'] if s['ring']==rid and s['kind']=='ring']
        segs.sort(key=lambda s:s['seq'])
        for i,n in enumerate(r['csg'],1):
            left=all(segs[k]['id'] not in cut for k in range(i));right=all(segs[k]['id'] not in cut for k in range(i,len(segs)))
            res[n]=('NBE12' if left else None,'NBE22' if right else None)
    for s in d['segments']:
        if s['kind']=='nhánh cụt':
            z=s['z'];ok=s['id'] not in cut
            res[z]=tuple(x if ok and x else None for x in res.get(s['a'],(None,None)))
    return res

def detect_issues(d):
    L=[]
    for s in d['segments']:
        if s['rerouted']:
            L.append((s['id'],'đổi tuyến',f"HĐ {s['km_hd']} km là chiều dài thiết kế (qua cáp C11); tuyến thực tế sau khi chuyển hướng dài {s['km_otdr']} km"))
        elif s['km_otdr'] and s['km_hd'] and abs(s['km_otdr']-s['km_hd'])/s['km_hd']>CONFIG['hd_warn']:
            L.append((s['id'],'chiều dài',f"BBNT: HĐ {s['km_hd']} km vs OTDR {s['km_otdr']} km (lệch {round((s['km_otdr']/s['km_hd']-1)*100)}%)"))
        if s['km_otdr'] and s['km_kml']:
            r=s['km_otdr']/s['km_kml']
            if not CONFIG['ratio_warn'][0]<=r<=CONFIG['ratio_warn'][1]:L.append((s['id'],'KML',f"OTDR/KML = {r:.2f} (KML {s['km_kml']} km, OTDR {s['km_otdr']} km)"))
        if s['ok_core'] is False:L.append((s['id'],'lệch core',f"chênh {s['delta']} dB > {CONFIG['core_delta_max']} dB"))
        if s['ok_loss'] is False:L.append((s['id'],'suy hao',f"{s['db_ref']} dB > ngưỡng {s['allow']} dB"))
    hd=[s for s in d['segments'] if s['km_hd']];
    from collections import Counter
    for v,c in Counter(s['km_hd'] for s in hd).items():
        if c>=3:L.append(('BBNT','số liệu',f'giá trị HĐ {v} km lặp {c} lần: nghi số điền mẫu'))
    L.append(('ODF-HNB020','ghi chú','ghi "To HNB027" ở cả hai hướng: nghi sai, đúng ra HNB031 và AGG-NBE22'))
    L.append(('ODF-HNB014/054/006/091/048/060/059','thiếu','chưa ghi đầu cáp/hướng'))
    L.append(('MX_NVT_03A','tên','hai măng xông cùng tên; người dùng xác nhận là 03A và 03B (hai bên lề)'))
    return L

if __name__=='__main__':
    d=build()
    print(len(d['nodes']),'nút',len(d['segments']),'đoạn',len(d['odf']),'cổng ODF CSG',len(d['closures']),'MX',len(d['issues']),'cảnh báo')
    for i in d['issues']:print(i)
    iso=[k for k,v in simulate_cut(d,['R1-02','R1-03']).items() if v==(None,None)];print('đứt R1-02+R1-03 → mất:',iso)
    print(splice_pairs({'X':['A','A','B','B'],'Y':['A','A','B','B','C']}))

def corridor_overlap(p1,p2,tol=20,step=10):
    """Độ dài (km) hai đường vẽ KML đi sát nhau trong dung sai tol (m). Cảnh báo, không phải đo thực địa."""
    import collections
    mx=111.32*math.cos(math.radians(10.69))*1000;my=110.57*1000
    xy=lambda p:((p[0]-106.7)*mx,(p[1]-10.69)*my)
    def dens(p):
        q=[xy(a) for a in p];o=[q[0]]
        for a,b in zip(q,q[1:]):
            n=max(1,int(math.dist(a,b)//step))
            o+=[(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(1,n+1)]
        return o
    A,B=dens(p1),dens(p2);cell=collections.defaultdict(list)
    for q in B:cell[(int(q[0]//tol),int(q[1]//tol))].append(q)
    c=0
    for a in A:
        ci,cj=int(a[0]//tol),int(a[1]//tol)
        if any(math.dist(a,q)<=tol for di in(-1,0,1) for dj in(-1,0,1) for q in cell.get((ci+di,cj+dj),())):c+=1
    return c*step/1000

def check_splice(pairs,a,ca,b,cb,subst=None,nominal_b=None):
    """Đối chiếu một mối hàn (cáp a core ca ↔ cáp b core cb) với bảng phối core suy ra từ sơ đồ MX.
    subst/nominal_b: core hư được thay (quy tắc vẫn theo thiết kế ban đầu, thực tế thay core)."""
    if not a or not b:return 'chưa có sơ đồ','không xác định cáp trong sơ đồ MX'
    m={}
    for p in pairs:
        if p['a']==a and p['b']==b:m[p['core_a']]=(p['core_b'],p['label'])
        elif p['a']==b and p['b']==a:m[p['core_b']]=(p['core_a'],p['label'])
    if not any(c in m for c in ca):return 'chưa có nhãn','sơ đồ MX chưa ghi nhãn cho các core này'
    bad=[];ok=True
    for x,y in zip(ca,cb):
        if x in m and m[x][0]==y:continue
        ok=False;bad.append(f"core {x}→{m[x][0] if x in m else '?'} (sơ đồ) ≠ {y} (mô tả)")
    if ok:return 'khớp sơ đồ','nhãn '+','.join(sorted({m[x][1] for x in ca if x in m}))
    if subst and nominal_b:
        # thiết kế: ca[i] ↔ nominal_b[i]; thực tế core hư nominal thay bằng subst
        act=[subst.get(str(n),n) for n in nominal_b]
        if act==list(cb) and {c for c in cb}=={m[x][0] for x in ca if x in m}:
            return 'khớp sơ đồ (thay core hư)','thiết kế '+'+'.join(f'{x}↔{n}' for x,n in zip(ca,nominal_b))+'; thực tế '+'+'.join(f'{x}↔{y}' for x,y in zip(ca,cb))
    if all(x in m for x in ca) and {m[x][0] for x in ca}==set(cb):return 'khớp nhóm, THỨ TỰ KHÁC','cùng nhóm core: '+'; '.join(bad)
    return 'KHÁC sơ đồ','; '.join(bad)

def load_paths(d):
    cables={c['id']:c for c in json.load(open(os.path.join(DATA,'cables.json'),encoding='utf-8'))}
    omap=json.load(open(os.path.join(DATA,'odf_core_map.json'),encoding='utf-8'))
    d['odf_core_map']=omap
    ov_path=os.path.join(DATA,'overrides.json')
    ov=json.load(open(ov_path,encoding='utf-8')) if os.path.exists(ov_path) else {}
    d['overrides']=ov
    ov_pairs=[]
    grp={}
    for r_ in ov.get('mx_labels',[]):
        if r_.get('nhan'):grp.setdefault((r_['mx'],r_['nhan']),[]).append(r_)
    for (mx_,lab_),rs_ in grp.items():
        bycab={}
        for r_ in rs_:bycab.setdefault(r_['cable'],[]).append(r_)
        if len(bycab)!=2:continue
        (ca_,la_),(cb_,lb_)=sorted(bycab.items())
        la_=sorted(la_,key=lambda x:x['core']);lb_=sorted(lb_,key=lambda x:x['core'])
        for x_,y_ in zip(la_,lb_):
            ov_pairs.append(dict(mx=mx_,label=lab_,a='CAB:'+ca_,core_a=x_['core'],b='CAB:'+cb_,core_b=y_['core'],station=x_.get('tram') or y_.get('tram') or '',source='nhập tay'))
    d['ov_pairs']=ov_pairs
    so=_csv('cap_tong_hop.csv')
    for c in cables.values():
        r=so[c['so_row']-2] if c.get('so_row') else None
        c['ma_cap']=(c.get('ma_cap') or '') or ((r['ma_cap'].strip() if r else '') or '')
        c['cs_dau']=str(c.get('cs_dau') or '') or (r['cs_dau'] if r else '');c['cs_cuoi']=str(c.get('cs_cuoi') or '') or (r['cs_cuoi'] if r else '');c['so_ghi_chu']=r['ghi_chu'] if r else ''
        c['so_dau_cuoi']=f"{r['dau']} → {r['cuoi']}" if r else ''
    for cid_,o in ov.get('cables',{}).items():
        if cid_ in cables:
            for k_,v_ in o.items():
                if v_ not in (None,''):cables[cid_][k_]=v_
    d['phys_cables']=cables
    out=[]
    for f in sorted(os.listdir(os.path.join(DATA,'paths'))):
        if not f.endswith('.json'):continue
        P=json.load(open(os.path.join(DATA,'paths',f),encoding='utf-8'))
        for lk in P['links']:
            tot=0;rows=[]
            for st in lk['steps']:
                r=dict(st)
                if st['t']=='cable':
                    c=cables[st['cable']];tot+=c['len_m'];r.update(name=c['name'],fo=c['fo'],frm=c['frm'],to=c['to'],len_m=c['len_m'],src=c['src'],cum=tot)
                if st['t']=='mx':
                    ea=cables[st['a_cable']]['ends'].get(st['at']) or 'CAB:'+st['a_cable'];eb=cables[st['b_cable']]['ends'].get(st['at']) or 'CAB:'+st['b_cable']
                    r['check'],r['check_detail']=check_splice(d['mx_pairs'],ea,st['cores_a'],eb,st['cores_b'],st.get('subst'),st.get('nominal_b'))
                    if r['check'].startswith('chưa') and d['ov_pairs']:
                        c2,t2=check_splice(d['ov_pairs'],'CAB:'+st['a_cable'],st['cores_a'],'CAB:'+st['b_cable'],st['cores_b'],st.get('subst'),st.get('nominal_b'))
                        if not c2.startswith('chưa'):r['check'],r['check_detail']=c2+' (nhãn nhập tay)',t2
                if st['t']=='odf' and st.get('odf_ref'):
                    inv={v:int(k) for k,v in omap[st['odf_ref']].items()}
                    r['ports']=[inv.get(c,c) for c in st['cores']]
                rows.append(r)
            bb=lk.get('bbnt_otdr_m')
            if bb is None:
                sg=next((s for s in d['segments'] if s['id']==lk['id']),None)
                bb=round(sg['km_otdr']*1000) if sg and sg.get('km_otdr') else None
            ref=(lk.get('odf_otdr_m') or [None])[0] or bb
            dz=sum(cables[c]['len_m'] for c in lk.get('design_cables',[])) or None
            out.append(dict(design_m=dz,ring=P['ring'],id=lk['id'],frm=lk['frm'],to=lk['to'],total_m=tot,bbnt_otdr_m=bb,rerouted=lk.get('rerouted',False),note=lk.get('note',''),odf_otdr_m=lk.get('odf_otdr_m'),ref_m=ref,complete=lk.get('complete',True),steps=rows))
    return out


AGG_ODF={'C01':('phai','ODF-02'),'C22':('phai','ODF-01'),'C35':('trai','ODF-01'),'C17':('trai','ODF-02')}

def agg_odf_use(d):
    """Cổng ODF AGG -> (cáp, core): link ring (so khớp đường đi) và dùng khác (đối tác, liên kết AGG–AGG, hư)."""
    omap={int(k):v for k,v in d['odf_core_map']['ODF-01 NBE12'].items()}
    other={};linkport=[]
    for cid,(side,odfn) in AGG_ODF.items():
        for r in d['odf_agg']:
            if r['phia']!=side or not r['odf'].startswith(odfn):continue
            p=int(r['cong']);core=omap.get(p,p) if cid=='C22' else p
            dest=(r['dich'] or '').strip();note=(r['ghi_chu'] or '').strip()
            if re.search(r'HNB\d+\s*ring',dest):linkport.append((cid,p,core,norm(dest.split()[0]),dest))
            else:
                bad=any(re.fullmatch(r'h[uư]',str(r[k]).strip().lower()) for k in('cot1','cot2','cot3'))
                other[(cid,core)]=(dest or '(trống)')+((' — '+note) if note else '')+(' [hư]' if bad else '')
    return other,linkport

def agg_check(d):
    """So khớp: mỗi link có đầu AGG phải dùng đúng core mà ODF AGG ghi cho trạm đó."""
    other,linkport=agg_odf_use(d);out=[];used={}
    for lk in d['paths']:
        csg=lk['to'] if lk['frm'].startswith('NBE') else lk['frm'] if lk['to'].startswith('NBE') else None
        if not csg:continue
        cabs=[s for s in lk['steps'] if s['t']=='cable']
        end=cabs[0] if lk['frm'].startswith('NBE') else cabs[-1]
        used[(end['cable'],tuple(end['cores']),csg)]=lk['id']
    for cid,p,core,csg,dest in linkport:
        hit=[v for (c,cs_,g),v in used.items() if c==cid and g==csg and core in cs_]
        out.append((cid,p,core,csg,dest,hit[0] if hit else None))
    return out

# MX thẳng: số mối hàn theo sổ "Sheet2" (thiết kế + phát sinh). Giả định: core i hàn thẳng core i (i ≤ số mối hàn). Phần suy ra tên MX là phỏng đoán.
STRAIGHT={'MX nhập đài Long Thới–NVT':12,'MX thẳng 66-16':6,'MX thẳng 62-21':8,'MX thẳng 13-21':8,'MX thẳng 11-56':6,
 'MX thẳng Phạm Hùng':8,'MX cầu NVL 1':8,'MX cầu NVL 2':8,'MX thẳng đi LVL':12,'MX thẳng LVL-05/DST':12,'MX thẳng LVL-01/075':8,
 'MX thẳng HTP':12,'MX băng sông 1':6,'MX băng sông 2':4}

def station_of(name):
    n=name.upper()
    if n.startswith('HNB'):return re.match(r'HNB\d+',n).group(0)
    if 'NBE22' in n:return 'NBE22'
    if 'NBE12' in n or 'VNPT LONG THỚI' in n.replace('Ớ','Ớ'):return 'NBE12'
    return None

def core_graph(d):
    """Đồ thị core: (cáp, core, MX) -> [(cáp kế, core kế, nguồn, link)]. Nguồn: mô tả > MX thẳng (số mối hàn) > nhập tay > sơ đồ MX."""
    cables=d['phys_cables'];E={}
    def add(c1,k1,c2,k2,mx,src,link=''):
        for a_,ka,b_,kb in ((c1,k1,c2,k2),(c2,k2,c1,k1)):
            lst=E.setdefault((a_,ka,mx),[])
            if not any(x[0]==b_ and x[1]==kb for x in lst):lst.append((b_,kb,src,link))
    for lk in d['paths']:
        for st in lk['steps']:
            if st['t']=='mx':
                for x,y in zip(st['cores_a'],st['cores_b']):add(st['a_cable'],x,st['b_cable'],y,st['at'],'mô tả',lk['id'])
    for mx_,n in STRAIGHT.items():
        cs=[c for c in cables.values() if mx_ in (c['frm'],c['to'])]
        if len(cs)==2:
            a,b=cs
            for i in range(1,min(n,a['fo'],b['fo'])+1):add(a['id'],i,b['id'],i,mx_,'MX thẳng (số mối hàn)')
    cap2={}
    for c in cables.values():
        for mx_,cap in c['ends'].items():cap2[cap]=(c['id'],mx_)
    for p in d['mx_pairs']:
        if p.get('balanced',True) and p['a'] in cap2 and p['b'] in cap2:
            (ca,ma),(cb_,mb)=cap2[p['a']],cap2[p['b']]
            if ma==mb:add(ca,p['core_a'],cb_,p['core_b'],ma,'sơ đồ MX')
    for p in d['ov_pairs']:add(p['a'][4:],p['core_a'],p['b'][4:],p['core_b'],p['mx'],'nhập tay')
    return E

def _use(d):
    if '_use' not in d:
        u={}
        for r in d['ledger']:u[(r['cable'],r['core'])]=r['links']
        d['_use']=u
    return d['_use']

def trace_core(d,E,cable,core,from_node):
    """Đi từ đầu from_node của cáp theo core: trả (loại, trạm/MX cuối, danh sách bước, nguồn, link)."""
    cables=d['phys_cables'];hops=[];srcs=[];links=set();cur,cc,frm=cable,core,from_node
    for _ in range(60):
        c=cables[cur];far=c['to'] if c['frm']==frm else c['frm']
        hops.append((cur,cc,far));st=station_of(far)
        links.update(_use(d).get((cur,cc),[]))
        if st:return ('station',st,far,hops,srcs,sorted(links))
        nxt=E.get((cur,cc,far))
        if not nxt:return ('dead',far,far,hops,srcs,sorted(links))
        n=nxt[0]
        srcs.append(n[2])
        if n[3]:links.add(n[3])
        cur,cc,frm=n[0],n[1],far
    return ('dead','vòng lặp','',hops,srcs,sorted(links))

def odf_ports(d):
    """Số cổng ODF CSG theo từng hướng (từ file ODF): {trạm: {đích: số cổng}}."""
    out={}
    for r in d['odf']:
        dest=r['dest'].replace('AGG-','')
        if dest:out.setdefault(r['node'],{}).setdefault(dest,0);out[r['node']][dest]+=1
    return out

def station_core_table(d):
    """Mỗi cáp kết thúc tại trạm: từng core đi đến đâu (hàn thông / chưa ghi hàn / hư), phụ thuộc măng xông và sợi nối trực tiếp."""
    E=core_graph(d);cables=d['phys_cables'];led={(r['cable'],r['core']):r for r in d['ledger']};rows=[];op=odf_ports(d)
    use={}
    for lk in d['paths']:
        for s_ in lk['steps']:
            if s_['t']=='cable':use.setdefault(s_['cable'],set()).add(lk['id'])
    # cổng ODF suy theo thứ tự hướng (phía NBE12 trước, phía NBE22 sau), mỗi cáp chiếm fo cổng liên tiếp; chỉ áp dụng khi tổng FO ≤ số cổng ODF
    def ring_idx(n):
        if n=='NBE12':return -1
        if n=='NBE22':return 999
        r=d['nodes'].get(n,{}).get('ring');ch=d['rings'].get(r,{}).get('csg',[])
        return ch.index(n) if n in ch else None
    pofs={}
    for st_ in {station_of(c[e]) for c in cables.values() for e in ('frm','to')}-{None,'NBE12','NBE22'}:
        items=[];ok=True
        for cid,c in cables.items():
            if station_of(c['frm'])==st_ or station_of(c['to'])==st_:
                nb={(next(x for x in d['paths'] if x['id']==l)['to'] if next(x for x in d['paths'] if x['id']==l)['frm']==st_ else next(x for x in d['paths'] if x['id']==l)['frm']) for l in use.get(cid,[])}
                if len(nb)!=1:ok=False;break
                ix=ring_idx(next(iter(nb)));ix2=ring_idx(st_)
                if ix is None or ix2 is None:ok=False;break
                items.append((ix,cid,c['fo']))
        nport=sum(1 for o in d['odf'] if o['node']==st_)
        if ok and items and sum(f for _,_,f in items)<=nport:
            off=0
            for ix,cid,fo in sorted(items):pofs[(st_,cid)]=off;off+=fo
    for cid,c in cables.items():
        for end,other in (('frm','to'),('to','frm')):
            node=c[end];st=station_of(node)
            if not st:continue
            neigh=set()
            for lid in use.get(cid,[]):
                lk_=next(x for x in d['paths'] if x['id']==lid);o_=lk_['to'] if lk_['frm']==st or station_of(lk_['frm'])==st else lk_['frm']
                if o_!=st:neigh.add(o_.replace('NBE12','NBE12'))
            ports=None
            if st in op:
                tot=[op[st].get(n_) for n_ in neigh if op[st].get(n_)]
                ports=sum(tot) if tot else None
            for core in range(1,c['fo']+1):
                lr=led[(cid,core)]
                if lr['status']=='HƯ':kind,dest,via,srcs,links='hư','','',[],[]
                else:
                    res=trace_core(d,E,cid,core,node)
                    kind,dest,via,srcs,links=res[0],(res[1] if res[0]=='station' else ''),'→'.join(h[2] for h in res[3]),res[4],res[5]
                    if res[0]=='dead':via=res[1]
                port_note=''
                if ports is not None and core>ports:port_note=f'không có cổng ODF (ODF chỉ có {ports} cổng hướng này)'
                if kind=='hư':text='HƯ'
                elif kind=='station':
                    if links:text='đang chạy link '+', '.join(links)+' → '+dest
                    elif srcs and set(srcs)=={'MX thẳng (số mối hàn)'}:text='hàn thông (MX thẳng, theo số mối hàn) → '+dest
                    elif not srcs:text='sợi nối trực tiếp → '+dest+' (chưa rõ đã hàn pigtail ở ODF hai đầu)'
                    else:text='hàn thông theo nhãn sơ đồ → '+dest+' (chưa gán link)'
                else:text='chưa ghi hàn tại '+via+' (dự phòng / chưa rõ / không hàn)'
                rows.append(dict(odf_port=(pofs[(st,cid)]+core) if (st,cid) in pofs else None,text=text,port_note=port_note,odf_ports=ports,station=st,node=node,cable=cid,name=c['name'],ma_cap=c['ma_cap'],fo=c['fo'],other_end=c[other],core=core,kind=kind,dest=dest,via=via,srcs=sorted(set(srcs)),links=links,status=lr['status']))
    return rows

def agg_odf_table(d):
    """4 ODF ở hai AGG: cổng, core cáp, đích ghi trên ODF, kết quả truy vết theo đồ thị."""
    E=core_graph(d);omap={int(k):v for k,v in d['odf_core_map']['ODF-01 NBE12'].items()}
    spec=[('NBE12','ODF-01 (hướng NB)','C22','phai','ODF-01'),('NBE12','ODF-02 (hướng NVT)','C01','phai','ODF-02'),('NBE22','ODF-01 (cs 1816)','C35','trai','ODF-01'),('NBE22','ODF-02 (cs 1288)','C17','trai','ODF-02')]
    other,_=agg_odf_use(d);out=[]
    for st,name,cid,side,pre in spec:
        c=d['phys_cables'][cid];node=c['frm'] if station_of(c['frm'])==st else c['to']
        for r in d['odf_agg']:
            if r['phia']!=side or not r['odf'].startswith(pre):continue
            p=int(r['cong']);core=omap.get(p,p) if cid=='C22' else p
            res=trace_core(d,E,cid,core,node)
            dest=(r['dich'] or '').strip();note=(r['ghi_chu'] or '').strip()
            out.append(dict(station=st,odf=name,cable=cid,port=p,core=core,dest=dest,note=note,kind=res[0],end=res[1],links=res[5],srcs=sorted(set(res[4]))))
    return out

def core_ledger(d):
    """Quỹ core từng cáp: dùng bởi link nào, hư, nhãn sơ đồ, xung đột. Loại trừ dần: core đã dùng/hư không còn là ứng viên."""
    cables=d['phys_cables'];usage={};other,_=agg_odf_use(d)
    for lk in d['paths']:
        for st in lk['steps']:
            if st['t']=='cable':
                for c in st['cores']:usage.setdefault((st['cable'],c),[]).append(lk['id'])
    labels={}
    for r in d['mx_cores']:labels[(r['cap_id'],int(r['core']))]=(r['nhan'],r['tram'])
    rows=[];conf=[]
    for cid,c in cables.items():
        for core in range(1,c['fo']+1):
            use=sorted(set(usage.get((cid,core),[])))
            lab=[];tr=[]
            for node,cap in c['ends'].items():
                l=labels.get((cap,core))
                if l and (l[0] or l[1]):lab.append(f"{node}: {l[0] or '·'}");tr+= [l[1]] if l[1] else []
            hu=any('HƯ' in x for x in lab)
            if len(use)>1:conf.append((cid,core,use))
            ot=other.get((cid,core),'')
            status='HƯ' if (hu or re.search(r'\bh[uư]\b|\[hư\]',ot.lower())) else ('dùng '+'+'.join(use) if use else ('dùng khác (ODF AGG)' if ot else ('có nhãn, chưa gán link' if lab else 'trống/chưa rõ')))
            rows.append(dict(cable=cid,name=c['name'],route=f"{c['frm']} → {c['to']}",core=core,status=status,other=ot,labels='; '.join(lab),stations=', '.join(dict.fromkeys(tr)),links=use))
    return rows,conf


def _rng(xs):
    xs=sorted(set(xs))
    if not xs:return ''
    out=[];st=pv=xs[0]
    for x in xs[1:]+[None]:
        if x is not None and x==pv+1:pv=x;continue
        out.append(f'{st}' if st==pv else f'{st}-{pv}')
        if x is not None:st=pv=x
    return ','.join(out)

def cable_profiles(d):
    """Hồ sơ từng cáp phục vụ xử lý sự cố: mã cáp, core đang chạy (link nào), hư, có nhãn chưa gán, trống, hệ quả khi đứt."""
    led={}
    for r in d['ledger']:led.setdefault(r['cable'],[]).append(r)
    seg_ids={s['id'] for s in d['segments']}
    out=[]
    for cid,c in d['phys_cables'].items():
        rows=led[cid];run={};hu=[];lab=[];free=[];stn={};oth={}
        for r in rows:
            if r['other']:oth.setdefault(r['other'],[]).append(r['core'])
            if r['status']=='HƯ':hu.append(r['core'])
            elif r['status'].startswith('dùng khác'):pass
            elif r['status'].startswith('dùng'):
                for l in r['links']:run.setdefault(l,[]).append(r['core'])
            elif r['status'].startswith('có nhãn'):
                lab.append(r['core'])
                if r['stations']:stn.setdefault(r['stations'],[]).append(r['core'])
            else:free.append(r['core'])
        links=sorted(run);cut=[l for l in links if l in seg_ids]
        res=simulate_cut(d,cut) if cut else {}
        lost=sorted(k for k,v in res.items() if v==(None,None))
        out.append(dict(id=cid,name=c['name'],ma_cap=c['ma_cap'] or '(chưa ghi mã cáp trong sổ)',fo=c['fo'],frm=c['frm'],to=c['to'],len_m=c['len_m'],
            cs_dau=c['cs_dau'],cs_cuoi=c['cs_cuoi'],so_row=c.get('so_row'),so_dau_cuoi=c.get('so_dau_cuoi',''),
            run='; '.join(f"{_rng(run[l])} ({l})" for l in links) or '—',run_cores=sorted(sum(run.values(),[])),
            hu=_rng(hu) or '—',other='; '.join(f'{_rng(v)}: {k}' for k,v in oth.items()) or '—',lab=_rng(lab) or '—',lab_stations='; '.join(f"{k}: {_rng(v)}" for k,v in stn.items()) or '—',free=_rng(free) or '—',
            n_free=len(free),links=links,lost=', '.join(lost) or '—',
            effect=('MẤT KẾT NỐI: '+', '.join(lost)) if lost else ('các link '+', '.join(links)+' mất một hướng, ring vẫn bảo vệ' if links else 'chưa có link mô tả'),
            link_status=run))
    for p in out:
        c=d['phys_cables'][p['id']];stn=lambda x:x.startswith(('HNB','NBE','ODF'))
        p['n_links']=len(p['links']);p['rings']=sorted({l.split('-')[0] for l in p['links']});p['used_cores']=len(p['run_cores']);p['util']=len(p['run_cores'])/c['fo']
        if stn(c['frm']) and stn(c['to']):p['kind']='giữa hai trạm'
        elif (stn(c['frm']) or stn(c['to'])) and c['len_m']<CONFIG['drop_max_m']:p['kind']='cáp vào trạm'
        elif stn(c['frm']) or stn(c['to']):p['kind']='cáp riêng tới trạm (>=300 m)'
        else:p['kind']='cáp trục'
        if p['kind']=='cáp vào trạm':
            p['rule']='đạt (<300 m, ≥12FO)' if c['fo']>=CONFIG['drop_min_fo'] else 'KHÔNG đạt: cáp vào trạm phải ≥12FO'
        else:p['rule']='—'
    return out
