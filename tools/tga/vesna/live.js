// Vesna's Trade (#361) check mock-up: draws what BPC_VesnaTrade draws, with the same layout.json numbers and the same
// atlas cells (out/T_VT_Atlas.png, T_VT_Icons.png, T_VT_Turn_*.png). Sample state = 4 worn (Cuirass, Gauntlets, Greaves,
// Sabatons), Pauldrons selected, 3,120 gold, next price 2,000 (#96 curve after 4 buys). The hero figure is a stand-in:
// in game it is the live capture of the hero.
(function(){
const A=L.atlas, AS=L.S, R0=document.getElementById('root');
const worn=new Set([10,12,14,13]), owned=new Set([10,12,14,13]), avail=new Set([10,11,12,13,14]);
const sel=1, scroll=0, gold=3120, price=2000, wc=worn.size;
const ICON=['Chest','Shoulders','Gauntlets','Shins','Boots'];
const tint=c=>c; // css filter-free tint: white cells use mask + background colour
function cellDiv(k,x,y,w,h,color,src,uv){ // uv in 0..1 of a texture of tw x th
  const d=document.createElement('div'); const tw=src.tw, th=src.th;
  const u=uv?uv:[A[k].x*AS/2048,A[k].y*AS/2048,A[k].w*AS/2048,A[k].h*AS/2048];
  w=w||A[k].w; h=h||A[k].h; const sx=w/(u[2]*tw), sy=h/(u[3]*th);
  const bg=`url(${src.url}) ${-u[0]*tw*sx}px ${-u[1]*th*sy}px / ${tw*sx}px ${th*sy}px no-repeat`;
  d.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;`+
    (color?`background:${color};-webkit-mask:${bg};mask:${bg}`:`background:${bg}`);
  R0.appendChild(d); return d; }
const AT={url:'out/T_VT_Atlas.png',tw:2048,th:2048}, IC={url:'out/T_VT_Icons.png',tw:1024,th:256};
const cell=(k,x,y,color,anchor)=>{const r=A[k]; const xx=anchor==='c'?x-r.w/2:anchor==='r'?x-r.w:x; return cellDiv(k,xx,y-r.h/2,0,0,color,AT);};
function txt(s,x,y,lh,color,anchor){const e=document.createElement('div'); e.textContent=s;
  e.style.cssText=`position:absolute;left:${x}px;top:${y}px;font-family:Cinzel;font-size:${lh*0.78}px;line-height:1;color:${color};white-space:nowrap;transform:translate(${anchor==='c'?'-50%':anchor==='r'?'-100%':'0'},-50%)`;
  R0.appendChild(e); return e;}
const CREAM='#ede3cf', DIM='#9e9485', GOLD='#f0cc85', GREEN='#9edb5c', RED='#e05c47';
const grp=n=>n.toLocaleString('en-US');
// portrait stand-in
// tabs
const tb=L.tabbar; const t1=L.tabs[1]; cell('tab1',(t1.x0+t1.x1)/2,tb.cy,null,'c');
// purse
txt(grp(gold),L.purse.gold[1],L.purse.cy,30,CREAM); txt('0',L.purse.iron[1],L.purse.cy,30,CREAM); txt('0',L.purse.silver[1],L.purse.cy,30,CREAM);
txt(`(${wc} / 11)`,322,L.lhead.cy+1,27,GOLD);
// rows
const R=L.rows;
for(let i=0;i<R.n;i++){ const idx=scroll+i, p=L.pieces[idx]; const ry=R.y0+i*R.step, cy=ry+R.h/2;
  if(idx===sel) cellDiv('rsel',R.x+L.rsel.dx,ry+L.rsel.dy,0,0,null,AT);
  const ic=R.icon, isz=58, icx=(ic[0]+ic[1])/2-isz/2;
  if(p.art) cellDiv(null,icx,cy-isz/2,isz,isz,null,IC,[ICON.indexOf(p.art)*128/1024,0,128/1024,.5]);
  else cellDiv('glyph'+p.id,icx,cy-isz/2,isz,isz,avail.has(p.id)?null:null,AT);
  cell('name'+p.id,R.name[0],ry+R.name[1]-R.y0,avail.has(p.id)?CREAM:DIM);
  cell('def'+p.id,R.deff[0],ry+R.deff[1]-R.y0,DIM);
  const sy=ry+R.state[1]-R.y0;
  if(worn.has(p.id)) cell('worn',R.state[0],sy,null,'r'); else if(owned.has(p.id)) cell('owned',R.state[0],sy,null,'r');
  else if(!avail.has(p.id)) cell('forging',R.state[0],sy,null,'r');
  else { const e=txt(grp(price)+' G',R.state[0],sy,25,gold>=price?GOLD:RED,'r'); const w=e.getBoundingClientRect().width; cell('coin',R.state[0]-w-28,sy,null); } }
const th=L.scroll.h*R.n/L.pieces.length; const d=document.createElement('div'); d.style.cssText=`position:absolute;left:${L.scroll.x}px;top:${L.scroll.y}px;width:${L.scroll.w}px;height:${th}px;background:rgba(217,180,106,.85);border-radius:3px`; R0.appendChild(d);
// centre
const p=L.pieces[sel];
cell('title'+p.id,L.ititle.cx,L.ititle.y,CREAM,'c'); cell('tag'+p.id,L.tags.slot_cx,L.tags.y,'#ccc2ad','c'); cell('setpiece',L.tags.piece_cx,L.tags.y,null,'c');
const TN=L.turn, zw=TN.w*1.15, zh=zw*340/512;
cellDiv(null,TN.cx-zw/2,TN.cy-8-zh/2,zw,zh,null,{url:'out/T_VT_Turn_'+p.art+'.png',tw:2048,th:2040},[0,0,.25,340/2040]);
for(let k=0;k<5;k++) cell(k===Math.round(sel*4/10)?'dot_on':'dot_off',L.dots.cx+(k-2)*L.dots.step,L.dots.y,null,'c');
const cur=[...worn].reduce((s,id)=>s+L.pieces.find(q=>q.id===id).deff,0), gain=worn.has(p.id)?0:p.deff;
txt('+'+p.deff,L.cmp.plus[0],L.cmp.plus[1],36,GREEN); txt(cur,L.cmp.cur[0],L.cmp.cur[1],29,CREAM,'c'); txt(cur+gain,L.cmp.after[0],L.cmp.after[1],29,GREEN,'c');
txt(`${wc} / 11`,L.bonus.count_r,L.bonus.head_y,26,CREAM,'r');
L.tiers.forEach((t,i)=>cell('tier'+i,L.bonus.diamond-8,L.bonus.lines[i],wc>=t.n?GREEN:'#ccc2ad'));
cell('btn_on',L.buy.x,L.buy.cy,null); cell('key_e',L.buy.key[0],L.buy.key[1],null,'c');
txt('BUY FOR  '+grp(price)+' G',L.buy.text,L.buy.cy,28,'#1a1208');
// right
cellDiv('rtab0',L.rtabs.eq[0],L.rtabs.y,0,0,null,AT);
const hr=L.hero, fig=document.createElement('div');
fig.style.cssText=`position:absolute;left:${hr.x}px;top:${hr.y}px;width:${hr.w}px;height:${hr.h}px;display:grid;place-items:center;color:#6d6457;font-family:Cinzel;font-size:13px;letter-spacing:2px;text-align:center;
  background:radial-gradient(28% 9% at 50% 13%,#2a2622 98%,transparent),radial-gradient(34% 30% at 50% 40%,#25221e 98%,transparent),radial-gradient(26% 40% at 50% 78%,#201d1a 98%,transparent)`;
fig.innerHTML='LIVE HERO<br>CAPTURE'; R0.appendChild(fig);
const SL=L.slot, slots=L.slotsL.concat(L.slotsR);
slots.forEach((id,i)=>{ const x=i<6?SL.lx:SL.rx, y=SL.cy0+(i%6)*SL.step, sz=46; const q=L.pieces.find(z=>z.id===id);
  const el=q&&q.art?cellDiv(null,x-sz/2,y-sz/2,sz,sz,null,IC,[ICON.indexOf(q.art)*128/1024,0,128/1024,.5]):cellDiv('glyph'+id,x-sz/2,y-sz/2,sz,sz,null,AT);
  el.style.opacity=worn.has(id)?1:(owned.has(id)?.85:.45);
  if(id===p.id) cellDiv('slotsel',x-35,y-35,0,0,null,AT); });
const ST=L.stats;
txt(cur,ST.val,ST.rows[0],25,CREAM); txt(`${cur+gain} (+${gain})`,ST.after,ST.rows[0],25,GREEN);
txt('35',ST.val,ST.rows[1],25,CREAM); txt('100%',ST.val,ST.rows[2],25,CREAM); txt('250',ST.val,ST.rows[3],25,CREAM);
})();
