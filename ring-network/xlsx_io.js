/* xlsx_io.js — đọc/ghi các sheet DL_* trong file .xlsx ngay trên trình duyệt (không thư viện).
   Ghi "tại chỗ": chỉ thay phần dữ liệu của sheet DL_*, giữ nguyên byte của mọi phần khác trong file. */
(function(root){
'use strict';
const TD=new TextDecoder('utf-8'),TE=new TextEncoder();
const u16=(b,o)=>b[o]|(b[o+1]<<8),u32=(b,o)=>(b[o]|(b[o+1]<<8)|(b[o+2]<<16)|(b[o+3]<<24))>>>0;
let CRC=null;function crc32(b){if(!CRC){CRC=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;CRC[n]=c>>>0}}let c=0xFFFFFFFF;for(let i=0;i<b.length;i++)c=CRC[(c^b[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0}
async function pipe(bytes,stream){const r=new Response(new Blob([bytes]).stream().pipeThrough(stream));return new Uint8Array(await r.arrayBuffer())}
const inflate=b=>pipe(b,new DecompressionStream('deflate-raw')),deflate=b=>pipe(b,new CompressionStream('deflate-raw'));

function readZip(buf){ // buf: Uint8Array -> {entries:[{name,method,crc,csize,usize,off,flags,time,date}],buf}
  let e=buf.length-22;while(e>=0&&u32(buf,e)!==0x06054b50)e--; if(e<0)throw new Error('Không phải file .xlsx (thiếu EOCD)');
  const n=u16(buf,e+10);let p=u32(buf,e+16);const entries=[];
  for(let i=0;i<n;i++){ if(u32(buf,p)!==0x02014b50)throw new Error('Danh mục zip hỏng');
    const nl=u16(buf,p+28),el=u16(buf,p+30),cl=u16(buf,p+32);
    entries.push({flags:u16(buf,p+8),method:u16(buf,p+10),time:u16(buf,p+12),date:u16(buf,p+14),crc:u32(buf,p+16),csize:u32(buf,p+20),usize:u32(buf,p+24),off:u32(buf,p+42),name:TD.decode(buf.subarray(p+46,p+46+nl))});
    p+=46+nl+el+cl;}
  return {entries,buf};}
function rawData(z,en){const b=z.buf,o=en.off;const nl=u16(b,o+26),el=u16(b,o+28);return b.subarray(o+30+nl+el,o+30+nl+el+en.csize)}
async function getFile(z,name){const en=z.entries.find(x=>x.name===name);if(!en)return null;const r=rawData(z,en);return en.method===0?r.slice():inflate(r)}
async function getText(z,name){const b=await getFile(z,name);return b?TD.decode(b):null}

async function writeZip(z,changed){ // changed: {name:Uint8Array}
  const parts=[],cd=[];let off=0;
  const push=b=>{parts.push(b);off+=b.length};
  const names=z.entries.map(e=>e.name);
  const ordered=z.entries.map(e=>({name:e.name,en:e}));
  for(const {name,en} of ordered){
    let method=en.method,crc=en.crc,cs=en.csize,us=en.usize,data;
    if(changed[name]){const raw=changed[name];data=await deflate(raw);method=8;crc=crc32(raw);cs=data.length;us=raw.length;}
    else data=rawData(z,en);
    const nb=TE.encode(name);const h=new Uint8Array(30+nb.length);const dv=new DataView(h.buffer);
    dv.setUint32(0,0x04034b50,true);dv.setUint16(4,20,true);dv.setUint16(6,0x0800,true);dv.setUint16(8,method,true);dv.setUint16(10,en.time,true);dv.setUint16(12,en.date,true);
    dv.setUint32(14,crc,true);dv.setUint32(18,cs,true);dv.setUint32(22,us,true);dv.setUint16(26,nb.length,true);dv.setUint16(28,0,true);h.set(nb,30);
    const lho=off;push(h);push(data);
    const c=new Uint8Array(46+nb.length);const cv=new DataView(c.buffer);
    cv.setUint32(0,0x02014b50,true);cv.setUint16(4,20,true);cv.setUint16(6,20,true);cv.setUint16(8,0x0800,true);cv.setUint16(10,method,true);cv.setUint16(12,en.time,true);cv.setUint16(14,en.date,true);
    cv.setUint32(16,crc,true);cv.setUint32(20,cs,true);cv.setUint32(24,us,true);cv.setUint16(28,nb.length,true);cv.setUint32(42,lho,true);c.set(nb,46);cd.push(c);}
  const cdStart=off;cd.forEach(push);const cdLen=off-cdStart;
  const e=new Uint8Array(22);const ev=new DataView(e.buffer);ev.setUint32(0,0x06054b50,true);ev.setUint16(8,cd.length,true);ev.setUint16(10,cd.length,true);ev.setUint32(12,cdLen,true);ev.setUint32(16,cdStart,true);push(e);
  const out=new Uint8Array(off);let p=0;parts.forEach(b=>{out.set(b,p);p+=b.length});return out;}

// ---- XML
const unesc=s=>s.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&apos;/g,"'").replace(/&#(\d+);/g,(m,d)=>String.fromCodePoint(+d)).replace(/&#x([0-9a-f]+);/gi,(m,h)=>String.fromCodePoint(parseInt(h,16))).replace(/&amp;/g,'&');
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'');
const colIdx=ref=>{const m=/^([A-Z]+)/.exec(ref)[1];let n=0;for(const ch of m)n=n*26+ch.charCodeAt(0)-64;return n-1};
const colName=i=>{let s='';i++;while(i>0){const m=(i-1)%26;s=String.fromCharCode(65+m)+s;i=Math.floor((i-1)/26)}return s};
function sharedStrings(xml){if(!xml)return[];const out=[];const re=/<si>([\s\S]*?)<\/si>|<si\/>/g;let m;while((m=re.exec(xml))){const t=[...(m[1]||'').matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map(x=>unesc(x[1])).join('');out.push(t)}return out}
function parseSheet(xml,ss){ // -> array of rows (arrays of strings/numbers)
  const rows=[];const reR=/<row\b[^>]*?(?:\/>|>([\s\S]*?)<\/row>)/g;let mr;
  while((mr=reR.exec(xml))){const rn=+/\br="(\d+)"/.exec(mr[0])[1];const cells=[];const body=mr[1]||'';
    const reC=/<c\b([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g;let mc;
    while((mc=reC.exec(body))){const at=mc[1],inner=mc[2]||'';const ref=/\br="([A-Z]+\d+)"/.exec(at)[1];const t=(/\bt="(\w+)"/.exec(at)||[])[1];let v='';
      if(t==='inlineStr'){v=[...inner.matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map(x=>unesc(x[1])).join('')}
      else{const mv=/<v>([\s\S]*?)<\/v>/.exec(inner);if(mv){const raw=unesc(mv[1]);v=t==='s'?(ss[+raw]??''):t==='str'||t==='e'?raw:t==='b'?(raw==='1'?1:0):(raw===''?'':+raw)}}
      cells[colIdx(ref)]=v;}
    rows[rn-1]=cells;}
  return rows;}
async function sheetMap(z){ // tên sheet -> đường dẫn phần
  const wb=await getText(z,'xl/workbook.xml'),rel=await getText(z,'xl/_rels/workbook.xml.rels');const rid={};
  for(const m of rel.matchAll(/<Relationship\b([^>]*)\/?>/g)){const a=m[1];const id=/\bId="([^"]+)"/.exec(a)[1],tg=/\bTarget="([^"]+)"/.exec(a)[1];rid[id]=tg.startsWith('/')?tg.slice(1):'xl/'+tg}
  const out={};for(const m of wb.matchAll(/<sheet\b([^>]*)\/?>/g)){const a=m[1];const nm=unesc(/\bname="([^"]*)"/.exec(a)[1]);const id=/\br:id="([^"]+)"/.exec(a)[1];out[nm]=rid[id]}return out}

const LAYER_SHEETS={
 cables:['DL_Cáp',['id','name','fo','frm','to','len_m','so_row','ma_cap','cs_dau','cs_cuoi','src','ends']],
 links:['DL_Link',['id','ring','frm','to','odf_otdr_m','bbnt_otdr_m','rerouted','complete','design_cables','note']],
 steps:['DL_Bước',['link','seq','t','at','name','cable','cores','odf_ref','note','a_cable','cores_a','b_cable','cores_b','subst','nominal_b']],
 labels:['DL_Nhãn MX',['mx','cable','core','nhan','tram','hu']]};

async function readLayer(bytes){
  const z=readZip(bytes),sm=await sheetMap(z),ss=sharedStrings(await getText(z,'xl/sharedStrings.xml'));const L={};
  for(const [key,[nm,cols]] of Object.entries(LAYER_SHEETS)){
    if(!sm[nm])throw new Error('Thiếu sheet '+nm+' — hãy dùng file Excel do công cụ tạo (ring_network_NhaBe.xlsx).');
    const rows=parseSheet(await getText(z,sm[nm]),ss);const hdr=(rows[0]||[]).map(x=>String(x||''));
    L[key]=rows.slice(1).filter(r=>r&&r.some(v=>v!==''&&v!=null)).map(r=>{const o={};cols.forEach(c=>{const i=hdr.indexOf(c);const v=i<0?'':r[i];o[c]=v==null?'':v});return o});}
  return L;}

function sheetXml(oldXml,cols,rows){
  const hs=/<c\b[^>]*\br="A1"[^>]*\bs="(\d+)"|<c\b[^>]*\bs="(\d+)"[^>]*\br="A1"/.exec(oldXml);const hstyle=hs?(hs[1]||hs[2]):null;
  const cell=(ref,v,s)=>{const st=s?` s="${s}"`:'';if(v===''||v==null)return '';if(typeof v==='number'&&isFinite(v))return `<c r="${ref}"${st}><v>${v}</v></c>`;return `<c r="${ref}"${st} t="inlineStr"><is><t xml:space="preserve">${esc(v)}</t></is></c>`};
  let sd='<row r="1">'+cols.map((c,j)=>cell(colName(j)+'1',c,hstyle)).join('')+'</row>';
  rows.forEach((r,i)=>{sd+=`<row r="${i+2}">`+cols.map((c,j)=>cell(colName(j)+(i+2),r[c],null)).join('')+'</row>'});
  const dim=`A1:${colName(cols.length-1)}${rows.length+1}`;
  let x=oldXml.replace(/<sheetData\b[\s\S]*?<\/sheetData>|<sheetData\/>/,'<sheetData>'+sd+'</sheetData>');
  x=/<dimension\b[^>]*\/>/.test(x)?x.replace(/<dimension\b[^>]*\/>/,`<dimension ref="${dim}"/>`):x;
  return x;}
async function writeLayer(bytes,L){
  const z=readZip(bytes),sm=await sheetMap(z),ch={};
  for(const [key,[nm,cols]] of Object.entries(LAYER_SHEETS)){
    if(!sm[nm])throw new Error('Thiếu sheet '+nm);
    ch[sm[nm]]=TE.encode(sheetXml(await getText(z,sm[nm]),cols,L[key]||[]));}
  return writeZip(z,ch);}
const api={readLayer,writeLayer,readZip,getText,crc32,LAYER_SHEETS};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.XlsxIO=api;
})(typeof self!=='undefined'?self:this);
