// ===== phần "liên kết Excel" + giao diện măng xông + sửa dữ liệu =====
let xbytes=null,fh=null,fname='',dirty=false;
function esc_(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
const FCOL=['#2f6fdb','#f28c28','#2da44e','#8b5a2b','#8a8f98','#ffffff'];
const fcol=n=>FCOL[(n-1)%6],tube=n=>Math.ceil(n/6);
const hue=l=>{let h=0;for(const ch of String(l))h=(h*31+ch.charCodeAt(0))%360;return h};
const lcol=l=>`hsl(${hue(l)} 65% 45%)`;
const ti=x=>parseInt(x,10);
function setDirty(v){dirty=v;renderSrc()}
function renderSrc(){$('#src').innerHTML=(fname?`Nguồn dữ liệu: <b>${esc_(fname)}</b>`:'Nguồn dữ liệu: bản nhúng sẵn trong HTML (bấm “Mở Excel” để nạp file Excel của bạn)')+(dirty?` · <span class="dirty">● có thay đổi chưa lưu</span>`:'')+(fh?' · lưu thẳng vào file':(fname?' · “Lưu” sẽ tải file mới về':''))}
function refresh(){derive();fillCab();upC();upO();renderMxList();if(curMx)renderMx(curMx);draw()}
function touch(){setDirty(true);saveDraft();refresh()}
// ---- mở / lưu Excel
async function loadBytes(b,name,handle){try{const L=await XlsxIO.readLayer(b);if(dirty&&!confirm('Đang có thay đổi chưa lưu. Nạp file Excel sẽ thay thế chúng (bản nháp vẫn được giữ để khôi phục). Tiếp tục?'))return;RAW.layer=L;BASE=JSON.parse(JSON.stringify(L));xbytes=b;fname=name;fh=handle||null;dirty=false;refresh();renderSrc()}catch(e){alert('Không đọc được file: '+e.message)}}
$('#bOpen').onclick=async()=>{
 if(window.showOpenFilePicker){try{const [h]=await showOpenFilePicker({types:[{description:'Excel',accept:{'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':['.xlsx']}}]});const f=await h.getFile();await loadBytes(new Uint8Array(await f.arrayBuffer()),f.name,h)}catch(e){if(e.name!=='AbortError')alert(e.message)}}
 else $('#fIn').click()};
$('#fIn').onchange=async e=>{const f=e.target.files[0];if(f)await loadBytes(new Uint8Array(await f.arrayBuffer()),f.name,null);e.target.value=''};
$('#bSave').onclick=async()=>{
 if(!xbytes){alert('Chưa mở file Excel. Bấm “Mở Excel” và chọn ring_network_NhaBe.xlsx trước; khi lưu, các sheet DL_* trong chính file đó được cập nhật, các sheet khác giữ nguyên.');return}
 try{const out=await XlsxIO.writeLayer(xbytes,RAW.layer);
  if(fh){const w=await fh.createWritable();await w.write(out);await w.close();xbytes=out;setDirty(false);alert('Đã lưu vào '+fname)}
  else{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([out],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));a.download=fname||'ring_network_NhaBe.xlsx';document.body.appendChild(a);a.click();a.remove();xbytes=out;setDirty(false)}
 }catch(e){alert('Lưu lỗi: '+e.message)}};
addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});
// ---- sửa cáp
function cabRow(id){return RAW.layer.cables.find(c=>String(c.id)===id)}
function cabEdit(c){const r=cabRow(c.id)||{};const mxs=Object.keys((E.cables[c.id]||{}).ends||{});
 return `<h4 style="margin:12px 0 4px">Sửa thông tin cáp (ghi vào sheet DL_Cáp)</h4>
 <div class="fld"><label>Mã cáp</label><input type="text" id="ce_ma" value="${esc_(r.ma_cap)}" placeholder="vd. FOCAL 9/2020"></div>
 <div class="fld"><label>Chỉ số đầu (m)</label><input type="text" id="ce_d" value="${esc_(r.cs_dau)}"></div>
 <div class="fld"><label>Chỉ số cuối (m)</label><input type="text" id="ce_c" value="${esc_(r.cs_cuoi)}"></div>
 <div class="fld"><label>Chiều dài (m)</label><input type="number" id="ce_l" value="${esc_(r.len_m)}"></div>
 <div class="row"><button onclick="saveCab('${c.id}')" class="on">Lưu thay đổi</button><span class="mut">Cập nhật tức thì mọi bảng; nhớ bấm “Lưu Excel”.</span></div>
 ${mxs.length?'<div class="mut">Măng xông trên cáp: '+mxs.map(m=>`<a href="#" onclick="showMx('${m.replace(/'/g,"\\'")}');return false">${esc_(m)}</a>`).join(' · ')+'</div>':''}`}
