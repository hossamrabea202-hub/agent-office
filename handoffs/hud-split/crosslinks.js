// i5: links that cross the edge of a y-band (the feature to move):  node crosslinks.js <export> <ylo> <yhi>
const fs = require('fs'), { parse, pinOf } = require('./t3d');
const [,, f, lo, hi] = process.argv; const { N, order } = parse(fs.readFileSync(f, 'utf8'));
const inB = n => N[n] && N[n].y >= +lo && N[n].y <= +hi;
const band = order.filter(inB); console.log('band nodes', band.length);
for (const n of band) for (const p of N[n].pins) for (const [m, pid] of p.links) if (!inB(m)) {
  const q = N[m] && pinOf(N[m], pid);
  console.log(`${p.dir === 'in' ? 'IN ' : 'OUT'} ${p.cat.padEnd(6)} ${n}.${p.name}  ${p.dir === 'in' ? '<-' : '->'}  ${m}.${q ? q.name : pid} (${N[m] ? N[m].cls + ' y' + N[m].y : 'MISSING'})`);
}
