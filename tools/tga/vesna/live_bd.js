// Vesna's Trade, #424 bundles check mock-up (chrome.html?m=mock&L=bd): draws what gen_trade_bd.py's BPC_VesnaTrade
// graph draws, with layout_bd.json and the #424 textures. Sample state: Torso + Gauntlets worn, Legs owned (not worn),
// Helm has no art yet (FORGING), Heater Shield worn, Torso selected, 3,120 gold.
(function(){
const A=L.atlas, AS=L.S, R0=document.getElementById('root');
const T='../../../handoffs/obsidian-bundles-424/textures/', OLD='../../../assets/tga/VesnaTrade/textures/';
const worn=new Set([1,2,28]), owned=new Set([1,2,3,28]), avail=new Set([1,2,3,27,28,29]);
const price={0:150,1:690,2:160,3:400,27:180,28:250,29:450};
const sel=1, scroll=0, gold=3120, bc=2;
const BUNDLE_ICON={1:1,2:2,3:3}, SHIELD_ICON={27:10,28:9};
function cellDiv(k,x,y,w,h,color,src,uv){
  const d=document.createElement('div'); const tw=src.tw, th=src.th;
  const u=uv?uv:[A[k].x*AS/2048,A[k].y*AS/2048,A[k].w*AS/2048,A[k].h*AS/2048];
  w=w||A[k].w; h=h||A[k].h; const sx=w/(u[2]*tw), sy=h/(u[3]*th);
  const bg=`url(${src.url}) ${-u[0]*tw*sx}px ${-u[1]*th*sy}px / ${tw*sx}px ${th*sy}px no-repeat`;
  d.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;`+
    (color?`background:${color};-webkit-mask:${bg};mask:${bg}`:`background:${bg}`);
  R0.appendChild(d); return d; }
const AT={url:T+'T_VT_Atlas_424.png',tw:2048,th:2048}, IC={url:OLD+'T_VT_Icons.png',tw:1024,th:256}, BT={url:T+'T_VT_Bundles_424.png',tw:1024,th:256};
const cell=(k,x,y,color,anchor)=>{const r=A[k]; const xx=anchor==='c'?x-r.w/2:anchor==='r'?x-r.w:x; return cellDiv(k,xx,y-r.h/2,0,0,color,AT);};
function icon(id,x,y,sz,op){ let e;
  if(BUNDLE_ICON[id]!=null) e=cellDiv(null,x,y,sz,sz,null,BT,[BUNDLE_ICON[id]*.25,0,.25,1]);
  else if(SHIELD_ICON[id]!=null) e=cellDiv(null,x,y,sz,sz,null,IC,[(SHIELD_ICON[id]%8)*.125,Math.floor(SHIELD_ICON[id]/8)*.5,.125,.5]);
  else e=cellDiv('glyph'+id,x,y,sz,sz,null,AT);
  if(op!=null) e.style.opacity=op; return e; }
function txt(s,x,y,lh,color,anchor){const e=document.createElement('div'); e.textContent=s;
  e.style.cssText=`position:absolute;left:${x}px;top:${y}px;font-family:Cinzel;font-size:${lh*0.78}px;line-height:1;color:${color};white-space:nowrap;transform:translate(${anchor==='c'?'-50%':anchor==='r'?'-100%':'0'},-50%)`;
  R0.appendChild(e); return e;}
const CREAM='#ede3cf', DIM='#9e9485', GOLD='#f0cc85', GREEN='#9edb5c', RED='#e05c47';
const grp=n=>n.toLocaleString('en-US');
const tb=L.tabbar; const t1=L.tabs[1]; cell('tab1',(t1.x0+t1.x1)/2,tb.cy,null,'c');
txt(grp(gold),L.purse.gold[1],L.purse.cy,30,CREAM); txt('0',L.purse.iron[1],L.purse.cy,30,CREAM); txt('0',L.purse.silver[1],L.purse.cy,30,CREAM);
txt(`(${bc} / 4)`,322,L.lhead.cy+1,27,GOLD);
const R=L.rows;
for(let i=0;i<R.n;i++){ const idx=scroll+i, p=L.pieces[idx]; if(!p) break; const ry=R.y0+i*R.step, cy=ry+R.h/2;
  if(idx===sel) cellDiv('rsel',R.x+L.rsel.dx,ry+L.rsel.dy,0,0,null,AT);
  const ic=R.icon, isz=58; icon(p.id,(ic[0]+ic[1])/2-isz/2,cy-isz/2,isz,avail.has(p.id)?1:.55);
  cell('name'+p.id,R.name[0],ry+R.name[1]-R.y0,avail.has(p.id)?CREAM:DIM);
  cell('def'+p.id,R.deff[0],ry+R.deff[1]-R.y0,DIM);
  const sy=ry+R.state[1]-R.y0;
  if(worn.has(p.id)) cell('worn',R.state[0],sy,null,'r'); else if(owned.has(p.id)) cell('owned',R.state[0],sy,null,'r');
  else if(!avail.has(p.id)) cell('forging',R.state[0],sy,null,'r');
  else { const pr=price[p.id]; const e=txt(grp(pr)+' G',R.state[0],sy,25,gold>=pr?GOLD:RED,'r'); const w=e.getBoundingClientRect().width; cell('coin',R.state[0]-w-28,sy,null); } }
const th=L.scroll.h*R.n/L.pieces.length; const d=document.createElement('div'); d.style.cssText=`position:absolute;left:${L.scroll.x}px;top:${L.scroll.y}px;width:${L.scroll.w}px;height:${th}px;background:rgba(217,180,106,.85);border-radius:3px`; R0.appendChild(d);
const p=L.pieces[sel];
cell('title'+p.id,L.ititle.cx,L.ititle.y,CREAM,'c'); cell('tag'+p.id,L.tags.slot_cx,L.tags.y,'#ccc2ad','c'); cell('setpiece',L.tags.piece_cx,L.tags.y,null,'c');

const TN=L.turn, zw=TN.w*1.15, zh=zw*340/512;
cellDiv(null,TN.cx-zw/2,TN.cy-8-zh/2,zw,zh,null,{url:OLD+'T_VT_Turn_Chest.png',tw:2048,th:2040},[0,0,.25,340/2040]);
for(let k=0;k<5;k++) cell(k===Math.round(sel*4/(L.pieces.length-1))?'dot_on':'dot_off',L.dots.cx+(k-2)*L.dots.step,L.dots.y,null,'c');
const deff=id=>(L.pieces.find(q=>q.id===id)||{deff:0}).deff;
const cur=[...worn].reduce((s,id)=>s+deff(id),0);
txt('+'+p.deff,L.cmp.plus[0],L.cmp.plus[1],36,GREEN); txt(cur,L.cmp.cur[0],L.cmp.cur[1],29,CREAM,'c'); txt(cur,L.cmp.after[0],L.cmp.after[1],29,GREEN,'c');
txt(`${bc} / 4`,L.bonus.count_r,L.bonus.head_y,26,CREAM,'r');
L.tiers.forEach((t,i)=>cell('tier'+i,L.bonus.diamond-8,L.bonus.lines[i],bc>=t.n?GREEN:'#ccc2ad'));
cell('btn_on',L.buy.x,L.buy.cy,null); cell('key_e',L.buy.key[0],L.buy.key[1],null,'c');
txt('TAKE OFF',L.buy.text,L.buy.cy,28,'#1a1208');
cellDiv('rtab0',L.rtabs.eq[0],L.rtabs.y,0,0,null,AT);
const hr=L.hero, fig=document.createElement('div');
fig.style.cssText=`position:absolute;left:${hr.x}px;top:${hr.y}px;width:${hr.w}px;height:${hr.h}px;display:grid;place-items:center;color:#6d6457;font-family:Cinzel;font-size:13px;letter-spacing:2px;text-align:center;
  background:radial-gradient(28% 9% at 50% 13%,#2a2622 98%,transparent),radial-gradient(34% 30% at 50% 40%,#25221e 98%,transparent),radial-gradient(26% 40% at 50% 78%,#201d1a 98%,transparent)`;
fig.innerHTML='LIVE HERO<br>CAPTURE'; R0.appendChild(fig);
// doll: bundle icon when worn, faint outline when empty; the shield slot shows the worn kit shield; weapon = sword outline
const SL=L.slot, slots=L.slotsL.concat(L.slotsR);
slots.forEach((sid,i)=>{ const x=i<3?SL.lx:SL.rx, y=SL.cy0+(i%3)*SL.step, sz=50;
  if(sid>=0 && worn.has(sid)) icon(sid,x-sz/2,y-sz/2,sz,1);
  else if(sid===-1 && worn.has(28)) icon(28,x-sz/2,y-sz/2,sz,1);
  else cellDiv('out'+i,x-sz/2,y-sz/2,sz,sz,'rgba(217,180,106,.38)',AT);
  if(sid===p.id) cellDiv('slotsel',x-35,y-35,0,0,null,AT); });
const ST=L.stats;
txt(cur,ST.val,ST.rows[0],25,CREAM);
txt('35',ST.val,ST.rows[1],25,CREAM); txt('100%',ST.val,ST.rows[2],25,CREAM); txt('250',ST.val,ST.rows[3],25,CREAM);
})();