function saveCab(id){const r=cabRow(id);if(!r)return;r.ma_cap=$('#ce_ma').value.trim();r.cs_dau=$('#ce_d').value.trim();r.cs_cuoi=$('#ce_c').value.trim();const l=$('#ce_l').value;if(l!=='')r.len_m=+l;touch()}
// ---- MX: dữ liệu
const capRec={};RAW.static.mxcap.forEach(c=>capRec[c.cap_id]=c);
const diag={};RAW.static.mxcore.forEach(r=>{(diag[r.cap_id]=diag[r.cap_id]||{})[ti(r.core)]=r});
function allMx(){const m=new Map();const add=(n,k)=>{if(!m.has(n))m.set(n,{name:n,tags:new Set()});m.get(n).tags.add(k)};
 E.mxList.forEach(n=>add(n,'sơ đồ'));RAW.static.closures.forEach(c=>add(c.name,'KML'));
 E.paths.forEach(p=>p.steps.forEach(s=>{if(s.t=='mx')add(s.at,'đường đi')}));Object.keys(RAW.static.straight).forEach(n=>add(n,'MX thẳng'));
 Object.values(E.cables).forEach(c=>Object.keys(c.ends||{}).forEach(n=>add(n,'cáp')));return [...m.values()].sort((a,b)=>a.name.localeCompare(b.name,'vi'))}
function mxCables(name){const ids=new Set();Object.values(E.cables).forEach(c=>{if((c.ends||{})[name])ids.add(c.id)});
 const run={};E.paths.forEach(p=>p.steps.forEach(s=>{if(s.t=='mx'&&s.at==name){[[s.a_cable,s.cores_a],[s.b_cable,s.cores_b]].forEach(([cb,cs])=>{if(!cb)return;ids.add(cb);cs.forEach(c=>{((run[cb]=run[cb]||{})[c]=run[cb][c]||[]).push(p.id)})})}}));
 if(RAW.static.straight[name]!==undefined)Object.values(E.cables).forEach(c=>{if(c.frm===name||c.to===name)ids.add(c.id)});
 return [...ids].sort().map(id=>{const c=E.cables[id];const cap=(c.ends||{})[name];const rec=capRec[cap]||{};const dg=diag[cap]||{};
  const ov={};E.labs.forEach(r=>{if(r.mx==name&&r.cable==id)ov[r.core]=r});
  const cores=[];for(let n=1;n<=c.fo;n++){const g=dg[n]||{};const o=ov[n];const lab=o&&o.nhan?o.nhan:(g.nhan||'');
   cores.push({n,ong:g.ong||tube(n),mau:g.mau_soi||'',nhan:lab,tram:(o&&o.tram)||g.tram||'',hu:!!(o&&o.hu)||/^h[ưu]$/i.test(lab),ov:!!o,links:(run[id]||{})[n]||((cap&&cap[0]=='@')?(ledOf(id,n)):[])})}
  return {id,c,cap,huong:rec.huong||'',cores}})}
let _ledE=null,_ledM={};function ledOf(id,n){if(_ledE!==E){_ledE=E;_ledM={};E.ledger.forEach(r=>_ledM[r.cable+'|'+r.core]=r.links||[])}return _ledM[id+'|'+n]||[]}
function mxPairsFor(name,cabs){const idOfCap={};cabs.forEach(x=>{if(x.cap)idOfCap[x.cap]=x.id});const out=[];
 E.mxpairs.forEach(p=>{if(p.mx==name&&idOfCap[p.a]&&idOfCap[p.b])out.push({label:p.label,a:idOfCap[p.a],ca:p.core_a,b:idOfCap[p.b],cb:p.core_b,station:p.station,src:'sơ đồ'+(p.balanced?'':' (không cân)')})});
 E.ovPairs.forEach(p=>{if(p.mx==name)out.push({label:p.label,a:p.a.slice(4),ca:p.core_a,b:p.b.slice(4),cb:p.core_b,station:p.station,src:'nhập tay'})});
 E.paths.forEach(p=>p.steps.forEach(s=>{if(s.t=='mx'&&s.at==name){s.cores_a.forEach((ca,i)=>out.push({label:'',a:s.a_cable,ca,b:s.b_cable,cb:s.cores_b[i],station:p.frm.startsWith('NBE')?p.to:p.frm,src:'đường đi '+p.id}))}}));
 const n=RAW.static.straight[name];if(n!==undefined){const cs=cabs.map(x=>x.c);if(cs.length==2)for(let i=1;i<=Math.min(n,cs[0].fo,cs[1].fo);i++)out.push({label:'',a:cs[0].id,ca:i,b:cs[1].id,cb:i,station:'',src:'MX thẳng'})}
 return out}
