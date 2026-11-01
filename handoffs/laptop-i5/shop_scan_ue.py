# Shop scan (i5 core, 2026-11-01): list the array/default variables of the shop Blueprints' CDOs, read-only.
# Output: Saved/Logs + handoffs/laptop-i5/shop_scan_i5.txt
import unreal
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/laptop-i5/shop_scan_i5.txt'
log = []
for path in ('/Game/CastleDefender/Gameplay/Castle/BP_ArmoryHUD', '/Game/CastleDefender/Gameplay/Castle/BPC_VesnaTrade',
             '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'):
    bp = unreal.load_asset(path)
    cls = unreal.BlueprintEditorLibrary.generated_class(bp)
    cdo = unreal.get_default_object(cls)
    log.append('== %s' % path)
    for p in sorted(dir(cdo)):
        if p.startswith('_'): continue
        try: v = cdo.get_editor_property(p)
        except Exception: continue
        if isinstance(v, (unreal.Array, list)) or isinstance(v, (int, float, str, unreal.Name, unreal.Text)):
            s = str(list(v)[:40]) if isinstance(v, (unreal.Array, list)) else str(v)
            if isinstance(v, (unreal.Array, list)) or any(w in p.lower() for w in ('price', 'cost', 'dmg', 'damage', 'def', 'item', 'weapon', 'shield', 'gold')):
                log.append('  %-28s %s' % (p, s[:600]))
open(OUT, 'w', encoding='utf-8').write('\n'.join(log))
unreal.log('i5 shop scan: %d lines -> %s' % (len(log), OUT))
