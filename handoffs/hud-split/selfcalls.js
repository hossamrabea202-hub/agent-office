// list self-context function calls and self var refs in a y-band of a graph export:  node selfcalls.js <export> <ylo> <yhi>
const fs = require('fs'); const [,, f, lo, hi] = process.argv;
const o = {}, v = {}, other = {};
for (const b of fs.readFileSync(f, 'utf8').split(/^Begin Object /m).slice(1)) {
  const y = +((b.match(/NodePosY=(-?\d+)/) || [])[1] || 0); if (y < +lo || y > +hi) continue;
  const cls = ((b.match(/Class=([^\s]+)/) || [])[1] || '').split('.').pop();
  const fr = (b.match(/FunctionReference=\(([^)]*)\)/) || [])[1];
  if (fr) { const k = (fr.match(/MemberName="([^"]+)"/) || [])[1] + (/bSelfContext=True/.test(fr) ? ' [SELF]' : /MemberParent="([^"]+)"/.test(fr) ? ' <' + fr.match(/MemberParent="[^']*'([^']+)'/)?.[1]?.split('.').pop() + '>' : ''); o[k] = (o[k] || 0) + 1; }
  const vr = (b.match(/VariableReference=\(([^)]*)\)/) || [])[1];
  if (vr) { const k = cls.replace('K2Node_Variable', '') + ' ' + (vr.match(/MemberName="([^"]+)"/) || [])[1] + (/bSelfContext=True/.test(vr) ? ' [SELF]' : ''); v[k] = (v[k] || 0) + 1; }
  if (!fr && !vr) other[cls] = (other[cls] || 0) + 1;
}
console.log('FUNCTIONS:', Object.entries(o).sort((a, b) => b[1] - a[1]).map(e => e.join('x')).join(', '));
console.log('\nVARS:', Object.entries(v).sort((a, b) => b[1] - a[1]).map(e => e.join('x')).join(', '));
console.log('\nOTHER NODES:', Object.entries(other).map(e => e.join('x')).join(', '));