// ---- MX: danh sách
let curMx=null,curCore=null,curPair='';
function mxStat(m){const cabs=mxCables(m.name);const lab=cabs.reduce((a,x)=>a+x.cores.filter(c=>c.nhan).length,0);const runs=cabs.reduce((a,x)=>a+x.cores.filter(c=>c.links.length).length,0);const miss=E.paths.some(p=>p.steps.some(s=>s.t=='mx'&&s.at==m.name&&String(s.check).startsWith('chưa')));return {cabs,lab,runs,miss}}
function renderMxList(){const q=($('#mxQ').value||'').toLowerCase().trim(),only=$('#mxOnlyL').checked;
 const L=allMx().map(m=>Object.assign(m,mxStat(m))).filter(m=>(!q||(m.name+' '+m.cabs.map(c=>c.id+' '+c.c.ma_cap+' '+c.c.frm+' '+c.c.to).join(' ')).toLowerCase().includes(q))&&(!only||m.miss));
 $('#mxList').innerHTML=L.map(m=>`<div class="mxi${m.name==curMx?' sel':''}" onclick="goMx('${m.name.replace(/\\/g,'\\\\').replace(/'/g,"\\'")}')"><div class="t">${esc_(m.name)}</div>${[...m.tags].map(t=>`<span class="tag">${t}</span>`).join('')}<div class="mut">${m.cabs.length} cáp · ${m.lab} core có nhãn · ${m.runs} core đang chạy${m.miss?' · <span class="warn">thiếu nhãn</span>':''}</div></div>`).join('')||'<div class="mut">Không có măng xông phù hợp.</div>'}
$('#mxQ').oninput=renderMxList;$('#mxOnlyL').onchange=renderMxList;
function goMx(name){curMx=name;curCore=null;curPair='';goTab('mx');renderMxList();renderMx(name);$('#mxDetail').scrollIntoView({behavior:'smooth',block:'start'})}
// ---- MX: chi tiết
function coreChip(mx,cid,c){const sel=curCore&&curCore[0]==cid&&curCore[1]==c.n;
 return `<div class="cc${c.ov?' ov':''}${c.hu?' hu':''}${c.links.length?' run':''}${sel?' sel':''}" title="${esc_([c.mau,'ống '+c.ong,c.links.join(', ')].filter(Boolean).join(' · '))}" onclick="editCore('${cid}',${c.n})"><div class="n"><i style="background:${fcol(c.n)}"></i>${c.n}</div><div class="l" style="color:${c.nhan?(c.hu?'var(--bad)':lcol(c.nhan)):'var(--mut)'}">${esc_(c.nhan)||'·'}</div><div class="s">${esc_(c.tram)||(c.links.length?c.links[0]:'')}</div></div>`}
function splicesSvg(name,cabs,pairs,A,B){const ca=cabs.find(x=>x.id==A),cb=cabs.find(x=>x.id==B);if(!ca||!cb)return '';
 const ps=pairs.filter(p=>(p.a==A&&p.b==B)||(p.a==B&&p.b==A)).map(p=>p.a==A?p:{label:p.label,a:A,ca:p.cb,b:B,cb:p.ca,station:p.station,src:p.src});
 const rh=17,n=Math.max(ca.c.fo,cb.c.fo),H=n*rh+24,W=360,xa=96,xb=W-96;const seen=new Set();
 let s=`<svg class="mxsvg" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:520px"><text x="${xa-8}" y="11" text-anchor="end" font-weight="700" fill="currentColor">${A}</text><text x="${xb+8}" y="11" font-weight="700" fill="currentColor">${B}</text>`;
 const y=i=>20+(i-1)*rh+rh/2;
 for(let i=1;i<=ca.c.fo;i++){const c=ca.cores[i-1];s+=`<circle cx="${xa}" cy="${y(i)}" r="4.5" fill="${fcol(i)}" stroke="#0007"/><text x="${xa-8}" y="${y(i)+3.5}" text-anchor="end" fill="${c.hu?'#d62839':'currentColor'}">${i}${c.nhan?' '+esc_(c.nhan):''}</text>`}
 for(let i=1;i<=cb.c.fo;i++){const c=cb.cores[i-1];s+=`<circle cx="${xb}" cy="${y(i)}" r="4.5" fill="${fcol(i)}" stroke="#0007"/><text x="${xb+8}" y="${y(i)+3.5}" fill="${c.hu?'#d62839':'currentColor'}">${i}${c.nhan?' '+esc_(c.nhan):''}</text>`}
 ps.forEach(p=>{const k=p.ca+'-'+p.cb+p.src;if(seen.has(k))return;seen.add(k);const col=p.label?lcol(p.label):'#888';const dash=p.src.startsWith('đường đi')?'4 3':p.src=='MX thẳng'?'1 3':'';
  s+=`<line x1="${xa}" y1="${y(p.ca)}" x2="${xb}" y2="${y(p.cb)}" stroke="${col}" stroke-width="2" ${dash?`stroke-dasharray="${dash}"`:''}><title>${A} ${p.ca} ↔ ${B} ${p.cb} · ${esc_(p.label)} · ${esc_(p.src)}</title></line>`});
 return s+'</svg><div class="mut">Nét liền: theo sơ đồ/nhập tay (màu = nhóm nhãn) · nét đứt: theo mô tả đường đi · nét chấm: MX thẳng.</div>'}
