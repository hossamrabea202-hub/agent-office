// #472 (i5): performance / logic smell scan of a whole-BP T3D (read-only).
// Per graph: node count; events; what runs on Event Tick (reachable exec chain); expensive calls and where they run.
// Usage: node bp_smells.js <file.t3d.txt> [more files]
const fs = require('fs');
const HOT = ['GetAllActorsOfClass', 'GetAllActorsWithTag', 'GetAllActorsOfClassWithTag', 'GetActorOfClass', 'LineTraceSingle', 'LineTraceMulti',
  'SphereTraceSingle', 'SphereTraceMulti', 'SphereOverlapActors', 'BoxOverlapActors', 'SpawnActor', 'BeginDeferredActorSpawnFromClass',
  'PlayAnimation', 'SetAnimationMode', 'PlayAnimMontage', 'SetMaterial', 'CreateDynamicMaterialInstance', 'SetSkeletalMeshAsset',
  'GetDistanceTo', 'FindLookAtRotation', 'SimpleMoveToActor', 'SimpleMoveToLocation', 'AIMoveTo', 'MoveToActor', 'MoveToLocation',
  'SetTimerbyEvent', 'K2_SetTimer', 'K2_SetTimerDelegate', 'Delay', 'PrintString', 'GetPlayerCharacter', 'GetPlayerPawn', 'Cast'];
for (const f of process.argv.slice(2)) {
  const t = fs.readFileSync(f, 'utf8');
  const blocks = [...t.matchAll(/Begin Object (?:Class=\S+ )?Name="([^"]+)" ExportPath="\/Script\/[A-Za-z]+\.(K2Node_\w+|\w+)'[^"]*:([^.'"]+)\.[^"]*"([\s\S]*?)\n\s*End Object/g)];
  const by = {};
  for (const [, name, cls, graph, body] of blocks) if (body.includes('CustomProperties Pin')) by[name] = { name, cls, graph, body };
  const pins = b => [...b.body.matchAll(/CustomProperties Pin \((.*)\)\s*$/gm)].map(m => m[1]);
  const fn = b => (b.body.match(/FunctionReference=\([^)]*MemberName="([^"]+)"/) || [])[1] || (b.cls === 'K2Node_DynamicCast' ? 'Cast' : b.cls === 'K2Node_SpawnActorFromClass' ? 'SpawnActor' : '');
  const ev = b => (b.body.match(/EventReference=\([^)]*MemberName="([^"]+)"/) || [])[1] || (b.body.match(/CustomFunctionName="([^"]+)"/) || [])[1];
  const execOut = b => pins(b).filter(p => /PinCategory="exec"/.test(p) && /EGPD_Output/.test(p)).flatMap(p => [...((p.match(/LinkedTo=\(([^)]*)\)/) || [, ''])[1]).matchAll(/(\w+) \w+/g)].map(m => m[1]));
  const reach = start => { const seen = new Set([start]); const q = [start]; while (q.length) { const n = q.shift(); const b = by[n]; if (!b) continue; for (const x of execOut(b)) if (!seen.has(x)) { seen.add(x); q.push(x); } } return seen; };
  const graphs = {}; for (const b of Object.values(by)) (graphs[b.graph] = graphs[b.graph] || []).push(b);
  console.log('\n######', f.split(/[\\/]/).pop(), '|', Object.keys(by).length, 'nodes |', Object.entries(graphs).map(([g, v]) => g + ' ' + v.length).join(', '));
  const events = Object.values(by).filter(b => /K2Node_(Event|CustomEvent|ComponentBoundEvent|InputAction|InputKey|EnhancedInputAction)$/.test(b.cls));
  const hotCount = {};
  for (const b of Object.values(by)) { const n = fn(b); if (HOT.includes(n)) hotCount[n] = (hotCount[n] || 0) + 1; }
  console.log('expensive / risky calls (whole BP):', Object.entries(hotCount).sort((a, b) => b[1] - a[1]).map(([k, v]) => k + ' x' + v).join(', '));
  for (const e of events) {
    const name = ev(e) || e.name;
    const r = reach(e.name);
    const hot = {}; for (const n of r) { const b = by[n]; if (!b) continue; const k = fn(b); if (HOT.includes(k)) hot[k] = (hot[k] || 0) + 1; }
    const loops = [...r].filter(n => by[n] && /ForEach|ForLoop|WhileLoop/.test(by[n].body.match(/MacroGraphReference=\([^)]*Graph="[^"]*:(\w+)/)?.[1] || '')).length;
    if (/Tick/i.test(name) || Object.keys(hot).length || loops)
      console.log('  EVENT %s: %d exec nodes, loops %d | %s', (name + (/Tick/i.test(name) ? '  <-- EVERY FRAME' : '')).padEnd(34), r.size, loops, Object.entries(hot).map(([k, v]) => k + ' x' + v).join(', '));
  }
}
