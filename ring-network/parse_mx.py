"""Đọc sơ đồ măng xông (sheet 'MX' của MX__NHA_BE.xlsx) -> măng xông / cáp / core / nhãn / trạm.
Quy ước bố cục (suy ra từ sơ đồ): tiêu đề măng xông là khối lớn ở giữa; mỗi cáp là một hàng (hoặc cột) số core
quay nhãn về phía khối măng xông, tiêu đề cáp nằm phía ngoài; nhãn chữ = nhóm hàn; tên trạm (HNBxxx) nằm sát nhãn.
Chạy: python3 parse_mx.py <MX.xlsx> <out.json>  (chỉ trích nguyên văn, không sửa số liệu)"""
import json,re,sys,unicodedata
import openpyxl
from openpyxl.utils import get_column_letter as L
nf=lambda s:unicodedata.normalize('NFC',str(s)).strip()
STN=re.compile(r'^(HNB\d+|AGG\S*|NBE\d+|LACG\d+|TTC|MTC.*|ODF.*)$',re.I)

def parse(path):
    ws=openpyxl.load_workbook(path)['MX']
    cells={};span={}
    for m in ws.merged_cells.ranges:
        for r in range(m.min_row,m.max_row+1):
            for c in range(m.min_col,m.max_col+1):span[(r,c)]=(m.min_row,m.min_col,m.max_row,m.max_col)
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None and nf(c.value)!='':cells[(c.row,c.column)]=nf(c.value)
    box=lambda r,c:span.get((r,c),(r,c,r,c))
    titles=[]
    for (r,c),v in cells.items():
        if re.match(r'[\s/]*MX_',v) and box(r,c)[2]>box(r,c)[0]:
            name=re.match(r'[\s/]*(MX_[^:\n]+?)\s*(?::|\n|$)',v).group(1).strip()
            titles.append(dict(name=name,box=box(r,c),text=v.replace('\n',' / ')))
    seen={}
    for t in sorted(titles,key=lambda t:(t['name'],-t['box'][1])):
        if t['name'] in seen:
            t['name']='MX_NVT_03B' if t['name']=='MX_NVT_03A' else t['name']+' (2)'
        else:seen[t['name']]=t['box'][1]
    heads=[]
    for (r,c),v in cells.items():
        if 'CÁP' in v.upper() and 'FO' in v.upper() and not re.match(r'[\s/]*MX_',v) and (r,c)==box(r,c)[:2]:heads.append(dict(box=box(r,c),text=v.replace('\n',' / ')))
    runs=[]
    for (r,c),v in sorted(cells.items()):
        if v!='1':continue
        for kind in('h','v'):
            n=1
            while cells.get((r,c+n) if kind=='h' else (r+n,c))==str(n+1):n+=1
            if n>=2:runs.append(dict(kind=kind,r=r,c=c,n=n))
    # hàng số core bị hoán vị: các ô số liền nhau tạo thành hoán vị của 1..n (n>=12) nhưng không bắt đầu bằng 1
    rowsn={}
    for (r,c),v in cells.items():
        if v.isdigit():rowsn.setdefault(r,[]).append(c)
    for r,cs in rowsn.items():
        cs.sort();seg=[cs[0]]
        for c in cs[1:]+[None]:
            if c is not None and c==seg[-1]+1:seg.append(c);continue
            vals=[int(cells[(r,x)]) for x in seg]
            if len(seg)>=12 and sorted(vals)==list(range(1,len(seg)+1)) and vals[0]!=1:
                runs.append(dict(kind='h',r=r,c=seg[0],n=len(seg),nums=vals))
            if c is not None:seg=[c]
    # bỏ các run con nằm gọn trong một hàng số hoán vị
    perm=[x for x in runs if x.get('nums')]
    def inside(x):
        return any(y is not x and y['kind']==x['kind'] and y['r']==x['r'] and y['c']<=x['c'] and y['c']+y['n']>=x['c']+x['n'] and not x.get('nums') for y in perm)
    runs=[x for x in runs if not inside(x)]
    lab=re.compile(r'^([A-Za-z]\d?|HƯ|Hư|hư|HU)$')
    good=[]
    for run in runs:
        r,c,n,k=run['r'],run['c'],run['n'],run['kind'];best=None
        for sgn in(1,-1):
            labs=[cells.get((r+sgn,c+i) if k=='h' else (r+i,c+sgn),'') for i in range(n)]
            cnt=sum(1 for x in labs if lab.match(x))
            if cnt and (best is None or cnt>best[0]):best=(cnt,sgn,labs)
        if best:_,sgn,labs=best
        else:sgn,labs=0,['']*n
        st=[''] *n
        for i in range(n):
            if not sgn:break
            rr,cc=(r+2*sgn,c+i) if k=='h' else (r+i,c+2*sgn);b=box(rr,cc);v=cells.get((b[0],b[1]),'')
            if STN.match(v):st[i]=v
        run.update(sgn=sgn,labels=[x.upper() if lab.match(x) else '' for x in labs],stations=st)
        run['rb']=(r,c,r,c+n-1) if k=='h' else (r,c,r+n-1,c)
        good.append(run)
    def hdr_for(run):
        r0,c0,r1,c1=run['rb'];sgn=run['sgn'];best=None
        for h in heads:
            hr0,hc0,hr1,hc1=h['box']
            if run['kind']=='h':
                if not(hc0<=c1 and hc1>=c0):continue
                g=(r0-hr1) if sgn==1 else (hr0-r1) if sgn==-1 else min(r0-hr1 if r0-hr1>=1 else 99,hr0-r1 if hr0-r1>=1 else 99)
            else:
                if not(hr0<=r1 and hr1>=r0):continue
                g=(c0-hc1) if sgn==1 else (hc0-c1) if sgn==-1 else min(c0-hc1 if c0-hc1>=1 else 99,hc0-c1 if hc0-c1>=1 else 99)
            if 1<=g<=2 and (best is None or g<best[0]):best=(g,h)
        return best[1] if best else None
    for run in good:run['head']=hdr_for(run)
    # nếu một tiêu đề có run có nhãn thì bỏ các run không nhãn cùng tiêu đề (vd hàng số ODF phụ)
    byh={}
    for x in good:
        if x['head']:byh.setdefault(x['head']['box'],[]).append(x)
    drop=set()
    for k,v in byh.items():
        if any(any(l for l in x['labels']) for x in v):
            for x in v:
                if not any(l for l in x['labels']):drop.add(id(x))
    good=[x for x in good if id(x) not in drop]
    good=[x for x in good if x['sgn'] or x['head']]
    def gap(a,b):
        dr=max(a[0]-b[2],b[0]-a[2],0);dc=max(a[1]-b[3],b[1]-a[3],0);return dr+dc
    cables=[];bykey={}
    for run in sorted(good,key=lambda x:(x['r'],x['c'])):
        h=run['head'];key=h['box'] if h else ('run',run['r'],run['c'])
        t=min(titles,key=lambda t:gap(run['rb'],t['box']))
        if key not in bykey:
            bykey[key]=dict(mx=t['name'],header=h['text'] if h else '',kind=run['kind'],cell=f"{L(run['c'])}{run['r']}",tubes=[]);cables.append(bykey[key])
        bykey[key]['tubes'].append(dict(cell=f"{L(run['c'])}{run['r']}",labels=run['labels'],stations=run['stations'],nums=run.get('nums')))
    notes=[(f'{L(c)}{r}',v.replace('\n',' ')) for (r,c),v in cells.items() if re.search(r'Chéo|swap|Core \d|hàn vào|MTC|TTC',v) and 'CÁP' not in v.upper() and len(v)<80]
    return dict(titles=[dict(name=t['name'],text=t['text']) for t in titles],cables=cables,notes=notes,
                headers_unused=[h['text'][:60] for h in heads if not any(c['header']==h['text'] for c in cables)])
if __name__=='__main__':
    res=parse(sys.argv[1]);json.dump(res,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
    print(len(res['titles']),'MX',len(res['cables']),'cáp;',sum(1 for c in res['cables'] if not c['header']),'cáp chưa có tiêu đề;',len(res['headers_unused']),'tiêu đề chưa gán')