function renderMx(name){const cabs=mxCables(name);const pairs=mxPairsFor(name,cabs);const rec=allMx().find(m=>m.name==name);
 const note=RAW.static.closures.find(c=>c.name==name);const steps=[];E.paths.forEach(p=>p.steps.forEach(s=>{if(s.t=='mx'&&s.at==name)steps.push([p,s])}));
 let h=`<div class="card"><div class="row"><h3 style="margin:0;flex:1">${esc_(name)}</h3><button onclick="curMx=null;$('#mxDetail').innerHTML='';renderMxList()">đóng</button></div>
 <div class="mut">${rec?[...rec.tags].join(' · '):''}${note?` · ${note.lat.toFixed(5)}, ${note.lon.toFixed(5)} · <a target="_blank" href="https://maps.google.com/?q=${note.lat},${note.lon}">bản đồ</a>`:''}</div>${note?`<div class="mut">${esc_(note.desc)}</div>`:''}
 ${sugBox(name)}${RAW.static.straight[name]!==undefined?`<div class="mut">MX thẳng: hàn thẳng core i↔i cho <b>${RAW.static.straight[name]}</b> core đầu (theo sổ MX).</div>`:''}`;
 if(!cabs.length)h+='<div class="mut">Chưa gắn cáp nào vào măng xông này (xem sheet DL_Cáp cột “ends”).</div>';
 cabs.forEach(x=>{h+=`<div style="margin-top:10px"><span class="b" style="cursor:pointer" onclick="goCab('${x.id}')">${x.id}</span> <span class="mut">${esc_(x.c.ma_cap||'(chưa mã)')} · ${x.c.fo}FO · ${esc_(x.c.frm)} → ${esc_(x.c.to)}${x.huong?' · hướng '+esc_(x.huong):''} <small>${x.cap&&x.cap[0]=='@'?'(MX thẳng giữa cáp, cách đầu “Từ” ~'+x.cap.slice(1)+' m)':'(đầu '+esc_(x.cap?x.cap.split('|')[1]:'?')+')'}</small></span><div class="cs">${x.cores.map(c=>coreChip(name,x.id,c)).join('')}</div></div>`});
 h+='<div class="leg"><span><i style="background:var(--ok)"></i>core đang chạy link</span><span><i style="background:var(--bad)"></i>hư</span><span style="box-shadow:inset 0 0 0 2px var(--acc);padding:0 4px;border-radius:4px">nhãn nhập tay</span><span>chấm màu = màu sợi (6 màu/ống)</span></div>';
 if(cabs.length>=2){const opts=[];for(let i=0;i<cabs.length;i++)for(let j=i+1;j<cabs.length;j++)opts.push([cabs[i].id,cabs[j].id]);
  if(!curPair||!opts.some(o=>o.join('|')==curPair)){const withP=opts.find(o=>pairs.some(p=>(p.a==o[0]&&p.b==o[1])||(p.a==o[1]&&p.b==o[0])));curPair=(withP||opts[0]).join('|')}
  h+=`<h4 style="margin:12px 0 4px">Hàn nối giữa hai cáp</h4><div class="row"><select onchange="curPair=this.value;renderMx(curMx)">${opts.map(o=>`<option value="${o.join('|')}"${o.join('|')==curPair?' selected':''}>${o[0]} ↔ ${o[1]}</option>`).join('')}</select></div>`+splicesSvg(name,cabs,pairs,...curPair.split('|'))}
 if(pairs.length){const g={};pairs.forEach(p=>{const k=[p.src,p.label,p.a,p.b].join('|');(g[k]=g[k]||[]).push(p)});
  h+='<h4 style="margin:12px 0 4px">Bảng phối core</h4><table><tr><th>Nguồn</th><th>Nhãn</th><th>Cáp A / core</th><th>Cáp B / core</th><th>Trạm</th></tr>'+Object.values(g).map(L=>`<tr><td class="mut">${esc_(L[0].src)}</td><td class="b" style="color:${L[0].label?lcol(L[0].label):'inherit'}">${esc_(L[0].label)}</td><td>${L[0].a}<br><b>${RingEngine.rng(L.map(p=>p.ca))}</b></td><td>${L[0].b}<br><b>${RingEngine.rng(L.map(p=>p.cb))}</b></td><td>${esc_([...new Set(L.map(p=>p.station).filter(Boolean))].join(', '))}</td></tr>`).join('')+'</table>'}
 if(steps.length){h+='<h4 style="margin:12px 0 4px">Link đi qua măng xông này</h4><table><tr><th>Link</th><th>Cáp A / core</th><th>Cáp B / core</th><th>Đối chiếu sơ đồ</th></tr>'+steps.map(([p,s])=>`<tr><td class="b">${p.id}</td><td>${s.a_cable}<br>${s.cores_a.join('+')}</td><td>${s.b_cable}<br>${s.cores_b.join('+')}</td><td class="${/^khớp/.test(s.check)?'ok':/^chưa/.test(s.check)?'warn':'bad'}">${esc_(s.check)}<br><small class="mut">${esc_(s.check_detail||'')}</small></td></tr>`).join('')+'</table>';
  if(steps.some(([p,s])=>/^chưa/.test(s.check)))h+=`<div class="row"><button onclick="suggestLabels('${name.replace(/\\/g,'\\\\').replace(/'/g,"\\'")}')">✨ Đề xuất nhãn từ đường đi</button><span class="mut">Chưa có nhãn → gợi ý nhãn A, B… theo từng link (cùng nhãn = hàn với nhau).</span></div>`}
 const ns=RAW.static.mx_notes;h+='</div><div id="coreEd"></div>';$('#mxDetail').innerHTML=h;if(curCore)editCore(curCore[0],curCore[1],true)}
