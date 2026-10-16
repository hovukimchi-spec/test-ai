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
function touch(){setDirty(true);refresh()}
// ---- mở / lưu Excel
async function loadBytes(b,name,handle){try{const L=await XlsxIO.readLayer(b);RAW.layer=L;xbytes=b;fname=name;fh=handle||null;dirty=false;refresh();renderSrc()}catch(e){alert('Không đọc được file: '+e.message)}}
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
 ${mxs.length?'<div class="mut">Măng xông trên cáp: '+mxs.map(m=>`<a href="#" onclick="goMx('${m.replace(/'/g,"\\'")}');return false">${esc_(m)}</a>`).join(' · ')+'</div>':''}`}
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
