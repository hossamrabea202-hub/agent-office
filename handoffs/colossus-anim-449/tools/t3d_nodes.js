// node t3d_nodes.js <file.t3d> [filter words...]: list graph nodes (any nesting depth) with class, function and links.
// With filter words, prints only nodes whose name / function / defaults match, plus every node linked to them.
const fs = require('fs');
const [file, ...filters] = process.argv.slice(2);
const txt = fs.readFileSync(file, 'utf8');
const nodes = {}; const stack = []; let cur = null;
for (const line of txt.split(/\r?\n/)) {
  const b = line.match(/^\s*Begin Object (?:Class=(\S+) )?Name="([^"]+)"/);
  if (b) {
    const isNode = b[1] && /K2Node_/.test(b[1]);
    let obj = isNode ? { name: b[2], cls: b[1].replace(/.*\./, '').replace(/'$/, ''), fn: '', pins: [] } : null;
    if (!b[1] && nodes[b[2]]) obj = nodes[b[2]];            // second pass: the property block of a declared node
    if (obj && !nodes[obj.name]) nodes[obj.name] = obj;
    stack.push(obj); if (obj) cur = obj; continue;
  }
  if (/^\s*End Object/.test(line)) { stack.pop(); cur = [...stack].reverse().find(o => o) || null; continue; }
  if (!cur) continue;
  const fr = line.match(/(?:FunctionReference|EventReference|VariableReference)=\(MemberName="([^"]+)"/);
  if (fr && !cur.fn) cur.fn = fr[1];
  const ce = line.match(/CustomFunctionName="([^"]+)"/); if (ce) cur.fn = 'EVENT ' + ce[1];
  const p = line.match(/CustomProperties Pin \(PinId=\w+,PinName="([^"]+)"(.*)\)\s*$/);
  if (p) {
    const dir = /Direction="EGPD_Output"/.test(p[2]) ? 'out' : 'in';
    const exec = /PinCategory="exec"/.test(p[2]);
    const links = [...p[2].matchAll(/LinkedTo=\(([^)]*)\)/g)].flatMap(m => m[1].trim().split(/,\s*/).filter(Boolean).map(x => x.split(' ')[0]));
    const def = (p[2].match(/DefaultObject="[^"]*\.([^".]+)"/) || p[2].match(/DefaultValue="([^"]*)"/) || [])[1];
    cur.pins.push({ name: p[1], dir, exec, links, def });
  }
}
const match = n => !filters.length || filters.some(f => (n.name + ' ' + n.fn + ' ' + n.pins.map(p => p.def || '').join(' ')).toLowerCase().includes(f.toLowerCase()));
const show = new Set(Object.values(nodes).filter(match).map(n => n.name));
for (const n of [...show]) for (const p of nodes[n].pins) for (const l of p.links) show.add(l);
for (const name of show) {
  const n = nodes[name]; if (!n) continue;
  const ins = n.pins.filter(p => p.dir === 'in' && p.name !== 'self' && (p.links.length || (p.def && !['0', 'false', '', '0.0', 'None'].includes(p.def)))).map(p => `${p.name}${p.exec ? '!' : ''}<-${p.links.join('|') || ('"' + p.def + '"')}`);
  const outs = n.pins.filter(p => p.dir === 'out' && p.links.length).map(p => `${p.name}${p.exec ? '!' : ''}->${p.links.join('|')}`);
  console.log(`${name} [${n.cls}${n.fn ? ' ' + n.fn : ''}]\n    in:  ${ins.join('  ')}\n    out: ${outs.join('  ')}`);
}
console.log(`# ${Object.keys(nodes).length} nodes`);
