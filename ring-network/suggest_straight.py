"""Đề xuất vị trí cho các măng xông "thẳng/nối" chỉ có trong KML (không có sơ đồ MX, không có trong đường đi).
Ý tưởng: mỗi link có một chuỗi cáp–MX; chiếu các điểm biết toạ độ (trạm, MX có tên trong KML) lên đường KML của đoạn,
điểm chưa biết toạ độ được nội suy theo chiều dài cáp. MX thẳng nằm giữa hai đầu của cáp nào (cách tuyến < 60 m) thì đề xuất nằm trên cáp đó.
Chỉ là đề xuất để người dùng xác nhận; không đổi dữ liệu."""
import math,re,unicodedata
K=math.cos(10.69*math.pi/180)
pr=lambda lo,la:((lo-106.7)*K*111320,-(la-10.69)*110570)
def norm(s):
    s=unicodedata.normalize('NFD',s.lower());s=''.join(c for c in s if unicodedata.category(c)!='Mn').replace('đ','d')
    s=re.sub(r'\b(mx|tram|thang|nhap|noi|dai|truc)\b',' ',s);return re.sub(r'[^a-z0-9/\-]+',' ',s).strip()
def proj(pm,p):
    best=(1e9,0,0);cum=0
    for i in range(1,len(pm)):
        (x1,y1),(x2,y2)=pm[i-1],pm[i];dx,dy=x2-x1,y2-y1;l2=dx*dx+dy*dy;t=max(0,min(1,((p[0]-x1)*dx+(p[1]-y1)*dy)/l2)) if l2 else 0
        q=(x1+t*dx,y1+t*dy);dd=math.hypot(p[0]-q[0],p[1]-q[1]);l=math.sqrt(l2)
        if dd<best[0]:best=(dd,cum+t*l,0)
        cum+=l
    return best[0],best[1],cum
def at(pm,pos):
    cum=0
    for i in range(1,len(pm)):
        l=math.hypot(pm[i][0]-pm[i-1][0],pm[i][1]-pm[i-1][1])
        if cum+l>=pos or i==len(pm)-1:
            t=(pos-cum)/(l or 1);t=max(0,min(1,t));return (pm[i-1][0]+t*(pm[i][0]-pm[i-1][0]),pm[i-1][1]+t*(pm[i][1]-pm[i-1][1]))
        cum+=l
