// Weapon Mastery (#416) check mock-up: draws what BPC_SkillTome draws (layout_sk.json numbers, T_SK_Atlas cells, Cinzel numbers).
// Sample state: SWORD tab, Quake Slam selected, hero level 12, 4 points spent (8 free); ranks Blast Bolt 1, Charged Shot 0,
// Whirlwind 1, Quake Slam 0, Fissure 0; Defense Aura 1, Healer 0, Selfburn 0.
(function(){
const A=L.atlas, AS=L.S, R0=document.getElementById('root');
const AT={url:'out/T_SK_Atlas.png'};
function cellDiv(k,x,y,w,h,color){ const d=document.createElement('div'); const u=[A[k].x*AS/2048,A[k].y*AS/2048,A[k].w*AS/2048,A[k].h*AS/2048];
  w=w||A[k].w; h=h||A[k].h; const sx=w/(u[2]*2048), sy=h/(u[3]*2048);
  const bg=`url(${AT.url}) ${-u[0]*2048*sx}px ${-u[1]*2048*sy}px / ${2048*sx}px ${2048*sy}px no-repeat`;
  d.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;`+(color?`background:${color};-webkit-mask:${bg};mask:${bg}`:`background:${bg}`);
  R0.appendChild(d); return d; }
const cell=(k,x,y,color,anchor)=>{const r=A[k]; return cellDiv(k,anchor==='c'?x-r.w/2:anchor==='r'?x-r.w:x,y-r.h/2,0,0,color);};
const cellC=(k,cx,cy,sz,color)=>cellDiv(k,cx-sz/2,cy-sz/2,sz,sz,color);
function txt(s,x,y,lh,color,anchor){const e=document.createElement('div'); e.textContent=s;
  e.style.cssText=`position:absolute;left:${x}px;top:${y}px;font-family:Cinzel;font-size:${lh*0.78}px;line-height:1;color:${color};white-space:nowrap;transform:translate(${anchor==='c'?'-50%':anchor==='r'?'-100%':'0'},-50%)`;
  R0.appendChild(e); return e;}
function rect(x,y,w,h,c){const d=document.createElement('div'); d.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;background:${c}`; R0.appendChild(d); return d;}
const CREAM='#ede3cf', DIM='#9e9485', GOLD='#f0cc85', GREEN='#9edb5c', RED='#e05c47', GLY='#d8b773';
const level=12, spent=4, free=level-spent, tab=1, sel=1;
const rank={blast:1,charge:0,whirl:1,quake:0,fissure:0,adef:1,aheal:0,aburn:0};
const items=L.items, inTab=t=>items.filter(i=>i.tab===t);
const cost=it=>rank[it.key]+1;                                   // live rule: next rank costs rank + 1 points
// header
const t=L.tabs[tab]; cell('tab'+tab,(t.x0+t.x1)/2,L.tabbar.cy,null,'c');
txt(free+'  POINTS',L.purse.gold[1],L.purse.cy,26,CREAM); txt('LEVEL '+level,L.purse.iron[1]+40,L.purse.cy,24,CREAM);
const rows=inTab(tab), R=L.rows, nReal=rows.length, nAll=nReal+L.sealed[tab];
txt(`(${rows.reduce((a,i)=>a+rank[i.key],0)} / ${nReal*3})`,268,L.lhead.cy+1,27,GOLD);
// the tree spine through the discs: lit up to the last learned skill
const dx=(R.icon[0]+R.icon[1])/2, y0=R.y0+R.h/2, y1=R.y0+(nAll-1)*R.step+R.h/2;
rect(dx-1.5,y0,3,y1-y0,'rgba(122,96,52,.45)');
let lit=-1; rows.forEach((it,i)=>{ if(rank[it.key]>0) lit=i; });
if(lit>0) rect(dx-1.5,y0,3,lit*R.step,'linear-gradient(180deg,#f0c66e,#b8903f)');
for(let i=0;i<nAll;i++){ const ry=R.y0+i*R.step, cy=ry+R.h/2, it=rows[i];
  if(i===sel) cellDiv('rsel',R.x+L.rsel.dx,ry+L.rsel.dy);
  if(!it){ cellC('ring',dx,cy,60); cellC('glyph_lock',dx,cy,32,'#6f6658'); cell('name_sealed',R.name[0],ry+R.name[1]-R.y0,DIM);
    txt('NOT YET REVEALED',R.deff[0],ry+R.deff[1]-R.y0,17,'#6f6658'); cell('sealed',R.state[0],ry+R.state[1]-R.y0,null,'r'); continue; }
  const rk=rank[it.key]; cellC(rk>0?'ring_on':'ring',dx,cy,60); cellC('glyph_'+it.glyph,dx,cy,40,rk>0?'#f3d58e':GLY);
  cell('name_'+it.key,R.name[0],ry+R.name[1]-R.y0,CREAM);
  for(let p=0;p<3;p++) cell(p<rk?'pip_on':'pip_off',R.deff[0]+p*20,ry+R.deff[1]-R.y0);
  txt('RANK '+rk+' / 3',R.deff[0]+70,ry+R.deff[1]-R.y0,17,DIM);
  const sy=ry+R.state[1]-R.y0;
  if(rk>=3) cell('maxed',R.state[0],sy,null,'r');
  else { const c=cost(it), e=txt(String(c),R.state[0],sy,28,free>=c?GOLD:RED,'r'); cell('spt',R.state[0]-e.getBoundingClientRect().width-32,sy); } }
// centre: the selected skill
const it=rows[sel], rk=rank[it.key], c=cost(it);
cell('title_'+it.key,L.ititle.cx,L.ititle.y,CREAM,'c'); cell('tag_'+it.key,L.ititle.cx,L.tags.y,'#ccc2ad','c');
cellC('ring_on',L.turn.cx,L.turn.cy-10,236); cellC('glyph_'+it.glyph,L.turn.cx,L.turn.cy-10,150,'#f3d58e');
for(let p=0;p<3;p++) cellC(p<rk?'bigpip_on':'bigpip_off',L.rankpips.cx+(p-1)*L.rankpips.step,L.rankpips.y,26);
txt(c+(c===1?' POINT':' POINTS'),616,637,30,free>=c?GREEN:RED);
txt(String(rk),826,637,28,CREAM); txt('▸',856,637,20,CREAM); txt(String(rk+1),884,637,28,GREEN); txt('OF 3',922,637,20,DIM);
cell('d1_'+it.key,566,L.bonus.lines[0],'#dbd1bd'); cell('learnhint',566,L.bonus.lines[1]+6,DIM);
cell('btn_on',L.buy.x,L.buy.cy); cell('key_e',L.buy.key[0],L.buy.key[1],null,'c'); txt('LEARN RANK '+(rk+1)+'  —  '+c+(c===1?' POINT':' POINTS'),L.buy.text,L.buy.cy,26,'#1a1208');
// right: MASTERY, every skill's ranks by weapon
cellDiv('rtab0',L.rtabs.eq[0],L.rtabs.y);
const MA=L.mastery; let y=MA.head0;
[['CROSSBOW',0],['SWORD',1],['AURAS',2]].forEach(([h,tb])=>{ txt(h,MA.x+6,y,19,GOLD); rect(MA.x+120,y,330,1,'rgba(122,96,52,.4)'); y+=34;
  inTab(tb).forEach(i=>{ const r=rank[i.key]; cellC('glyph_'+i.glyph,MA.icon,y,26,r>0?'#f3d58e':'#7d7060'); txt(i.name.toUpperCase(),MA.label,y,19,r>0?CREAM:DIM);
    for(let p=0;p<3;p++) cell(p<r?'pip_on':'pip_off',MA.pip0+p*MA.pipstep,y); y+=MA.step-6; }); y+=10; });
// points summary
rect(1150,y+4,485,1,'rgba(122,96,52,.4)');
cellC('spt',1186,y+40,26); txt('SKILL POINTS',1214,y+40,21,CREAM); txt(String(free),1610,y+40,28,GOLD,'r');
txt('One point per hero level. Next at level '+(level+1)+'.',1160,y+78,17,DIM);
})();