// ---- sửa nhãn một core
function editCore(cid,n,keep){curCore=[cid,n];const x=mxCables(curMx).find(z=>z.id==cid);const c=x.cores[n-1];const r=RAW.layer.labels.find(l=>l.mx==curMx&&l.cable==cid&&ti(l.core)==n)||{};
 const el=$('#coreEd');if(!el)return;if(!keep)document.querySelectorAll('.cc.sel').forEach(e=>e.classList.remove('sel'));
 el.innerHTML=`<div class="card" style="border-color:var(--warn)"><div class="b">${cid} · core ${n} · ống ${c.ong}${c.mau?' · '+esc_(c.mau):''}</div><div class="mut">Sơ đồ gốc: ${esc_((diag[x.cap]||{})[n]?.nhan||'—')}${c.links.length?' · đang chạy '+c.links.join(', '):''}</div>
 <div class="fld"><label>Nhãn hàn</label><input type="text" id="ec_n" value="${esc_(r.nhan||'')}" placeholder="${esc_(c.nhan)}" maxlength="6"></div>
 <div class="fld"><label>Trạm (CSG)</label><input type="text" id="ec_t" value="${esc_(r.tram||'')}" placeholder="vd. HNB054"></div>
 <div class="fld"><label>Core hư</label><label><input type="checkbox" id="ec_h" ${(r.hu&&String(r.hu)!='0')?'checked':''}> đánh dấu hư</label></div>
 <div class="row"><button class="on" onclick="saveCore()">Lưu</button><button onclick="delCore()">Xoá nhập tay</button><button onclick="curCore=null;renderMx(curMx)">Đóng</button></div>
 <div class="mut">Cùng nhãn trong một măng xông = hàn với nhau (core nhỏ ↔ core nhỏ). Ghi vào sheet DL_Nhãn MX.</div></div>`;
 el.scrollIntoView({behavior:'smooth',block:'nearest'})}
function saveCore(){const [cid,n]=curCore;const L=RAW.layer.labels;let r=L.find(l=>l.mx==curMx&&l.cable==cid&&ti(l.core)==n);
 const nh=$('#ec_n').value.trim(),tr=$('#ec_t').value.trim(),hu=$('#ec_h').checked?1:0;
 if(!nh&&!tr&&!hu){if(r)L.splice(L.indexOf(r),1)}else{if(!r){r={mx:curMx,cable:cid,core:n,nhan:'',tram:'',hu:0};L.push(r)}r.nhan=nh;r.tram=tr;r.hu=hu}
 touch()}
function delCore(){const [cid,n]=curCore;const L=RAW.layer.labels;const i=L.findIndex(l=>l.mx==curMx&&l.cable==cid&&ti(l.core)==n);if(i>=0)L.splice(i,1);curCore=null;touch()}
function suggestLabels(name){const items=[];E.paths.forEach(p=>p.steps.forEach(s=>{if(s.t=='mx'&&s.at==name&&/^chưa/.test(s.check))items.push([p,s])}));
 const used=new Set(RAW.layer.labels.filter(l=>l.mx==name).map(l=>String(l.nhan)));const letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ';let k=0;const nxt=()=>{while(used.has(letters[k%26]))k++;const l=letters[k%26];used.add(l);return l};
 const seen={},add=[];items.forEach(([p,s])=>{const key=[s.a_cable,s.cores_a,s.b_cable,s.cores_b].join('|');if(!seen[key])seen[key]=nxt();const lab=seen[key],csg=p.frm.startsWith('NBE')?p.to:p.frm;
  [[s.a_cable,s.cores_a],[s.b_cable,s.cores_b]].forEach(([cb,cs])=>cs.forEach(c=>{if(!RAW.layer.labels.some(l=>l.mx==name&&l.cable==cb&&ti(l.core)==c&&l.nhan))add.push({mx:name,cable:cb,core:c,nhan:lab,tram:csg,hu:0})}))});
 if(!add.length){alert('Không có gì để thêm.');return}
 if(!confirm('Thêm '+add.length+' nhãn đề xuất cho '+name+'?\n'+[...new Set(add.map(a=>a.nhan+' = '+a.tram))].join('\n')+'\n\nĐây chỉ là gợi ý từ đường đi bạn mô tả, không phải đọc từ sơ đồ gốc — kiểm tra lại với sơ đồ MX.'))return;
 add.forEach(a=>{const r=RAW.layer.labels.find(l=>l.mx==a.mx&&l.cable==a.cable&&ti(l.core)==a.core);if(r)Object.assign(r,a);else RAW.layer.labels.push(a)});touch()}
