// i5 HUD split: summarize a pasted-graph export (T3D text): node classes, events, comment boxes, nodes per comment box.
//   node analyze_graph.js <export.txt>  > summary.txt
const fs = require('fs');
const txt = fs.readFileSync(process.argv[2], 'utf8');
const blocks = txt.split(/^Begin Object /m).slice(1);
const nodes = blocks.map(b => {
  const head = b.split('\n')[0];
  const cls = (head.match(/Class=([^\s]+)/) || [])[1] || '?';
  const name = (head.match(/Name="([^"]+)"/) || [])[1] || '?';
  const g = k => { const m = b.match(new RegExp('^\s*' + k + '=(.*)$', 'm')); return m ? m[1].trim() : null; };
  const x = +g('NodePosX') || 0, y = +g('NodePosY') || 0, w = +g('NodeWidth') || 0, h = +g('NodeHeight') || 0;
  const ev = (b.match(/CustomFunctionName="([^"]+)"/) || b.match(/EventReference=\(MemberParent=[^,]+,MemberName="([^"]+)"/) || [])[1];
  const fn = (b.match(/FunctionReference=\((?:MemberParent=[^,]*,)?MemberName="([^"]+)"/) || [])[1];
  const vars = [...b.matchAll(/VariableReference=\((?:MemberParent=[^,]*,)?MemberName="([^"]+)"/g)].map(m => m[1]);
  const comment = cls.includes('EdGraphNode_Comment') ? (g('NodeComment') || '').replace(/^"|"$/g, '') : null;
  return { cls: cls.split('.').pop(), name, x, y, w, h, ev, fn, vars, comment, keyKey: (b.match(/InputKey=([^\s,)]+)/) || [])[1] };
});
const comments = nodes.filter(n => n.comment !== null);
const others = nodes.filter(n => n.comment === null);
console.log('nodes', nodes.length, 'comments', comments.length);
const byCls = {}; others.forEach(n => byCls[n.cls] = (byCls[n.cls] || 0) + 1);
console.log('classes', Object.entries(byCls).sort((a, b) => b[1] - a[1]).slice(0, 15).map(e => e.join(':')).join(' '));
console.log('\nEVENTS / custom events / input keys:');
others.filter(n => n.ev || n.keyKey).forEach(n => console.log('  ', n.cls, n.ev || n.keyKey, '@', n.x, n.y));
console.log('\nCOMMENT BOXES (largest first): nodes inside, vars used');
comments.map(c => {
  const inside = others.filter(n => n.x >= c.x && n.x <= c.x + c.w && n.y >= c.y && n.y <= c.y + c.h);
  const vs = {}; inside.forEach(n => n.vars.forEach(v => vs[v] = (vs[v] || 0) + 1));
  return { c, n: inside.length, vs };
}).sort((a, b) => b.n - a.n).forEach(r => console.log(String(r.n).padStart(5), JSON.stringify(r.c.comment.slice(0, 70)), '| vars:', Object.keys(r.vs).slice(0, 12).join(',')));
