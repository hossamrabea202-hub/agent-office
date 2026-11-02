// i5 HUD split: per region (same y-gap segmentation as regions.js), which variables are used ONLY there (move into the
// new component) and which are shared with other regions (stay on the HUD, read through the Hud reference).
const fs = require('fs');
const txt = fs.readFileSync(process.argv[2], 'utf8'), GAP = 1500;
const nodes = txt.split(/^Begin Object /m).slice(1).map(b => ({ y: +((b.match(/NodePosY=(-?\d+)/) || [])[1] || 0),
  vars: [...b.matchAll(/VariableReference=\(([^)]*)\)/g)].filter(m => /bSelfContext=True/.test(m[1]) || !/MemberParent/.test(m[1])).map(m => (m[1].match(/MemberName="([^"]+)"/) || [])[1]).filter(Boolean),
  ext: [...b.matchAll(/VariableReference=\(([^)]*)\)/g)].filter(m => /MemberParent/.test(m[1]) && !/bSelfContext=True/.test(m[1])).map(m => (m[1].match(/MemberName="([^"]+)"/) || [])[1]) }));
const ys = nodes.map(n => n.y).sort((a, b) => a - b), cuts = [];
for (let i = 1; i < ys.length; i++) if (ys[i] - ys[i - 1] > GAP) cuts.push((ys[i] + ys[i - 1]) / 2);
const band = y => cuts.filter(c => y > c).length;
const where = {};
nodes.forEach(n => n.vars.forEach(v => (where[v] = where[v] || new Set()).add(band(n.y))));
for (const r of process.argv.slice(3).map(Number)) {
  const vs = [...new Set(nodes.filter(n => band(n.y) === r).flatMap(n => n.vars))];
  console.log(`region #${r}: ${vs.length} self vars`);
  console.log('  ONLY here (move):', vs.filter(v => where[v].size === 1).join(', '));
  console.log('  SHARED (stay on HUD):', vs.filter(v => where[v].size > 1).map(v => v + '[' + [...where[v]].join('') + ']').join(', '));
  const ex = [...new Set(nodes.filter(n => band(n.y) === r).flatMap(n => n.ext))];
  console.log('  other objects\' vars:', ex.slice(0, 30).join(', '));
}
