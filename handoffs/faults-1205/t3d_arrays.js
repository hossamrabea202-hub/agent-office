// faults-1205 (i5): list every GetArrayItem in a whole-BP T3D: graph, node, what feeds the Array pin, the index (literal or
// source), and which node consumes it. Usage: node t3d_arrays.js <file.t3d.txt> [filter regex on the array source]
const fs = require('fs');
const t = fs.readFileSync(process.argv[2], 'utf8');
const re = new RegExp(process.argv[3] || '.', 'i');
// split into node blocks (indented Begin Object Class=... K2Node ... End Object)
// whole-BP T3D: nodes are declared (Begin Object Class=... Name=...) and later defined (Begin Object Name=... ExportPath=
// "/Script/BlueprintGraph.K2Node_X'...:Graph.Name'") with the pins; keep the blocks that carry pins
const blocks = [...t.matchAll(/Begin Object (?:Class=\S+ )?Name="([^"]+)" ExportPath="\/Script\/BlueprintGraph\.(K2Node_\w+)'[^"]*:([^.'"]+)\.[^"]*"([\s\S]*?)\n\s*End Object/g)];
const by = {};
for (const [, name, cls, graph, body] of blocks) if (body.includes('CustomProperties Pin')) by[graph + '/' + name] = { cls, name, graph, body };
const pins = b => [...b.body.matchAll(/CustomProperties Pin \((.*)\)\s*$/gm)].map(m => m[1]);
const pin = (b, nm) => pins(b).find(p => p.includes('PinName="' + nm + '"'));
const links = p => p ? [...(p.match(/LinkedTo=\(([^)]*)\)/) || [, ''])[1].matchAll(/(\w+) (\w+)/g)].map(m => m[1]) : [];
const dv = p => p && (p.match(/DefaultValue="([^"]*)"/) || [])[1];
const desc = (g, n) => {
  const b = by[g + '/' + n]; if (!b) return n;
  const v = (b.body.match(/VariableReference=\([^)]*MemberName="([^"]+)"/) || [])[1];
  const f = (b.body.match(/FunctionReference=\([^)]*MemberName="([^"]+)"/) || [])[1];
  return n + '[' + b.cls.replace('K2Node_', '') + (v ? ':' + v : '') + (f ? ':' + f : '') + ']';
};
for (const b of Object.values(by)) {
  if (b.cls !== 'K2Node_GetArrayItem') continue;
  const arr = links(pin(b, 'Array')).map(n => desc(b.graph, n)).join('+') || 'unlinked';
  if (!re.test(arr)) continue;
  const ip = pin(b, 'Dimension 1');
  const idx = links(ip).length ? links(ip).map(n => desc(b.graph, n)).join('+') : 'literal ' + dv(ip);
  const outp = pins(b).find(p => /Direction="EGPD_Output"/.test(p));
  console.log(b.graph.padEnd(14), b.name.padEnd(22), 'array <-', arr, '| index <-', idx, '| ->', links(outp).map(n => desc(b.graph, n)).join(', '));
}
