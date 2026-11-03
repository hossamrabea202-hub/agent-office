// #472 (i5): readable exec flow of a whole-BP T3D: from an event (or node), the exec tree, each node with its data inputs
// expanded through pure nodes. Usage: node t3d_flow.js <file> <event or node name> [maxNodes]; no name = list the events.
const fs = require('fs'); const t = fs.readFileSync(process.argv[2], 'utf8');
const blocks = [...t.matchAll(/Begin Object (?:Class=\S+ )?Name="([^"]+)" ExportPath="\/Script\/[A-Za-z]+\.(\w+)'[^"]*:([^.'"]+)\.[^"]*"([\s\S]*?)\n\s*End Object/g)];
const by = {}; for (const [, name, cls, graph, body] of blocks) if (body.includes('CustomProperties Pin')) by[name] = { name, cls: cls.replace('K2Node_', ''), graph, body };
const pins = b => [...b.body.matchAll(/CustomProperties Pin \((.*)\)\s*$/gm)].map(m => m[1]).map(p => ({
  name: (p.match(/PinName="([^"]+)"/) || [])[1], dv: (p.match(/DefaultValue="([^"]*)"/) || [])[1], ao: (p.match(/DefaultObject="([^"]*)"/) || [])[1], out: /EGPD_Output/.test(p), exec: /PinCategory="exec"/.test(p),
  links: [...((p.match(/LinkedTo=\(([^)]*)\)/) || [, ''])[1]).matchAll(/(\w+) (\w+)/g)].map(m => m[1]), hidden: /bHidden=True/.test(p) }));
const label = b => { const m = b.body.match(/(?:FunctionReference|VariableReference|EventReference|MacroGraphReference)=\(([^)]*)\)/); let k = '';
  if (m) { k = (m[1].match(/MemberName="([^"]+)"/) || [])[1] || (m[1].match(/:(\w+)'"?,GraphBlueprint/) || m[1].match(/Graph="[^"]*:(\w+)/) || [])[1] || ''; const par = (m[1].match(/MemberParent="[^"]*\.(\w+)'"/) || [])[1]; if (par && /Variable/.test(b.cls)) k = par + '.' + k; }
  const ce = (b.body.match(/CustomFunctionName="([^"]+)"/) || [])[1]; const tt = (b.body.match(/TargetType="[^"]*\.(\w+)'"/) || [])[1];
  return b.cls + (k ? ':' + k : '') + (ce ? ':' + ce : '') + (tt ? '<' + tt + '>' : ''); };
const isExec = b => pins(b).some(p => p.exec);
const expr = (n, d = 0) => { const b = by[n]; if (!b) return n; if (isExec(b) || d > 4) return n + '#'; const ins = pins(b).filter(p => !p.out && !p.hidden && p.name !== 'self' || (p.name === 'self' && p.links.length)); const a = ins.map(p => p.links.length ? p.links.map(l => expr(l, d + 1)).join('+') : (p.dv ?? p.ao ?? '')).filter(x => x !== ''); const l = label(b).replace(/^(VariableGet|CallFunction|PromotableOperator|CommutativeAssociativeBinaryOperator):/, ''); return a.length ? l + '(' + a.join(',') + ')' : l; };
const events = () => Object.values(by).filter(b => /^(Event|CustomEvent|ComponentBoundEvent|InputAction|InputKey|EnhancedInputAction)$/.test(b.cls));
const arg = process.argv[3]; const max = +(process.argv[4] || 400);
if (!arg) { for (const e of events()) console.log(e.name, label(e), e.graph); process.exit(); }
const start = by[arg] ? arg : (events().find(e => label(e).endsWith(':' + arg)) || {}).name; if (!start) { console.log('not found', arg); process.exit(1); }
const seen = new Set(); let count = 0;
const walk = (n, ind) => { const b = by[n]; if (!b) return; if (seen.has(n)) { console.log(ind + '^' + n); return; } seen.add(n); if (++count > max) return;
  const ps = pins(b); const ins = ps.filter(p => !p.out && !p.exec && !p.hidden && (p.links.length || (p.dv && p.dv !== 'false' && p.dv !== '0' && p.dv !== '0.0' && p.dv !== '0, 0, 0')) || (!p.out && p.name === 'self' && p.links.length));
  console.log(ind + n + ' ' + label(b) + (ins.length ? ' {' + ins.map(p => p.name + '=' + (p.links.length ? p.links.map(l => expr(l)).join('+') : p.dv)).join('; ') + '}' : ''));
  const ex = ps.filter(p => p.out && p.exec); for (const p of ex) { if (ex.length > 1) { if (p.links.length) console.log(ind + ' [' + p.name + ']'); } for (const l of p.links) walk(l, ind + (ex.length > 1 ? '   ' : '')); } };
walk(start, '');
