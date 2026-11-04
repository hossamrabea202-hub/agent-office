const fs=require('fs');const lines=fs.readFileSync(process.argv[2],'utf8').split(/\r?\n/).filter(l=>l&&!l.startsWith('['));
const h=lines[0].split(',');const rows=lines.slice(1).map(l=>l.split(','));
const data=rows.filter(r=>r.length===h.length&&!isNaN(+r[0]));
const avg=i=>data.reduce((s,r)=>s+(+r[i]||0),0)/data.length;
console.log('frames',data.length,'cols',h.length);
for(const k of ['FrameTime','GameThreadTime','RenderThreadTime','RHIThreadTime','GPUTime','GameThreadTime_CriticalPath'])if(h.indexOf(k)>=0)console.log(k,avg(h.indexOf(k)).toFixed(1));
const pat=new RegExp(process.argv[3]||'^Exclusive/GameThread/');
const out=h.map((k,i)=>[k,avg(i)]).filter(([k])=>pat.test(k)).sort((a,b)=>b[1]-a[1]).slice(0,+process.argv[4]||25);
for(const [k,v] of out)console.log(v.toFixed(2).padStart(8),k);
