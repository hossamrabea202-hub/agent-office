// i5: for every DynamicCast in a graph export, list the nodes that read its As<Class> output and say whether each
// reader is reached ONLY through the cast's success exec ("then") or also from elsewhere (= Accessed None when the
// cast fails).   node castreads.js <export.txt> [classSubstring]
const fs = require('fs');
const txt = fs.readFileSync(process.argv[2], 'utf8'), want = process.argv[3] || 'ThirdPersonCharacter';
const N = {};
for (const b of txt.split(/^Begin Object /m).slice(1)) {
  const name = (b.match(/Name="([^"]+)"/) || [])[1], cls = ((b.match(/Class=([^\s]+)/) || [])[1] || '').split('.').pop();
  const pins = [...b.matchAll(/CustomProperties Pin \((.*)\)\s*$/gm)].map(m => {
    const p = m[1]; return { id: (p.match(/PinId=([0-9A-F]+)/) || [])[1], name: (p.match(/PinName="([^"]+)"/) || [])[1],
      dir: /Direction="EGPD_Output"/.test(p) ? 'out' : 'in', exec: /PinCategory="exec"/.test(p),
      links: ((p.match(/LinkedTo=\(([^)]*)\)/) || [])[1] || '').split(',').map(s => s.trim().split(' ')[0]).filter(Boolean) };
  });
  N[name] = { name, cls, pins, target: (b.match(/TargetType="([^"]+)"/) || [])[1] || '', text: b };
}
// exec successors
const succ = n => N[n].pins.filter(p => p.exec && p.dir === 'out').flatMap(p => p.links.map(l => [p.name, l]));
const preds = {}; Object.keys(N).forEach(n => succ(n).forEach(([p, m]) => (preds[m] = preds[m] || []).push([n, p])));
const impureReaders = (n, seen = new Set()) => { // pure readers forward to the impure (exec) nodes that consume them
  if (seen.has(n)) return []; seen.add(n);
  if (N[n].pins.some(p => p.exec)) return [n];
  return N[n].pins.filter(p => p.dir === 'out').flatMap(p => p.links).filter(m => N[m]).flatMap(m => impureReaders(m, seen));
};
for (const c of Object.values(N).filter(n => n.cls === 'K2Node_DynamicCast' && n.target.includes(want))) {
  const asPin = c.pins.find(p => p.name.startsWith('As')); if (!asPin) continue;
  const then = c.pins.find(p => p.exec && p.dir === 'out' && p.name === 'then');
  // nodes reachable only via then: forward walk from then
  const okSet = new Set(); const st = [...(then ? then.links : [])];
  while (st.length) { const u = st.pop(); if (!N[u] || okSet.has(u)) continue; okSet.add(u); succ(u).forEach(([, m]) => st.push(m)); }
  const readers = [...new Set(asPin.links.filter(m => N[m]).flatMap(m => impureReaders(m)))];
  const bad = readers.filter(r => !okSet.has(r) || (preds[r] || []).some(([p]) => !okSet.has(p) && p !== c.name));
  console.log(`${c.name} (${asPin.name}) readers ${readers.length}, OUTSIDE the success path: ${bad.length}`);
  bad.forEach(r => console.log('   ', r, N[r].cls, 'fed from', (preds[r] || []).map(x => x.join('.')).join(', ')));
}
