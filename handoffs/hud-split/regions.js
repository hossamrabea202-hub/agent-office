// i5 HUD split: segment a generated graph export into feature regions by gaps in NodePosY (then X), name each region by
// the texts / vars it uses.   node regions.js <export.txt> [gap=1500]
const fs = require('fs');
const txt = fs.readFileSync(process.argv[2], 'utf8'), GAP = +(process.argv[3] || 1500);
const nodes = txt.split(/^Begin Object /m).slice(1).map(b => {
  const g = re => (b.match(re) || [])[1];
  return { name: g(/Name="([^"]+)"/), cls: (g(/Class=([^\s]+)/) || '').split('.').pop(), x: +(g(/NodePosX=(-?\d+)/) || 0), y: +(g(/NodePosY=(-?\d+)/) || 0),
    strs: [...b.matchAll(/DefaultValue="([^"]{3,50})"/g)].map(m => m[1]).filter(s => /[A-Za-z]{3}/.test(s) && !/^\(|^\/|^[A-Z_]+$|Script|Game\/|^(true|false|None)$/.test(s)),
    vars: [...b.matchAll(/VariableReference=\((?:MemberParent=[^,]*,)?MemberName="([^"]+)"/g)].map(m => m[1]), size: b.length };
});
const ys = nodes.map(n => n.y).sort((a, b) => a - b);
const cuts = []; for (let i = 1; i < ys.length; i++) if (ys[i] - ys[i - 1] > GAP) cuts.push((ys[i] + ys[i - 1]) / 2);
const bands = []; let lo = -Infinity;
for (const c of cuts.concat([Infinity])) { bands.push(nodes.filter(n => n.y > lo && n.y <= c)); lo = c; }
bands.forEach((b, i) => {
  const cnt = f => { const o = {}; b.forEach(n => f(n).forEach(v => o[v] = (o[v] || 0) + 1)); return Object.entries(o).sort((p, q) => q[1] - p[1]); };
  console.log(`#${i} y ${Math.min(...b.map(n => n.y))}..${Math.max(...b.map(n => n.y))}  ${b.length} nodes  ${(b.reduce((s, n) => s + n.size, 0) / 1e6).toFixed(2)} MB`);
  console.log('   texts:', cnt(n => n.strs).slice(0, 8).map(e => e[0]).join(' | '));
  console.log('   vars :', cnt(n => n.vars).slice(0, 10).map(e => e.join('x')).join(', '));
});
