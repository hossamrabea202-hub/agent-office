const fs=require('fs'),rl=require('readline').createInterface({input:fs.createReadStream(process.argv[2])});
const st=[];let frames=0;const byBP={},under={},callers={};
const sh=n=>n.replace(/^Function\/Game\/CastleDefender\//,'').replace(/^.*\/(\w+)\.\1_C\./,'$1.');
const add=(o,k,v)=>o[k]=(o[k]||0)+v;
rl.on('line',l=>{if(l.startsWith('TimerName'))return;const i=l.lastIndexOf(',');const d=+l.slice(i+1);const r=l.slice(0,i);const j=r.lastIndexOf(','),k=r.lastIndexOf(',',j-1);
 const name=r.slice(0,k).replace(/^"|"$/g,''),t0=+r.slice(k+1,j),t1=+r.slice(j+1);const dur=(t1-t0)*1000;
 st.length=d;st[d]=name;if(name==='Frame'&&d===1)frames++;
 const isBP=/_C\.|ExecuteUbergraph/.test(name);
 // nearest BP ancestor
 let anc=null,top=null;for(let a=d-1;a>=0;a--){if(/_C\./.test(st[a])){if(!anc)anc=st[a];top=st[a];}}
 if(/LineOfSightTo|GetAllActorsWithTag|GetAllActorsOfClass|GetActorOfClass|LineTrace|SimpleMoveTo|SpawnSystem|SpawnEmitter|SpawnActor/.test(name))add(callers,name+'  <=  '+(anc?sh(anc):'(native: '+st[d-1]+')'),dur);
 if(/_C\.ReceiveTick$|_C\.ReceiveDrawHUD$|_C\.Think$|_C\.\w+$/.test(name)&&!(top&&top!==name))add(byBP,sh(name),dur); // top-level BP entry points only
 for(let a=d-1;a>=0;a--)if(/BP_SoldierSword_C\.ReceiveTick$/.test(st[a])){if(a===d-1||a===d-2)add(under,(d-a)+' '+sh(name),dur);break;}
});
rl.on('close',()=>{const F=frames;console.log('game frames',F);const pr=(t,o,n)=>{console.log('== '+t);Object.entries(o).sort((a,b)=>b[1]-a[1]).slice(0,n).forEach(([k,v])=>console.log((v/F).toFixed(2).padStart(7),'ms/f ',k.slice(0,130)))};
pr('top-level Blueprint entry points (inclusive)',byBP,22);pr('inside BP_SoldierSword ReceiveTick (depth 1-2)',under,25);pr('expensive calls by Blueprint caller',callers,25);});
