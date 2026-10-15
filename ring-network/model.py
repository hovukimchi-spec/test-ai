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
 'R5':dict(csg=['HNB012','HNB014','HNB075'],segs=[16,17,18,19],spurs=['HNB113']),
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

def splice_pairs(ends):
    """Quy ước nhãn hàn (người dùng): cùng nhãn = cùng nhóm hàn; trong một nhãn, sợi nhỏ hàn sợi nhỏ.
    ends: {tên_đầu_cáp: ['A','A','B',...]} (nhãn của sợi 1..n; '' = không hàn).
    Trả (cặp, cảnh_báo): cặp = [(nhãn, đầu1, sợi1, đầu2, sợi2)]."""
    pairs=[];warn=[];labels=sorted({l for v in ends.values() for l in v if l})
    for lab in labels:
        pos={e:[i+1 for i,l in enumerate(v) if l==lab] for e,v in ends.items() if lab in v}
        names=list(pos)
        if len(names)==1:warn.append(f'nhãn {lab}: chỉ có ở một đầu cáp ({names[0]})');continue
        if len(names)>2:warn.append(f'nhãn {lab}: có ở {len(names)} đầu cáp, cần chỉ định cặp');continue
        a,b=names
        if len(pos[a])!=len(pos[b]):warn.append(f'nhãn {lab}: số sợi khác nhau ({a}:{len(pos[a])} vs {b}:{len(pos[b])})')
        pairs+= [(lab,a,x,b,y) for x,y in zip(pos[a],pos[b])]
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
        closures.append(dict(name=name,straight=r['sheet']!='MX',lat=_f(r['lat']),lon=_f(r['lon']),desc=r['mo_ta']))
    cables=_csv('cap_tong_hop.csv')
    d=dict(config=CONFIG,nodes=nodes,rings=RINGS,segments=segments,odf=odf,odf_agg=odf_agg,closures=closures,cables=cables,partners=PARTNERS,
           vat_tu=_csv('vat_tu_odf_mx.csv'))
    d['issues']=detect_issues(d)
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
        if s['km_otdr'] and s['km_hd'] and abs(s['km_otdr']-s['km_hd'])/s['km_hd']>CONFIG['hd_warn']:
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
