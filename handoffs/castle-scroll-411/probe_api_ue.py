# Read-only probe of the UE 5.8 Python graph API (i5, #411).
import unreal
out = []
for c in ('BlueprintGraphPinLibrary', 'BlueprintEditorLibrary', 'EdGraph', 'EdGraphNode', 'K2Node', 'EdGraphPin'):
    k = getattr(unreal, c, None)
    out.append('%s: %s' % (c, None if k is None else [m for m in dir(k) if not m.startswith('_')][:200]))
bp = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit')
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
out.append('graph %s props %s' % (g, [m for m in dir(g) if not m.startswith('_')]))
open('C:/Users/hossam.rabea/agent-office/handoffs/castle-scroll-411/probe_api.txt', 'w').write('\n\n'.join(out))
unreal.log('i5 probe done')
