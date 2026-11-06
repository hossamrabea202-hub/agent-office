// node t3d_eventgraph.js <whole-BP export.t3d> <out EventGraph.txt>
// A whole-BP T3D export nests the EventGraph nodes under Blueprint > EdGraph and declares every node twice (a Class
// line, then a property block by name). applyall wants the clipboard layout: one flat block per node. This rewrites
// the EventGraph that way (same node names, same pins), so applyall can merge against a whole-BP export.
const fs = require('fs');
const [src, out] = process.argv.slice(2);
const lines = fs.readFileSync(src, 'utf8').split(/\r?\n/);
let inGraph = false, depth = 0, cur = null; const decl = {}, props = {}, order = [];
for (const line of lines) {
  // the graph itself is declared twice too: "Class=EdGraph Name=X" (with the node declarations) and later "Name=X" (with the node properties)
  const g = line.match(/^\s*Begin Object (?:Class=\/Script\/Engine\.EdGraph )?Name="([^"]+)" ExportPath="\/Script\/Engine\.EdGraph'/);
  if (g) { inGraph = g[1] === 'EventGraph'; depth = 1; continue; }
  if (!inGraph) continue;
  const b = line.match(/^\s*Begin Object (?:Class=(\S+) )?Name="([^"]+)"(.*)$/);
  if (b) {
    depth++;
    if (depth === 2) {
      if (b[1]) { decl[b[2]] = `Begin Object Class=${b[1]} Name="${b[2]}"${b[3]}`; order.push(b[2]); cur = null; }
      else { cur = b[2]; props[cur] = []; }
    } else if (cur) props[cur].push(line.replace(/^ {6}/, ''));   // nested objects inside a node keep their relative indent
    continue;
  }
  if (/^\s*End Object/.test(line)) {
    depth--;
    if (depth === 1) cur = null;
    else if (depth >= 2 && cur) props[cur].push(line.replace(/^ {6}/, ''));
    if (depth === 0) { inGraph = false; }
    continue;
  }
  if (cur) props[cur].push(line.replace(/^ {6}/, ''));
}
const outLines = [];
for (const n of order) { outLines.push(decl[n]); for (const l of (props[n] || [])) outLines.push(l); outLines.push('End Object'); }
fs.writeFileSync(out, outLines.join('\r\n') + '\r\n');
console.log(`${out}: ${order.length} nodes`);
