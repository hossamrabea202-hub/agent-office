// print a node's pins: name = default / <- linked sources ; usage: node t3d_node.js <file> <node> [...]
const fs = require('fs'); const t = fs.readFileSync(process.argv[2], 'utf8');
const blocks = [...t.matchAll(/Begin Object (?:Class=\S+ )?Name="([^"]+)" ExportPath="\/Script\/BlueprintGraph\.(K2Node_\w+)'[^"]*:([^.'"]+)\.[^"]*"([\s\S]*?)\n\s*End Object/g)];
const by = {}; for (const [, name, cls, graph, body] of blocks) if (body.includes('CustomProperties Pin')) by[name] = { cls, body };
for (const n of process.argv.slice(3)) {
  const b = by[n]; if (!b) { console.log(n, 'not found'); continue; }
  const f = (b.body.match(/(?:FunctionReference|VariableReference)=\([^)]*MemberName="([^"]+)"/) || [, ''])[1];
  const ps = [...b.body.matchAll(/CustomProperties Pin \((.*)\)\s*$/gm)].map(m => m[1]).map(p => {
    const nm = (p.match(/PinName="([^"]+)"/) || [])[1], dv = (p.match(/DefaultValue="([^"]*)"/) || [])[1];
    const lk = [...((p.match(/LinkedTo=\(([^)]*)\)/) || [, ''])[1]).matchAll(/(\w+) \w+/g)].map(m => m[1]);
    return (/EGPD_Output/.test(p) ? '>' : '<') + nm + (dv !== undefined && dv !== '' ? '=' + dv : '') + (lk.length ? (/EGPD_Output/.test(p) ? ' -> ' : ' <- ') + lk.join('+') : '');
  }).filter(s => !/^.(self|__WorldContext)/.test(s));
  console.log(n, '[' + b.cls.replace('K2Node_', '') + (f ? ':' + f : '') + ']', ps.join(' | '));
}
