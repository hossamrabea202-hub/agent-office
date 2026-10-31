// The Muster (#359) check mock-up: draws what BPC_Muster draws (layout_mu.json numbers, T_MU_Atlas cells, Cinzel numbers).
// Sample state: RECRUIT tab, Swordsman selected, 4 swordsmen + 3 crossbowmen of 10, 3,120 gold, ore 34 / 5 / 5 / 2,
// one swordsman in training (40 %), walls level 1, towers 0, flares not bought, 2 free cannon pads.
(function(){
const A=L.atlas, AS=L.S, R0=document.getElementById('root');
const AT={url:'out/T_MU_Atlas.png',tw:2048,th:2048};
function cellDiv(k,x,y,w,h,color){ const d=document.createElement('div'); const u=[A[k].x*AS/2048,A[k].y*AS/2048,A[k].w*AS/2048,A[k].h*AS/2048];
  w=w||A[k].w; h=h||A[k].h; const sx=w/(u[2]*2048), sy=h/(u[3]*2048);
  const bg=`url(${AT.url}) ${-u[0]*2048*sx}px ${-u[1]*2048*sy}px / ${2048*sx}px ${2048*sy}px no-repeat`;
  d.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;`+(color?`background:${color};-webkit-mask:${bg};mask:${bg}`:`background:${bg}`);
  R0.appendChild(d); return d; }
const cell=(k,x,y,color,anchor)=>{const r=A[k]; return cellDiv(k,anchor==='c'?x-r.w/2:anchor==='r'?x-r.w:x,y-r.h/2,0,0,color);};
function txt(s,x,y,lh,color,anchor){const e=document.createElement('div'); e.textContent=s;
  e.style.cssText=`position:absolute;left:${x}px;top:${y}px;font-family:Cinzel;font-size:${lh*0.78}px;line-height:1;color:${color};white-space:nowrap;transform:translate(${anchor==='c'?'-50%':anchor==='r'?'-100%':'0'},-50%)`;
  R0.appendChild(e); return e;}
const CREAM='#ede3cf', DIM='#9e9485', GOLD='#f0cc85', GREEN='#9edb5c', RED='#e05c47', grp=n=>n.toLocaleString('en-US');
const gold=3120, ore=[34,5,5,2], cnt={R:4,G:3,B:0,A:10}, army=cnt.R+cnt.G, tab=0, sel=0;
const price=b=>Math.round(b*Math.pow(1.25,army));
const items=L.items, TS=[0,5,6,9], TC=[5,1,3,1];
const st={sword:[price(40),0,'ARMY  7 / 10'],xbow:[price(60),0,'ARMY  7 / 10'],cmdr:[300,0,'ONE PER ARMY'],medic:[150,0,'MEDICS  1 / 4'],mech:[0,3,'IN TRAINING']};
const t=L.tabs[tab]; cell('tab'+tab,(t.x0+t.x1)/2,L.tabbar.cy,null,'c');
txt(grp(gold),L.purse.gold[1],L.purse.cy,30,CREAM); txt(ore[0],L.purse.iron[1],L.purse.cy,30,CREAM); txt(ore[2],L.purse.silver[1],L.purse.cy,30,CREAM);
txt(`(${army} / ${cnt.A})`,318,L.lhead.cy+1,27,GOLD);
const R=L.rows;
for(let i=0;i<TC[tab];i++){ const it=items[TS[tab]+i], [p,s,sub]=st[it.key]; const ry=R.y0+i*R.step, cy=ry+R.h/2;
  if(i===sel) cellDiv('rsel',R.x+L.rsel.dx,ry+L.rsel.dy);
  const g=cellDiv('glyph_'+it.glyph,(R.icon[0]+R.icon[1])/2-27,cy-27,54,54); if(s===3) g.style.opacity=.5;
  cell('name_'+it.key,R.name[0],ry+R.name[1]-R.y0,s===3?DIM:CREAM); txt(sub,R.deff[0],ry+R.deff[1]-R.y0,19,DIM);
  const sy=ry+R.state[1]-R.y0;
  if(s===0){ const e=txt(grp(p)+' G',R.state[0],sy,25,gold>=p?GOLD:RED,'r'); cell('coin',R.state[0]-e.getBoundingClientRect().width-28,sy); }
  else cell('locked',R.state[0],sy,null,'r'); }
const it=items[TS[tab]+sel], [p]=st[it.key];
cell('title_'+it.key,L.ititle.cx,L.ititle.y,CREAM,'c'); cell('tag_'+it.key,L.tags.slot_cx,L.tags.y,'#ccc2ad','c'); cell('setpiece',L.tags.piece_cx,L.tags.y,null,'c');
cellDiv('glyph_'+it.glyph,L.turn.cx-100,L.turn.cy-118,200,200); txt('ARMY  7 / 10',L.turn.cx,L.turn.cy+136,20,GOLD,'c');
txt(grp(p)+' G',616,637,32,GREEN); txt(grp(gold)+' G',826,637,24,CREAM);
cell('d1_'+it.key,566,L.bonus.lines[0],'#dbd1bd'); cell('d2_'+it.key,566,L.bonus.lines[1],'#dbd1bd');
cell('btn_on',L.buy.x,L.buy.cy); cell('key_e',L.buy.key[0],L.buy.key[1],null,'c'); txt('RECRUIT FOR  '+grp(p)+' G',L.buy.text,L.buy.cy,28,'#1a1208');
cellDiv('rtab0',L.rtabs.eq[0],L.rtabs.y);
const GA=L.garrison; [['SWORDSMEN','4','sword'],['CROSSBOWMEN','3','xbow'],['COMMANDER','-','banner'],['MEDICS','1 / 4','medic'],['ARMY','7 / 10','sword']].forEach(([l,v,g],k)=>{
  const y=GA.y0+k*GA.step; const d=cellDiv('glyph_'+g,GA.icon-14,y-14,28,28,'#d8b773'); txt(l,GA.label,y,21,CREAM); txt(v,GA.val,y,24,GOLD,'r'); });
const QU=L.queue; txt('IN TRAINING',GA.label,QU.y-30,20,DIM);
for(let q=0;q<3;q++){ const x=QU.x0+q*QU.step; cellDiv('qslot',x,QU.y); if(q===0){ cellDiv('glyph_sword',x+QU.w/2-26,QU.y+6,52,52);
  const b=document.createElement('div'); b.style.cssText=`position:absolute;left:${x+4}px;top:${QU.y+QU.h-7}px;width:${(QU.w-8)*.4}px;height:4px;background:#f0c773`; R0.appendChild(b);} }
L.stats.rows.forEach((y,k)=>txt(ore[k],L.stats.val,y,25,CREAM));
})();
