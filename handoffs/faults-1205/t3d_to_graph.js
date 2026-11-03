// faults-1205 (i5): turn one graph of a whole-BP T3D export into the Ctrl+A / Ctrl+C graph format applyall reads.
// In the whole-BP file a node is defined as `Begin Object Name="X" ExportPath="/Script/BlueprintGraph.K2Node_Y'...:Graph.X'"`
// (indented); in a graph copy it is `Begin Object Class=/Script/BlueprintGraph.K2Node_Y Name="X" ExportPath=...` at column 0.
// Usage: node t3d_to_graph.js <whole.t3d.txt> <GraphName> <out.txt>
const fs = require('fs');
const [, , src, graph, out] = process.argv;
const t = fs.readFileSync(src, 'utf8');
const re = /^([ \t]*)Begin Object Name="([^"]+)" ExportPath="(\/Script\/BlueprintGraph\.(K2Node_\w+)'[^"]*:([^.'"]+)\.[^"]*)"\r?\n([\s\S]*?)^\1End Object/gm;
const parts = []; let m;
while ((m = re.exec(t))) {
  const [, ind, name, xp, cls, g, body] = m;
  if (g !== graph || !body.includes('CustomProperties Pin')) continue;
  const lines = body.split(/\r?\n/).filter(l => l.length).map(l => l.startsWith(ind) ? l.slice(ind.length) : l);
  parts.push(['Begin Object Class=/Script/BlueprintGraph.' + cls + ' Name="' + name + '" ExportPath="' + xp + '"', ...lines, 'End Object'].join('\r\n'));
}
fs.writeFileSync(out, parts.join('\r\n') + '\r\n');
console.log(graph, parts.length, 'nodes ->', out);
