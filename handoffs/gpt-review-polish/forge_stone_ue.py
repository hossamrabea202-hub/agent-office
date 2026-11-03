# #451 forge hearth (i5, 2026-11-03). Forge_01 (BP_Forge, SM_Camp_Forge + MI_Camp_Forge on M_LP2Weapon) renders as white
# plastic blocks (shots/forgelit_A.png): the mesh only has a lightmap-style UV set, so the forge texture doesn't land.
# A real smithy hearth is dressed stone / brick like the walls around it. Per-INSTANCE override on this one placed actor:
# the hearth component gets the castle's world-aligned stone (MI_Castle_Trim_World), so it matches the wall it stands at.
# No shared asset is edited (MI_Camp_Forge / SM_Camp_Forge / BP_Forge untouched). Does not save the map.
#   py forge_stone_ue.py --dry-run | --apply | --revert       (backup forge_stone_backup.json)
import json, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]
BK = H + 'forge_stone_backup.json'
STONE = '/Game/CastleDefender/Shared/Materials/Castle/MI_Castle_Trim_World'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
done = []
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() != 'BP_Forge_C': continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if not m or m.get_name() != 'SM_Camp_Forge': continue
        key = a.get_path_name() + '|' + c.get_name()
        if '--revert' in A:
            bk = json.load(open(BK)); old = bk.get(key)
            if old: a.modify(); c.set_material(0, unreal.load_asset(old)); done.append('reverted ' + a.get_actor_label())
            continue
        done.append('%s %s.%s: %s -> MI_Castle_Trim_World' % ('APPLY' if '--apply' in A else 'WOULD', a.get_actor_label(), c.get_name(), c.get_materials()[0].get_name()))
        if '--apply' in A:
            bk = json.load(open(BK)) if os.path.exists(BK) else {}
            bk.setdefault(key, c.get_materials()[0].get_path_name()); json.dump(bk, open(BK, 'w'), indent=0)
            a.modify(); c.set_material(0, unreal.load_asset(STONE))
print('\n'.join(done) or 'no forge found')
