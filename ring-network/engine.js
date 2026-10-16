/* Động cơ tính toán mạng ring (JS) — bản port của model.py để HTML tự tính lại khi sửa dữ liệu.
   Đầu vào RAW = {static:{...}, layer:{cables,links,steps,labels}}; đầu ra D (xem cuối file).
   Không dùng DOM: chạy được trong trình duyệt và Node (kiểm thử đối chiếu với Python). */
(function(root){
'use strict';
const CFG={drop_max_m:300,drop_min_fo:12};
const toInt=x=>parseInt(x,10);
function toCores(v){ if(Array.isArray(v))return v.map(Number); if(v===null||v===undefined||v==='')return []; return String(v).split(/[,+; ]+/).filter(s=>s!=='').map(Number); }
function toNum(v){ if(v===null||v===undefined||v==='')return null; const n=Number(String(v).replace(',','.')); return isNaN(n)?null:n; }
function parseEnds(s){ const o={}; if(!s)return o; String(s).split(';').forEach(p=>{p=p.trim(); const i=p.indexOf('='); if(i>0)o[p.slice(0,i).trim()]=p.slice(i+1).trim();}); return o; }
function parseSubst(s){ if(!s)return null; const o={}; String(s).split(/[;,]/).forEach(p=>{const[a,b]=p.split(':'); if(a&&b)o[a.trim()]=Number(b);}); return Object.keys(o).length?o:null; }
const isHu=s=>/(^|[^\p{L}\p{N}_])h[uư]($|[^\p{L}\p{N}_])|\[hư\]/u.test(String(s).toLowerCase());
function rng(xs){ xs=[...new Set(xs)].sort((a,b)=>a-b); if(!xs.length)return ''; const out=[]; let st=xs[0],pv=xs[0];
  for(let i=1;i<=xs.length;i++){ const x=xs[i]; if(x!==undefined&&x===pv+1){pv=x;continue;} out.push(st===pv?String(st):st+'-'+pv); if(x!==undefined){st=pv=x;} }
  return out.join(','); }
function stationOf(name){ const n=String(name).toUpperCase(); if(n.startsWith('HNB')){const m=n.match(/^HNB\d+/); return m?m[0]:null;}
  if(n.includes('NBE22'))return 'NBE22'; if(n.includes('NBE12')||n.includes('VNPT LONG THỚI'))return 'NBE12'; return null; }

/* ---- ghép nhãn: cùng nhãn = cùng nhóm hàn; sợi nhỏ hàn sợi nhỏ ---- */
function splicePairs(ends){ // ends: [[id,[labels...]],...]
  const pairs=[],warn=[]; const labs=new Set(); ends.forEach(([e,v])=>v.forEach(l=>{if(l&&l!=='HƯ')labs.add(l);}));
  [...labs].sort().forEach(lab=>{
    const pos=[]; ends.forEach(([e,v])=>{ if(v.includes(lab))pos.push([e,v.map((l,i)=>l===lab?i+1:0).filter(x=>x)]); });
    if(pos.length===1){warn.push(`nhãn ${lab}: chỉ có ở một đầu cáp (${pos[0][0]})`);return;}
    if(pos.length>2){warn.push(`nhãn ${lab}: có ở ${pos.length} đầu cáp, cần chỉ định cặp`);return;}
    const [a,pa]=pos[0],[b,pb]=pos[1]; const bal=pa.length===pb.length;
    if(!bal)warn.push(`nhãn ${lab}: số sợi khác nhau (${a}:${pa.length} vs ${b}:${pb.length})`);
    const n=Math.min(pa.length,pb.length); for(let i=0;i<n;i++)pairs.push({label:lab,a,core_a:pa[i],b,core_b:pb[i],balanced:bal});
  });
  return {pairs,warn};
}
function checkSplice(pairs,a,ca,b,cb,subst,nominalB){
  if(!a||!b)return ['chưa có sơ đồ','không xác định cáp trong sơ đồ MX'];
  const m=new Map();
  pairs.forEach(p=>{ if(p.a===a&&p.b===b)m.set(p.core_a,[p.core_b,p.label]); else if(p.a===b&&p.b===a)m.set(p.core_b,[p.core_a,p.label]); });
  if(!ca.some(c=>m.has(c)))return ['chưa có nhãn','sơ đồ MX chưa ghi nhãn cho các core này'];
  const bad=[]; let ok=true;
  for(let i=0;i<Math.min(ca.length,cb.length);i++){ const x=ca[i],y=cb[i]; if(m.has(x)&&m.get(x)[0]===y)continue; ok=false; bad.push(`core ${x}→${m.has(x)?m.get(x)[0]:'?'} (sơ đồ) ≠ ${y} (mô tả)`); }
  if(ok)return ['khớp sơ đồ','nhãn '+[...new Set(ca.filter(x=>m.has(x)).map(x=>m.get(x)[1]))].sort().join(',')];
  if(subst&&nominalB){ const act=nominalB.map(n=>subst[String(n)]!==undefined?subst[String(n)]:n);
    const setCb=new Set(cb), setM=new Set(ca.filter(x=>m.has(x)).map(x=>m.get(x)[0]));
    if(act.length===cb.length&&act.every((v,i)=>v===cb[i])&&setCb.size===setM.size&&[...setCb].every(v=>setM.has(v)))
      return ['khớp sơ đồ (thay core hư)','thiết kế '+ca.map((x,i)=>`${x}↔${nominalB[i]}`).join('+')+'; thực tế '+ca.map((x,i)=>`${x}↔${cb[i]}`).join('+')]; }
  if(ca.every(x=>m.has(x))){ const sm=new Set(ca.map(x=>m.get(x)[0])), sc=new Set(cb); if(sm.size===sc.size&&[...sm].every(v=>sc.has(v)))return ['khớp nhóm, THỨ TỰ KHÁC','cùng nhóm core: '+bad.join('; ')]; }
  return ['KHÁC sơ đồ',bad.join('; ')];
}

function compute(RAW){
  const S=RAW.static,L=RAW.layer,CF=S.config||CFG;
  const drop_max=CF.drop_max_m||300, drop_min=CF.drop_min_fo||12;
  /* --- cáp --- */
  const cables={}; L.cables.forEach(r=>{ cables[r.id]={id:r.id,name:r.name||'',fo:toInt(r.fo),frm:r.frm||'',to:r.to||'',len_m:toNum(r.len_m)||0,so_row:r.so_row||null,
     ma_cap:r.ma_cap||'',cs_dau:r.cs_dau===undefined||r.cs_dau===null?'':String(r.cs_dau),cs_cuoi:r.cs_cuoi===undefined||r.cs_cuoi===null?'':String(r.cs_cuoi),src:r.src||'',so_dau_cuoi:r.so_dau_cuoi||'',ends:parseEnds(r.ends)}; });
  const omap=S.odf_core_map; const omapNb={}; Object.entries(omap['ODF-01 NBE12']).forEach(([k,v])=>omapNb[Number(k)]=v);
  /* --- nhãn sơ đồ MX (gốc) --- */
  const mxcaps=S.mxcap, byCap={}; S.mxcore.forEach(r=>{(byCap[r.cap_id]=byCap[r.cap_id]||[]).push(r);});
  const mxList=[...new Set(mxcaps.map(c=>c.mx))];
  const mxpairs=[],mxwarn=[];
  mxList.forEach(mx=>{ const ids=mxcaps.filter(c=>c.mx===mx).map(c=>c.cap_id); const ends=[],info={};
    ids.forEach(i=>{ const rows=byCap[i]||[]; const n=Math.max(...rows.map(r=>toInt(r.core))); const arr=new Array(n).fill(''); info[i]={};
      rows.forEach(r=>{arr[toInt(r.core)-1]=r.nhan; info[i][toInt(r.core)]=r;}); ends.push([i,arr]); });
    const {pairs,warn}=splicePairs(ends);
    pairs.forEach(p=>{ const ra=info[p.a][p.core_a],rb=info[p.b][p.core_b]; mxpairs.push({mx,label:p.label,a:p.a,core_a:p.core_a,color_a:ra.mau_soi,tube_a:ra.ong,b:p.b,core_b:p.core_b,color_b:rb.mau_soi,tube_b:rb.ong,station:ra.tram||rb.tram||'',balanced:p.balanced}); });
    warn.forEach(w=>mxwarn.push([mx,w]));
    ends.forEach(([i,arr])=>{ if(!arr.some(x=>x)){const c=mxcaps.find(x=>x.cap_id===i); mxwarn.push([mx,`${c.o_goc}: chưa ghi nhãn core (chưa có dữ liệu phối)`]);} });
  });
  /* --- nhãn nhập tay (lớp sửa) --- */
  const labs=(L.labels||[]).map(r=>({mx:r.mx,cable:r.cable,core:toInt(r.core),nhan:(r.nhan||'').trim(),tram:(r.tram||'').trim(),hu:!!(r.hu&&String(r.hu)!=='0')}));
  const ovPairs=[]; const grp={};
  labs.forEach(r=>{ if(r.nhan){const k=r.mx+'\u0000'+r.nhan;(grp[k]=grp[k]||[]).push(r);} });
  Object.entries(grp).forEach(([k,rs])=>{ const [mx,lab]=k.split('\u0000'); const by={}; rs.forEach(r=>{(by[r.cable]=by[r.cable]||[]).push(r);});
    const keys=Object.keys(by).sort(); if(keys.length!==2)return; const A=by[keys[0]].sort((x,y)=>x.core-y.core),B=by[keys[1]].sort((x,y)=>x.core-y.core);
    for(let i=0;i<Math.min(A.length,B.length);i++)ovPairs.push({mx,label:lab,a:'CAB:'+keys[0],core_a:A[i].core,b:'CAB:'+keys[1],core_b:B[i].core,station:A[i].tram||B[i].tram||'',source:'nhập tay'}); });
  /* --- đường đi --- */
  const paths=[]; L.links.forEach(lk=>{
    let tot=0; const steps=[]; const raw=L.steps.filter(s=>s.link===lk.id).sort((a,b)=>toInt(a.seq)-toInt(b.seq));
    raw.forEach(s=>{ const t=s.t; const st={t,at:s.at||'',name:s.name||'',note:s.note||'',odf_ref:s.odf_ref||''};
      if(t==='odf'){ st.cores=toCores(s.cores); if(st.odf_ref&&omap[st.odf_ref]){const inv={}; Object.entries(omap[st.odf_ref]).forEach(([k,v])=>inv[v]=Number(k)); st.ports=st.cores.map(c=>inv[c]!==undefined?inv[c]:c);} }
      else if(t==='cable'){ st.cable=s.cable; st.cores=toCores(s.cores); const c=cables[s.cable]; if(c){tot+=c.len_m; Object.assign(st,{name:c.name,fo:c.fo,frm:c.frm,to:c.to,len_m:c.len_m,src:c.src,cum:tot});} }
      else if(t==='mx'){ st.a_cable=s.a_cable; st.b_cable=s.b_cable; st.cores_a=toCores(s.cores_a); st.cores_b=toCores(s.cores_b); st.subst=parseSubst(s.subst); st.nominal_b=s.nominal_b?toCores(s.nominal_b):null;
        const ea=(cables[st.a_cable]&&cables[st.a_cable].ends[st.at])||('CAB:'+st.a_cable), eb=(cables[st.b_cable]&&cables[st.b_cable].ends[st.at])||('CAB:'+st.b_cable);
        let [ck,dt]=checkSplice(mxpairs,ea,st.cores_a,eb,st.cores_b,st.subst,st.nominal_b);
        if(ck.startsWith('chưa')&&ovPairs.length){ const [c2,t2]=checkSplice(ovPairs,'CAB:'+st.a_cable,st.cores_a,'CAB:'+st.b_cable,st.cores_b,st.subst,st.nominal_b); if(!c2.startsWith('chưa')){ck=c2+' (nhãn nhập tay)';dt=t2;} }
        st.check=ck; st.check_detail=dt; }
      else { st.cores=toCores(s.cores); }
      steps.push(st); });
    let bb=toNum(lk.bbnt_otdr_m); if(bb===null){ const sg=S.segments.find(x=>x.id===lk.id); bb=sg&&sg.km_otdr?Math.round(sg.km_otdr*1000):null; }
    const odfO=(lk.odf_otdr_m===undefined||lk.odf_otdr_m===null||lk.odf_otdr_m==='')?null:String(lk.odf_otdr_m).split(/[\/,; ]+/).filter(Boolean).map(Number);
    const ref=(odfO&&odfO[0])||bb||null;
    const dc=(lk.design_cables?String(lk.design_cables).split(/[,; ]+/).filter(Boolean):[]); const dz=dc.reduce((a,c)=>a+(cables[c]?cables[c].len_m:0),0)||null;
    paths.push({design_m:dz,ring:lk.ring,id:lk.id,frm:lk.frm,to:lk.to,total_m:tot,bbnt_otdr_m:bb,rerouted:!!(lk.rerouted&&String(lk.rerouted)!=='0'),note:lk.note||'',odf_otdr_m:odfO,ref_m:ref,complete:!(String(lk.complete)==='0'||lk.complete===false),steps});
  });
  /* --- AGG ODF sử dụng --- */
  const AGG_ODF={C01:['phai','ODF-02'],C22:['phai','ODF-01'],C35:['trai','ODF-01'],C17:['trai','ODF-02']};
  const other={}, linkport=[];
  Object.entries(AGG_ODF).forEach(([cid,[side,odfn]])=>{ S.odf_agg.forEach(r=>{ if(r.phia!==side||!String(r.odf).startsWith(odfn))return;
      const p=toInt(r.cong); const core=cid==='C22'?(omapNb[p]!==undefined?omapNb[p]:p):p; const dest=String(r.dich||'').trim(), note=String(r.ghi_chu||'').trim();
      if(/HNB\d+\s*ring/.test(dest))linkport.push([cid,p,core,dest.split(/\s+/)[0],dest]);
      else{ const bad=['cot1','cot2','cot3'].some(k=>/^h[uư]$/.test(String(r[k]).trim().toLowerCase())); other[cid+'|'+core]=(dest||'(trống)')+(note?' — '+note:'')+(bad?' [hư]':''); } }); });
  /* --- sổ cái core --- */
  const usage={}; paths.forEach(lk=>lk.steps.forEach(st=>{ if(st.t==='cable')st.cores.forEach(c=>{(usage[st.cable+'|'+c]=usage[st.cable+'|'+c]||[]).push(lk.id);}); }));
  const labmap={}; S.mxcore.forEach(r=>{labmap[r.cap_id+'|'+toInt(r.core)]=[r.nhan,r.tram];});
  const labByCable={}; labs.forEach(r=>{labByCable[r.cable+'|'+r.core+'|'+r.mx]=r;});
  const ledger=[],conflicts=[];
  Object.values(cables).forEach(c=>{ for(let core=1;core<=c.fo;core++){
    const use=[...new Set(usage[c.id+'|'+core]||[])].sort(); const lab=[],tr=[];
    Object.entries(c.ends).forEach(([node,cap])=>{ const l=labmap[cap+'|'+core]; if(l&&(l[0]||l[1])){lab.push(`${node}: ${l[0]||'·'}`); if(l[1])tr.push(l[1]);} });
    let huUser=false;
    Object.keys(c.ends).concat([c.frm,c.to]).forEach(node=>{ const r=labByCable[c.id+'|'+core+'|'+node]; if(r){ if(r.hu)huUser=true; if(r.nhan||r.tram){const t=`${node}: ${r.nhan||'·'}`; if(!lab.includes(t))lab.push(t); if(r.tram)tr.push(r.tram);} } });
    const hu=lab.some(x=>x.includes('HƯ'))||huUser;
    if(use.length>1)conflicts.push([c.id,core,use]);
    const ot=other[c.id+'|'+core]||'';
    const status=(hu||isHu(ot))?'HƯ':(use.length?'dùng '+use.join('+'):(ot?'dùng khác (ODF AGG)':(lab.length?'có nhãn, chưa gán link':'trống/chưa rõ')));
    ledger.push({cable:c.id,name:c.name,route:`${c.frm} → ${c.to}`,core,status,other:ot,labels:lab.join('; '),stations:[...new Set(tr)].join(', '),links:use}); } });
  /* --- đứt cáp --- */
  const ringsDef=S.rings; const segById={}; S.segments.forEach(s=>segById[s.id]=s);
  function simulateCut(cutIds){ const cut=new Set(cutIds),res={};
    Object.entries(ringsDef).forEach(([rid,r])=>{ const segs=S.segments.filter(s=>s.ring===rid&&s.kind==='ring').sort((a,b)=>a.seq-b.seq);
      r.csg.forEach((n,i0)=>{ const i=i0+1; let left=true,right=true; for(let k=0;k<i;k++)if(cut.has(segs[k].id))left=false; for(let k=i;k<segs.length;k++)if(cut.has(segs[k].id))right=false; res[n]=[left?'NBE12':null,right?'NBE22':null]; }); });
    S.segments.forEach(s=>{ if(s.kind==='nhánh cụt'){ const ok=!cut.has(s.id); const p=res[s.a]||[null,null]; res[s.z]=p.map(x=>ok&&x?x:null); } });
    return res; }
  /* --- hồ sơ cáp --- */
  const ledBy={}; ledger.forEach(r=>{(ledBy[r.cable]=ledBy[r.cable]||[]).push(r);});
  const segIds=new Set(S.segments.map(s=>s.id)); const profiles=[];
  Object.values(cables).forEach(c=>{ const rows=ledBy[c.id]||[]; const run={},hu=[],lab=[],free=[],stn={},oth={};
    rows.forEach(r=>{ if(r.other)(oth[r.other]=oth[r.other]||[]).push(r.core);
      if(r.status==='HƯ')hu.push(r.core); else if(r.status.startsWith('dùng khác')){} else if(r.status.startsWith('dùng')){ r.links.forEach(l=>{(run[l]=run[l]||[]).push(r.core);}); }
      else if(r.status.startsWith('có nhãn')){ lab.push(r.core); if(r.stations)(stn[r.stations]=stn[r.stations]||[]).push(r.core); } else free.push(r.core); });
    const links=Object.keys(run).sort(); const cut=links.filter(l=>segIds.has(l)); const res=cut.length?simulateCut(cut):{};
    const lost=Object.keys(res).filter(k=>res[k][0]===null&&res[k][1]===null).sort();
    const runCores=[].concat(...links.map(l=>run[l])).sort((a,b)=>a-b);
    const p={id:c.id,name:c.name,ma_cap:c.ma_cap||'(chưa ghi mã cáp trong sổ)',fo:c.fo,frm:c.frm,to:c.to,len_m:c.len_m,cs_dau:c.cs_dau,cs_cuoi:c.cs_cuoi,so_row:c.so_row,so_dau_cuoi:c.so_dau_cuoi,
      run:links.map(l=>`${rng(run[l])} (${l})`).join('; ')||'—',run_cores:runCores,hu:rng(hu)||'—',other:Object.entries(oth).map(([k,v])=>`${rng(v)}: ${k}`).join('; ')||'—',
      lab:rng(lab)||'—',lab_stations:Object.entries(stn).map(([k,v])=>`${k}: ${rng(v)}`).join('; ')||'—',free:rng(free)||'—',n_free:free.length,links,lost:lost.join(', ')||'—',
      effect:lost.length?'MẤT KẾT NỐI: '+lost.join(', '):(links.length?'các link '+links.join(', ')+' mất một hướng, ring vẫn bảo vệ':'chưa có link mô tả'),link_status:run};
    const stnLike=x=>/^(HNB|NBE|ODF)/.test(x);
    p.n_links=links.length; p.rings=[...new Set(links.map(l=>l.split('-')[0]))].sort(); p.used_cores=runCores.length; p.util=runCores.length/c.fo;
    if(stnLike(c.frm)&&stnLike(c.to))p.kind='giữa hai trạm'; else if((stnLike(c.frm)||stnLike(c.to))&&c.len_m<drop_max)p.kind='cáp vào trạm'; else if(stnLike(c.frm)||stnLike(c.to))p.kind='cáp riêng tới trạm (>=300 m)'; else p.kind='cáp trục';
    p.rule=p.kind==='cáp vào trạm'?(c.fo>=drop_min?'đạt (<300 m, ≥12FO)':'KHÔNG đạt: cáp vào trạm phải ≥12FO'):'—';
    profiles.push(p); });
  /* --- đồ thị core --- */
  const E={}; function addE(c1,k1,c2,k2,mx,src,link){ [[c1,k1,c2,k2],[c2,k2,c1,k1]].forEach(([a,ka,b,kb])=>{ const key=a+'|'+ka+'|'+mx; const lst=E[key]=E[key]||[]; if(!lst.some(x=>x[0]===b&&x[1]===kb))lst.push([b,kb,src,link||'']); }); }
  paths.forEach(lk=>lk.steps.forEach(st=>{ if(st.t==='mx'){ const n=Math.min(st.cores_a.length,st.cores_b.length); for(let i=0;i<n;i++)addE(st.a_cable,st.cores_a[i],st.b_cable,st.cores_b[i],st.at,'mô tả',lk.id); } }));
  Object.entries(S.straight).forEach(([mx,n])=>{ const cs=Object.values(cables).filter(c=>c.frm===mx||c.to===mx); if(cs.length===2){ const [a,b]=cs; for(let i=1;i<=Math.min(n,a.fo,b.fo);i++)addE(a.id,i,b.id,i,mx,'MX thẳng (số mối hàn)'); } });
  const cap2={}; Object.values(cables).forEach(c=>Object.entries(c.ends).forEach(([mx,cap])=>{cap2[cap]=[c.id,mx];}));
  mxpairs.forEach(p=>{ if(p.balanced&&cap2[p.a]&&cap2[p.b]){ const [ca,ma]=cap2[p.a],[cb,mb]=cap2[p.b]; if(ma===mb)addE(ca,p.core_a,cb,p.core_b,ma,'sơ đồ MX'); } });
  ovPairs.forEach(p=>addE(p.a.slice(4),p.core_a,p.b.slice(4),p.core_b,p.mx,'nhập tay'));
  function traceCore(cable,core,fromNode){ const hops=[],srcs=[],links=new Set(); let cur=cable,cc=core,frm=fromNode;
    for(let i=0;i<60;i++){ const c=cables[cur]; const far=c.to===frm?c.frm:c.to; hops.push([cur,cc,far]); const st=stationOf(far); ((ledMap[cur+'|'+cc]||{}).links||[]).forEach(l=>links.add(l));
      if(st)return ['station',st,far,hops,srcs,[...links].sort()];
      const nxt=E[cur+'|'+cc+'|'+far]; if(!nxt)return ['dead',far,far,hops,srcs,[...links].sort()];
      const n=nxt[0]; srcs.push(n[2]); if(n[3])links.add(n[3]); cur=n[0];cc=n[1];frm=far; }
    return ['dead','vòng lặp','',hops,srcs,[...links].sort()]; }
  /* --- core tại trạm --- */
  const ledMap={}; ledger.forEach(r=>ledMap[r.cable+'|'+r.core]=r);
  const op={}; S.odf.forEach(r=>{ const dest=String(r.dest||'').replace('AGG-',''); if(dest){ (op[r.node]=op[r.node]||{}); op[r.node][dest]=(op[r.node][dest]||0)+1; } });
  const useByCable={}; paths.forEach(lk=>lk.steps.forEach(s=>{ if(s.t==='cable'){(useByCable[s.cable]=useByCable[s.cable]||new Set()).add(lk.id);} }));
  const ringIdx=n=>{ if(n==='NBE12')return -1; if(n==='NBE22')return 999; const nd=nodeMap[n]; const ch=nd&&S.rings[nd.ring]?S.rings[nd.ring].csg:[]; const i=ch.indexOf(n); return i<0?null:i; };
  const nodeMap={}; S.nodes.forEach(n=>nodeMap[n.id]=n);
  const pofs={}; new Set(Object.values(cables).flatMap(c=>[stationOf(c.frm),stationOf(c.to)]).filter(x=>x&&x!=='NBE12'&&x!=='NBE22')).forEach(st=>{ const items=[]; let ok=true;
    for(const c of Object.values(cables)){ if(stationOf(c.frm)===st||stationOf(c.to)===st){ const nb=new Set([...(useByCable[c.id]||[])].map(l=>{const lk=paths.find(x=>x.id===l);return lk.frm===st?lk.to:lk.frm;})); if(nb.size!==1){ok=false;break;} const ix=ringIdx([...nb][0]),ix2=ringIdx(st); if(ix===null||ix2===null){ok=false;break;} items.push([ix,c.id,c.fo]); } }
    const nport=S.odf.filter(o=>o.node===st).length; if(ok&&items.length&&items.reduce((a,x)=>a+x[2],0)<=nport){ let off=0; items.sort((x,y)=>x[0]-y[0]||(x[1]<y[1]?-1:x[1]>y[1]?1:0)).forEach(([ix,cid,fo])=>{pofs[st+'|'+cid]=off;off+=fo;}); } });
  const stationCores=[];
  Object.values(cables).forEach(c=>{ [['frm','to'],['to','frm']].forEach(([end,oth2])=>{ const node=c[end]; const st=stationOf(node); if(!st)return;
      const neigh=new Set(); (useByCable[c.id]?[...useByCable[c.id]]:[]).forEach(lid=>{ const lk=paths.find(x=>x.id===lid); const o=(lk.frm===st||stationOf(lk.frm)===st)?lk.to:lk.frm; if(o!==st)neigh.add(o); });
      let ports=null; if(op[st]){ const tot=[...neigh].map(n=>op[st][n]).filter(Boolean); ports=tot.length?tot.reduce((a,b)=>a+b,0):null; }
      for(let core=1;core<=c.fo;core++){ const lr=ledMap[c.id+'|'+core]; let kind,dest,via,srcs,links;
        if(lr.status==='HƯ'){kind='hư';dest='';via='';srcs=[];links=[];}
        else{ const res=traceCore(c.id,core,node); kind=res[0]; dest=res[0]==='station'?res[1]:''; via=res[3].map(h=>h[2]).join('→'); srcs=res[4]; links=res[5]; if(res[0]==='dead')via=res[1]; }
        let port_note=''; if(ports!==null&&core>ports)port_note=`không có cổng ODF (ODF chỉ có ${ports} cổng hướng này)`;
        const srcSet=[...new Set(srcs)].sort(); let text;
        if(kind==='hư')text='HƯ'; else if(kind==='station'){ if(links.length)text='đang chạy link '+links.join(', ')+' → '+dest; else if(srcSet.length&&srcSet.every(x=>x==='MX thẳng (số mối hàn)')&&srcSet.length===1)text='hàn thông (MX thẳng, theo số mối hàn) → '+dest; else if(!srcs.length)text='sợi nối trực tiếp → '+dest+' (chưa rõ đã hàn pigtail ở ODF hai đầu)'; else text='hàn thông theo nhãn sơ đồ → '+dest+' (chưa gán link)'; }
        else text='chưa ghi hàn tại '+via+' (dự phòng / chưa rõ / không hàn)';
        stationCores.push({odf_port:(pofs[st+'|'+c.id]!==undefined)?pofs[st+'|'+c.id]+core:null,text,port_note,odf_ports:ports,station:st,node,cable:c.id,name:c.name,ma_cap:c.ma_cap,fo:c.fo,other_end:c[oth2],core,kind,dest,via,srcs:srcSet,links,status:lr.status}); } }); });
  /* --- bảng ODF AGG --- */
  const aggSpec=[['NBE12','ODF-01 (hướng NB)','C22','phai','ODF-01'],['NBE12','ODF-02 (hướng NVT)','C01','phai','ODF-02'],['NBE22','ODF-01 (cs 1816)','C35','trai','ODF-01'],['NBE22','ODF-02 (cs 1288)','C17','trai','ODF-02']];
  const aggOdf=[]; aggSpec.forEach(([st,name,cid,side,pre])=>{ const c=cables[cid]; if(!c)return; const node=stationOf(c.frm)===st?c.frm:c.to;
    S.odf_agg.forEach(r=>{ if(r.phia!==side||!String(r.odf).startsWith(pre))return; const p=toInt(r.cong); const core=cid==='C22'?(omapNb[p]!==undefined?omapNb[p]:p):p;
      const res=traceCore(cid,core,node); aggOdf.push({station:st,odf:name,cable:cid,port:p,core,dest:String(r.dich||'').trim(),note:String(r.ghi_chu||'').trim(),kind:res[0],end:res[1],links:res[5],srcs:[...new Set(res[4])].sort()}); }); });
  /* --- kiểm tra ODF AGG ↔ đường đi --- */
  const used={}; paths.forEach(lk=>{ const csg=lk.frm.startsWith('NBE')?lk.to:(lk.to.startsWith('NBE')?lk.frm:null); if(!csg)return; const cabs=lk.steps.filter(s=>s.t==='cable'); if(!cabs.length)return; const end=lk.frm.startsWith('NBE')?cabs[0]:cabs[cabs.length-1]; used[end.cable+'|'+csg+'|'+end.cores.join(',')]=lk.id; });
  const aggCheck=linkport.map(([cid,p,core,csg,dest])=>{ let hit=null; Object.entries(used).forEach(([k,v])=>{ const [c,g,cs]=k.split('|'); if(c===cid&&g===csg&&cs.split(',').map(Number).includes(core))hit=v; }); return [cid,p,core,csg,dest,hit]; });
  /* --- đoạn (trạng thái) --- */
  const segments=S.segments.map(s=>Object.assign({},s,{status:s.db_ref===null||s.db_ref===undefined?'Chưa đo':((s.ok_loss&&s.ok_core)?'Đạt':'Cảnh báo')}));
  return {cables,paths,mxpairs,mxwarn,ovPairs,ledger,conflicts,profiles,stationCores,aggOdf,aggCheck,segments,E,simulateCut,labs,mxList};
}
const api={compute,splicePairs,checkSplice,stationOf,toCores,rng};
if(typeof module!=='undefined'&&module.exports)module.exports=api; else root.RingEngine=api;
})(typeof window!=='undefined'?window:globalThis);