renderSrc();renderMxList();

// ---- đề xuất MX thẳng (từ suggest_straight.py)
const SUG={};(RAW.static.suggest?RAW.static.suggest.items:[]).forEach(i=>SUG[i.name]=i);
function sugBox(name){const s=SUG[name];if(!s)return '';const attached=Object.values(E.cables).some(c=>c.ends&&c.ends[name]&&String(c.ends[name])[0]=='@');
 let h=`<div class="card" style="border-color:var(--warn)"><div class="b">Đề xuất vị trí (MX thẳng chỉ có trong KML)</div><div class="mut">MX thẳng = hàn nối dài cáp, core i↔i, không rẽ nhánh. Độ tin cậy: ${esc_(s.conf)}${attached?' · <b class="ok">đã gắn vào cáp</b>':''}</div>`;
 if(!s.cables.length)h+='<div class="warn">Chưa xác định được cáp: cần biết chỉ số mét hoặc vị trí các MX lân cận.</div>';
 s.cables.forEach(c=>{const row=cabRow(c.cable)||{};const on=String(((row.ends||'').split(';').map(x=>x.trim()).find(x=>x.startsWith(name+'='))||'')).length>0;
  h+=`<div class="row"><span><b style="cursor:pointer" onclick="goCab('${c.cable}')">${c.cable}</b> ${esc_(row.ma_cap||'')} ${c.fo}FO · ${esc_(c.frm)} → ${esc_(c.to)} · dài ${c.len_m} m<br>cách đầu “${esc_(c.frm)}” ≈ <b>${c.off_m} m</b> · lệch tuyến ${c.lat_m} m · link ${c.links.join(', ')}</span>${on?'<span class="ok">✓ đã gắn</span>':`<button onclick="attachSug('${name.replace(/'/g,"\\'")}','${c.cable}',${c.off_m})">Gắn vào ${c.cable}</button>`}</div>`});
 if(s.maybe_same_as.length)h+='<div class="mut">Có thể chính là MX trong đường đi: '+s.maybe_same_as.map(m=>`<b>${esc_(m.mx)}</b> (cách ${m.dist_m} m)`).join(', ')+' — nếu đúng, hai tên là một điểm.</div>';
 return h+'</div>'}
function attachSug(name,cid,off){const r=cabRow(cid);if(!r)return;const parts=String(r.ends||'').split(';').map(x=>x.trim()).filter(x=>x&&!x.startsWith(name+'='));parts.push(name+'=@'+off);r.ends=parts.join('; ');touch()}

// ===== thu phóng / kéo bản đồ =====
(function(){const svg=$('#map');let vb0=svg.getAttribute('viewBox').split(' ').map(Number);let vb=vb0.slice();
 const set=()=>svg.setAttribute('viewBox',vb.map(v=>v.toFixed(1)).join(' '));
 const pt=(cx,cy)=>{const r=svg.getBoundingClientRect(),s=Math.max(vb[2]/r.width,vb[3]/r.height);const ox=(r.width-vb[2]/s)/2,oy=(r.height-vb[3]/s)/2;return [vb[0]+(cx-r.left-ox)*s,vb[1]+(cy-r.top-oy)*s,s]};
 function zoom(f,cx,cy){const r=svg.getBoundingClientRect();if(cx===undefined){cx=r.left+r.width/2;cy=r.top+r.height/2}const [px,py]=pt(cx,cy);let nw=vb[2]/f,nh=vb[3]/f;if(nw>vb0[2]*1.3||nw<vb0[2]/40){return}
  vb=[px-(px-vb[0])/f,py-(py-vb[1])/f,nw,nh];set();svg.style.setProperty('--z',vb0[2]/vb[2])}
 $('#zIn').onclick=()=>zoom(1.6);$('#zOut').onclick=()=>zoom(1/1.6);$('#zRst').onclick=()=>{vb=vb0.slice();set()};
 svg.addEventListener('wheel',e=>{e.preventDefault();zoom(e.deltaY<0?1.2:1/1.2,e.clientX,e.clientY)},{passive:false});
 const P=new Map();let moved=false,last=null,d0=0;
 svg.addEventListener('pointerdown',e=>{P.set(e.pointerId,[e.clientX,e.clientY]);moved=false;if(P.size==1)last=[e.clientX,e.clientY];if(P.size==2){const [a,b]=[...P.values()];d0=Math.hypot(a[0]-b[0],a[1]-b[1])}});
 svg.addEventListener('pointermove',e=>{if(!P.has(e.pointerId))return;const prev=P.get(e.pointerId);P.set(e.pointerId,[e.clientX,e.clientY]);
  if(P.size==1){const dx=e.clientX-last[0],dy=e.clientY-last[1];if(!moved&&Math.hypot(dx,dy)<6)return;moved=true;const s=pt(0,0)[2];vb[0]-=dx*s;vb[1]-=dy*s;last=[e.clientX,e.clientY];set()}
  else if(P.size==2){moved=true;const [a,b]=[...P.values()];const d=Math.hypot(a[0]-b[0],a[1]-b[1]);if(d0){zoom(d/d0,(a[0]+b[0])/2,(a[1]+b[1])/2)}d0=d}});
 const up=e=>{P.delete(e.pointerId);if(P.size<2)d0=0;if(P.size==1){last=[...P.values()][0]}};svg.addEventListener('pointerup',up);svg.addEventListener('pointercancel',up);
 svg.addEventListener('click',e=>{if(moved){e.stopPropagation();e.preventDefault();moved=false}},true);
})();

// ===== popup (thay vì chuyển tab) =====
let popFn=null;
const _closeSheet=closeSheet;closeSheet=function(){popFn=null;_closeSheet()};
function showCab(id){popFn=()=>{if(!D.cprof.find(x=>x.id==id))return;openSheet(cabCard(id)+`<div class="row"><button onclick="goCab('${id}')">Mở trong tab Cáp</button></div>`)};popFn()}
function showMx(name){popFn=()=>{const cabs=mxCables(name),pairs=mxPairsFor(name,cabs),rec=allMx().find(m=>m.name==name);
  const steps=[];E.paths.forEach(p=>p.steps.forEach(s=>{if(s.t=='mx'&&s.at==name)steps.push([p,s])}));const q=name.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
  let h=`<h3 style="margin:0">${esc_(name)}</h3><div class="mut">${rec?[...rec.tags].join(' · '):''}</div>${sugBox(name)}${RAW.static.straight[name]!==undefined?`<div class="mut">MX thẳng: hàn thẳng core i↔i cho ${RAW.static.straight[name]} core đầu.</div>`:''}`;
  cabs.forEach(x=>{h+=`<div style="margin-top:8px"><b style="cursor:pointer" onclick="showCab('${x.id}')">${x.id}</b> <span class="mut">${esc_(x.c.ma_cap||'(chưa mã)')} · ${x.c.fo}FO · ${esc_(x.c.frm)} → ${esc_(x.c.to)}</span><div class="cs">${x.cores.map(c=>`<div class="cc${c.ov?' ov':''}${c.hu?' hu':''}${c.links.length?' run':''}" onclick="goMx('${q}')"><div class="n"><i style="background:${fcol(c.n)}"></i>${c.n}</div><div class="l" style="color:${c.nhan?lcol(c.nhan):'var(--mut)'}">${esc_(c.nhan)||'·'}</div><div class="s">${esc_(c.tram)||(c.links.length?c.links[0]:'')}</div></div>`).join('')}</div></div>`});
  if(!cabs.length)h+='<div class="mut">Chưa gắn cáp nào vào măng xông này.</div>';
  if(pairs.length){const g={};pairs.forEach(p=>{const k=[p.src,p.label,p.a,p.b].join('|');(g[k]=g[k]||[]).push(p)});h+='<div class="b" style="margin-top:8px">Phối core</div><table><tr><th>Nguồn</th><th>Nhãn</th><th>Cáp A / core</th><th>Cáp B / core</th></tr>'+Object.values(g).map(L=>`<tr><td class="mut">${esc_(L[0].src)}</td><td class="b">${esc_(L[0].label)}</td><td>${L[0].a}<br><b>${RingEngine.rng(L.map(p=>p.ca))}</b></td><td>${L[0].b}<br><b>${RingEngine.rng(L.map(p=>p.cb))}</b></td></tr>`).join('')+'</table>'}
  if(steps.length)h+='<div class="b" style="margin-top:8px">Link đi qua</div><table>'+steps.map(([p,s])=>`<tr><td class="b">${p.id}</td><td>${s.a_cable} ${s.cores_a.join('+')} ↔ ${s.b_cable} ${s.cores_b.join('+')}</td><td class="${/^khớp/.test(s.check)?'ok':/^chưa/.test(s.check)?'warn':'bad'}">${esc_(String(s.check).slice(0,40))}</td></tr>`).join('')+'</table>';
  h+=`<div class="row"><button class="on" onclick="goMx('${q}')">Mở trang MX (sửa nhãn)</button></div>`;openSheet(h)};popFn()}
const _refresh=refresh;refresh=function(){_refresh();if(popFn&&$('#sheet').classList.contains('on'))popFn()};

// ===== bản nháp tự lưu (không mất thay đổi khi tải bản HTML/Excel mới) =====
// Lưu vào trình duyệt: lớp dữ liệu hiện tại + lớp gốc lúc bắt đầu sửa. Khôi phục theo kiểu "3 bên": chỉ áp dụng phần bạn đã sửa lên dữ liệu mới.
let BASE=JSON.parse(JSON.stringify(RAW.layer));const DK='ringDraftV1';
function saveDraft(){try{localStorage.setItem(DK,JSON.stringify({t:Date.now(),base:BASE,layer:RAW.layer}))}catch(e){}}
function loadDraft(){try{const s=localStorage.getItem(DK);return s?JSON.parse(s):null}catch(e){return null}}
function clearDraft(){try{localStorage.removeItem(DK)}catch(e){}}
const S_=x=>x==null?'':String(x);
function mergeDraft(dr){const L=RAW.layer,B=dr.base,Dl=dr.layer;let n=0;
 const byId=(arr,k)=>{const m={};arr.forEach(r=>m[S_(r[k])]=r);return m};
 [['cables','id'],['links','id']].forEach(([key,k])=>{const nb=byId(B[key],k),nl=byId(L[key],k);Dl[key].forEach(r=>{const id=S_(r[k]),b=nb[id],t=nl[id];
   if(!b){if(!t){L[key].push(r);n++}return}if(!t)return;Object.keys(r).forEach(f=>{if(S_(r[f])!==S_(b[f])){t[f]=r[f];n++}})})});
 const grp=arr=>{const m={};arr.forEach(r=>(m[S_(r.link)]=m[S_(r.link)]||[]).push(r));return m};const gb=grp(B.steps),gd=grp(Dl.steps);
 Object.keys(gd).forEach(l=>{if(JSON.stringify(gd[l])!==JSON.stringify(gb[l]||[])){L.steps=L.steps.filter(r=>S_(r.link)!==l).concat(gd[l]);n++}});
 const lk=r=>[r.mx,r.cable,S_(r.core)].join('|');const lb=byId2(B.labels),ld=byId2(Dl.labels),ln=byId2(L.labels);
 function byId2(arr){const m={};arr.forEach(r=>m[lk(r)]=r);return m}
 Object.keys(ld).forEach(k=>{const r=ld[k],b=lb[k];if(!b||JSON.stringify(r)!==JSON.stringify(b)){if(ln[k])Object.assign(ln[k],r);else L.labels.push(Object.assign({},r));n++}});
 Object.keys(lb).forEach(k=>{if(!ld[k]&&ln[k]){L.labels.splice(L.labels.indexOf(ln[k]),1);n++}});
 return n}
function exportDraft(){const b=new Blob([JSON.stringify({t:Date.now(),base:BASE,layer:RAW.layer})],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='ring_ban_nhap.json';document.body.appendChild(a);a.click();a.remove()}
async function importDraft(f){try{const dr=JSON.parse(await f.text());const n=mergeDraft(dr);BASE=JSON.parse(JSON.stringify(RAW.layer));BASE0=null;setDirty(true);saveDraft();refresh();alert('Đã áp dụng '+n+' thay đổi từ bản nháp.')}catch(e){alert('Không đọc được bản nháp: '+e.message)}}
let BASE0=null;
function offerDraft(){const dr=loadDraft();if(!dr)return;const same=JSON.stringify(dr.layer)===JSON.stringify(RAW.layer);if(same)return;
 const d=new Date(dr.t).toLocaleString('vi-VN');const bar=document.createElement('div');bar.id='draftBar';bar.style.cssText='background:color-mix(in srgb,var(--warn) 25%,var(--card));padding:8px 12px;border-bottom:1px solid var(--line);font-size:13px';
 bar.innerHTML=`Có <b>bản nháp chưa lưu Excel</b> (${esc_(d)}). <button id="dRes" class="on">Khôi phục</button> <button id="dDis">Bỏ bản nháp</button>`;$('#src').after(bar);
 $('#dRes').onclick=()=>{const n=mergeDraft(dr);BASE=JSON.parse(JSON.stringify(RAW.layer));setDirty(n>0);saveDraft();refresh();bar.remove();alert('Đã khôi phục '+n+' thay đổi. Nhớ bấm “Lưu Excel”.')};
 $('#dDis').onclick=()=>{if(confirm('Xoá bản nháp?')){clearDraft();bar.remove()}}}
$('.tools').insertAdjacentHTML('afterbegin','<button id="bBak" title="Sao lưu / nạp bản nháp">⬇⬆</button>');
$('#bBak').onclick=()=>{if(confirm('OK = tải bản sao lưu (.json) về máy.\nHuỷ = chọn file sao lưu để nạp.'))exportDraft();else{const i=document.createElement('input');i.type='file';i.accept='.json';i.onchange=()=>i.files[0]&&importDraft(i.files[0]);i.click()}};
// sau khi lưu Excel thành công thì bản nháp không còn cần: đặt lại mốc
const _setDirty=setDirty;setDirty=function(v){_setDirty(v);if(!v){BASE=JSON.parse(JSON.stringify(RAW.layer));clearDraft()}};
offerDraft();