def suggest(d):
    kml={c['name']:pr(c['lon'],c['lat']) for c in d['closures']};nodes={k:pr(v['lon'],v['lat']) for k,v in d['nodes'].items()}
    cab=d['phys_cables'];segs={s['id']:[pr(a,b) for a,b in s['polyline']] for s in d['segments']}
    stepmx=sorted({s['at'] for lk in d['paths'] for s in lk['steps'] if s['t']=='mx'})
    alias={}
    for m in stepmx:
        if m in kml:alias[m]=m;continue
        c=[x for x in kml if x not in stepmx and norm(x)==norm(m)];alias[m]=c[0] if c else None
    known=lambda n:nodes.get(n) or kml.get(n) or (kml.get(alias.get(n)) if alias.get(n) else None) or (nodes.get(re.search(r'\b(HNB\d+|NBE\d+)\b',n).group(1)) if re.search(r'\b(HNB\d+|NBE\d+)\b',n) else None)
    placed=set(alias.values())|set(stepmx)|{c for c in kml if c.startswith('MX_')}
    todo=[c for c in kml if c not in placed]
    cand={x:{} for x in todo};est={}
    for lk in d['paths']:
        pm=segs.get(lk['id'])
        if not pm:continue
        cs=[s for s in lk['steps'] if s['t']=='cable']
        if not cs:continue
        nodes_=[cab[cs[0]['cable']]['frm']] ;seq=[]
        # chuỗi nút theo thứ tự đi qua
        chain=[];cur=None
        for s in cs:
            c=cab[s['cable']]
            if cur is None:
                a,b=c['frm'],c['to']
                nxt=[x for x in cs[1:2]];
                if nxt:
                    c2=cab[nxt[0]['cable']]
                    if c['frm'] in (c2['frm'],c2['to']):a,b=c['to'],c['frm']
                chain=[a,b];cur=b
            else:
                far=c['to'] if c['frm']==cur else c['frm'];chain.append(far);cur=far
        lens=[cab[s['cable']]['len_m'] for s in cs]
        pos=[]
        for n in chain:
            p=known(n);pos.append(proj(pm,p)[1] if p and proj(pm,p)[0]<150 else None)
        # nội suy
        i=0
        while i<len(pos):
            if pos[i] is None:
                j=i
                while j<len(pos) and pos[j] is None:j+=1
                if i>0 and j<len(pos):
                    p0,p1=pos[i-1],pos[j];tl=sum(lens[i-1:j]) or 1;acc=0
                    for q in range(i,j):acc+=lens[q-1];pos[q]=p0+(p1-p0)*acc/tl;est.setdefault(chain[q],[]).append((lk['id'],pos[q]))
                i=j
            else:i+=1
        for q,s in enumerate(cs):
            if pos[q] is None or pos[q+1] is None:continue
            lo,hi=sorted((pos[q],pos[q+1]));c=cab[s['cable']]
            for x in todo:
                dd,al,_=proj(pm,kml[x])
                if dd<60 and lo-20<=al<=hi+20:
                    frm_first=pos[q]<=pos[q+1]
                    off=(al-pos[q])/((pos[q+1]-pos[q]) or 1)*c['len_m']
                    off=max(0,min(c['len_m'],off))
                    if chain[q]!=c['frm']:off=c['len_m']-off
                    cand[x].setdefault(s['cable'],dict(cable=s['cable'],frm=c['frm'],to=c['to'],fo=c['fo'],len_m=c['len_m'],off_m=round(off),lat_m=round(dd),links=[]))['links'].append(lk['id'])
    # MX trong đường đi chưa có toạ độ KML: ước lượng toạ độ rồi so với các điểm KML chưa gắn
    guess={}
    for m in stepmx:
        if alias.get(m):continue
        e=est.get(m)
        if not e:continue
        lid,p=e[0];xy=at(segs[lid],p);best=sorted((math.hypot(xy[0]-kml[x][0],xy[1]-kml[x][1]),x) for x in todo)[:2]
        guess[m]=[(x,round(dd)) for dd,x in best if dd<300]
    out=[]
    for x in todo:
        m=re.findall(r'(\d+)-(\d+)',x);pair={f'HNB{int(a):03d}' for a,b in m for a in (a,b)}
        cs=list(cand[x].values())
        for c in cs:
            st={re.search(r'HNB\d+',c['frm']).group(0) if re.search(r'HNB\d+',c['frm']) else None,re.search(r'HNB\d+',c['to']).group(0) if re.search(r'HNB\d+',c['to']) else None}
            c['pair_match']=bool(pair) and pair<=st
        if pair and any(c['pair_match'] for c in cs):cs=[c for c in cs if c['pair_match']];conf='tên trạm khớp'
        elif len(cs)==1:conf='vị trí (1 cáp)'
        elif cs:conf='vị trí (nhiều cáp ở ranh giới — cần chọn)'
        else:conf='không xác định'
        for c in cs:c['links']=sorted(set(c['links']))
        mm=[k_ for k_,v in guess.items() if any(g[0]==x for g in v)]
        out.append(dict(name=x,lat=d['closures'][[c['name'] for c in d['closures']].index(x)]['lat'],lon=d['closures'][[c['name'] for c in d['closures']].index(x)]['lon'],conf=conf,cables=cs,maybe_same_as=[dict(mx=k_,dist_m=dict(guess[k_])[x]) for k_ in mm]))
    return dict(items=out,alias={k:v for k,v in alias.items() if v and v!=k},unlocated=[m for m in stepmx if not alias.get(m)])
if __name__=='__main__':
    import model,json
    r=suggest(model.build())
    print('alias:',r['alias'])
    for i in r['items']:print(i['name'],'|',i['conf'],'|',[(c['cable'],c['off_m'],c['lat_m']) for c in i['cables']],'|',i['maybe_same_as'])
