// #472 Track L (i5): read-only scan of whole-BP T3Ds for logic that silently does nothing. Only hand-made graphs count, the compiled copies in the export are skipped.
//   CUT CHAIN    impure node with no exec input but something after it: everything after it never runs (HalfHorse BeginPlay).
//   DEAD VALUE   impure node with no exec input whose output a running node reads: it gets an empty value (BattleDirector Target).
//   AND READ     array read with a literal index feeding a BooleanAND: Blueprint's AND does not short-circuit, so a length check next to it does not protect it (F11).
// Plain orphans with nothing connected are ignored: dead code, harmless. Usage: node t3d_orphans.js <file.T3D> [more]
const fs = require('fs');
const EXEC_IN = ['execute', 'Exec'];
let total = 0;
for (const f of process.argv.slice(2)) {
  let t; try { t = fs.readFileSync(f, 'utf8'); } catch (e) { continue; }
  const nodes = {};
  for (const m of t.matchAll(/Begin Object Name="([^"]+)" ExportPath="\/Script\/[A-Za-z]+\.(K2Node_\w+)'[^"]*:([^.'"]+)\.[^"]*"([\s\S]*?)\n\s*End Object/g)) {
    const [, name, cls, graph, b] = m;
    if (!b.includes('CustomProperties Pin') || /^(ExecuteUbergraph|EdGraph_|.*_MERGED|EvaluateGraphExposedInputs)/.test(graph)) continue;
    const pins = [...b.matchAll(/CustomProperties Pin \((.*)\)\s*$/gm)].map(x => x[1]).map(p => ({ n: (p.match(/PinName="([^"]+)"/) || [])[1], out: /EGPD_Output/.test(p), ex: /PinCategory="exec"/.test(p), dv: (p.match(/DefaultValue="([^"]*)"/) || [])[1],
      l: [...((p.match(/LinkedTo=\(([^)]*)\)/) || [, ''])[1]).matchAll(/(\w+) \w+/g)].map(x => x[1]) }));
    nodes[graph + '/' + name] = { name, cls, graph, pins, fn: (b.match(/(?:FunctionReference|VariableReference)=\([^)]*MemberName="(\w+)"/) || [, cls.replace('K2Node_', '')])[1], pure: /PureState=Pure|bIsPureFunc=True/.test(b) };
  }
  const get = (g, n) => nodes[g + '/' + n];
  const hasExecIn = n => n.pins.some(p => p.ex && !p.out);
  const wiredIn = n => n.pins.some(p => p.ex && !p.out && p.l.length);
  const out = [];
  for (const n of Object.values(nodes)) {
    if (!hasExecIn(n) || wiredIn(n) || n.pure) continue;
    const thenTo = n.pins.filter(p => p.ex && p.out).flatMap(p => p.l);
    const used = n.pins.filter(p => !p.ex && p.out).flatMap(p => p.l).filter(x => { const c = get(n.graph, x); return c && (!hasExecIn(c) || wiredIn(c)); });
    if (thenTo.length) out.push('CUT CHAIN  ' + n.graph + ' ' + n.name + ':' + n.fn + ' -> ' + thenTo.slice(0, 3).map(x => x + ':' + ((get(n.graph, x) || {}).fn || '')).join(', '));
    else if (used.length) out.push('DEAD VALUE ' + n.graph + ' ' + n.name + ':' + n.fn + ' read by ' + used.slice(0, 3).map(x => x + ':' + ((get(n.graph, x) || {}).fn || '')).join(', '));
  }
  for (const n of Object.values(nodes)) {
    if (n.cls !== 'K2Node_GetArrayItem') continue;
    const dim = n.pins.find(p => p.n === 'Dimension 1'); if (!dim || dim.l.length) continue;
    let front = n.pins.filter(p => p.out).flatMap(p => p.l), seen = new Set(), hit = false;
    for (let i = 0; i < 4 && front.length && !hit; i++) {
      const nx = [];
      for (const x of front) { if (seen.has(x)) continue; seen.add(x); const c = get(n.graph, x); if (!c) continue; if (/BooleanAND/.test(c.fn)) hit = true; if (!hasExecIn(c)) nx.push(...c.pins.filter(p => p.out).flatMap(p => p.l)); }
      front = nx;
    }
    if (hit) out.push('AND READ   ' + n.graph + ' ' + n.name + '[' + (dim.dv || '0') + ']');
  }
  if (out.length) { total += out.length; console.log('\n## ' + f.split(/[\\/]/).pop().replace(/\.T3D$/, '') + ' (' + out.length + ')\n  ' + out.slice(0, 40).join('\n  ')); }
}
console.log('\ntotal findings', total);
