// i5 HUD split: cut a graph export at its Event + Sequence nodes and report each connected chunk
// (node count, the texts it draws, vars it reads/writes, functions it calls).   node chunks.js <export.txt>
const fs = require('fs');
const txt = fs.readFileSync(process.argv[2], 'utf8');
const blocks = txt.split(/^Begin Object /m).slice(1);
const N = {}, order = [];
for (const b of blocks) {
  const head = b.split('\n')[0];
  const name = (head.match(/Name="([^"]+)"/) || [])[1]; const cls = ((head.match(/Class=([^\s]+)/) || [])[1] || '').split('.').pop();
  const links = [...b.matchAll(/LinkedTo=\(([^)]*)\)/g)].flatMap(m => m[1].split(',').map(s => s.trim().split(' ')[0]).filter(Boolean));
  const pins = [...b.matchAll(/PinName="([^"]+)"[^\n]*?LinkedTo=\(([^)]*)\)/g)].map(m => [m[1], m[2].split(',').map(s => s.trim().split(' ')[0]).filter(Boolean)]);
  const strs = [...b.matchAll(/DefaultValue="([^"]{3,60})"/g)].map(m => m[1]).filter(s => /[A-Za-z]{3}/.test(s) && !/^\(|^\/|^[A-Z_]+$|Script|Game\//.test(s));
  const fn = (b.match(/FunctionReference=\((?:MemberParent=[^,]*,)?MemberName="([^"]+)"/) || [])[1];
  const vars = [...b.matchAll(/VariableReference=\((?:MemberParent=[^,]*,)?MemberName="([^"]+)"/g)].map(m => (cls === 'K2Node_VariableSet' ? 'SET ' : '') + m[1]);
  const y = +((b.match(/NodePosY=(-?\d+)/) || [])[1] || 0), x = +((b.match(/NodePosX=(-?\d+)/) || [])[1] || 0);
  N[name] = { name, cls, links, pins, strs, fn, vars, x, y }; order.push(name);
}
const cut = new Set(order.filter(n => /K2Node_Event$|ExecutionSequence/.test(N[n].cls)));
const adj = {}; order.forEach(n => adj[n] = new Set());
order.forEach(n => N[n].links.forEach(m => { if (N[m]) { adj[n].add(m); adj[m].add(n); } }));
const seen = new Set(), chunks = [];
for (const s of order) {
  if (seen.has(s) || cut.has(s)) continue;
  const st = [s], comp = []; seen.add(s);
  while (st.length) { const u = st.pop(); comp.push(u); adj[u].forEach(v => { if (!seen.has(v) && !cut.has(v)) { seen.add(v); st.push(v); } }); }
  // which cut node + pin feeds this chunk
  const feeds = []; cut.forEach(c => N[c].pins.forEach(([p, ls]) => ls.forEach(l => { if (comp.includes(l)) feeds.push(c + '.' + p); })));
  chunks.push({ comp, feeds });
}
chunks.sort((a, b) => b.comp.length - a.comp.length);
console.log('cut nodes:', [...cut].map(c => c + '(' + N[c].pins.map(p => p[0]).join('/') + ')').join(' '));
for (const ch of chunks.slice(0, 40)) {
  const cnt = (f) => { const o = {}; ch.comp.forEach(n => f(N[n]).forEach(v => o[v] = (o[v] || 0) + 1)); return Object.entries(o).sort((a, b) => b[1] - a[1]); };
  const xs = ch.comp.map(n => N[n].x), ys = ch.comp.map(n => N[n].y);
  console.log(`\n## ${ch.comp.length} nodes  fed by ${ch.feeds.join(',') || '-'}  box x ${Math.min(...xs)}..${Math.max(...xs)} y ${Math.min(...ys)}..${Math.max(...ys)}`);
  console.log('  texts:', cnt(n => n.strs).slice(0, 10).map(e => e[0]).join(' | '));
  console.log('  vars :', cnt(n => n.vars).slice(0, 14).map(e => e.join('x')).join(', '));
  console.log('  fns  :', cnt(n => n.fn ? [n.fn] : []).slice(0, 10).map(e => e.join('x')).join(', '));
}
