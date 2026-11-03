// faults-1205 (i5): from a pure node, follow outputs until the first node with exec pins (impure) and print it with the node
// that feeds its 'execute'. Usage: node t3d_consumer.js <file.t3d.txt> <node> [<node> ...]
const fs = require('fs'); const t = fs.readFileSync(process.argv[2], 'utf8');
const blocks = [...t.matchAll(/Begin Object (?:Class=\S+ )?Name="([^"]+)" ExportPath="\/Script\/BlueprintGraph\.(K2Node_\w+)'[^"]*:([^.'"]+)\.[^"]*"([\s\S]*?)\n\s*End Object/g)];
const by = {};
for (const [, name, cls, graph, body] of blocks) if (body.includes('CustomProperties Pin')) by[name] = { cls, name, graph, body };
const pins = b => [...b.body.matchAll(/CustomProperties Pin \((.*)\)\s*$/gm)].map(m => m[1]);
const links = p => [...((p.match(/LinkedTo=\(([^)]*)\)/) || [, ''])[1]).matchAll(/(\w+) (\w+)/g)].map(m => m[1]);
const isExec = b => pins(b).some(p => /PinCategory="exec"/.test(p));
const fn = b => (b.body.match(/(?:FunctionReference|VariableReference)=\([^)]*MemberName="([^"]+)"/) || [, b.cls])[1];
for (const start of process.argv.slice(3)) {
  const seen = new Set(); let front = [start]; const hits = [];
  while (front.length) {
    const nx = [];
    for (const n of front) {
      const b = by[n]; if (!b || seen.has(n)) continue; seen.add(n);
      if (n !== start && isExec(b)) { const ex = pins(b).find(p => /PinName="execute"/.test(p)); hits.push(n + '[' + fn(b) + '] exec<-' + (ex ? links(ex).join('+') : '?')); continue; }
      for (const p of pins(b)) if (/EGPD_Output/.test(p) && !/PinCategory="exec"/.test(p)) nx.push(...links(p));
    }
    front = nx;
  }
  console.log(start, '=>', [...new Set(hits)].join(' | '));
}
