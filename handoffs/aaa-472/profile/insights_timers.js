const fs=require('fs');const L=fs.readFileSync(process.argv[2],'utf8').split(/\r?\n/).slice(1).filter(Boolean);
const F=+process.argv[4]||47;const re=new RegExp(process.argv[3]||'.');const col=process.argv[5]==='incl'?3:8;
const r=L.map(l=>{const m=l.match(/^("(?:[^"]|"")*"|[^,]*),(.*)$/);const n=m[1].replace(/^"|"$/g,'');const v=m[2].split(',');return [n,+v[0],+v[col-1]]}).filter(x=>re.test(x[0]));
r.sort((a,b)=>b[2]-a[2]);for(const [n,c,t] of r.slice(0,+process.argv[6]||30))console.log((t*1000/F).toFixed(2).padStart(7),'ms/f',String(Math.round(c/F)).padStart(6),'calls/f ',n.slice(0,110));
