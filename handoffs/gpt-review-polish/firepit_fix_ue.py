# #451 courtyard fire pit (i5, 2026-11-03). The pit's 9 logs are engine Cylinders (FirePit_Log_00..09, M_FirePitLog):
# smooth uniform CG tubes (shots/firepit_A.png). Real firewood has bark, split faces and cut ends. Fix: hide the 9
# cylinders (never delete) and place SM_FirePitLogs451 (a teepee of 7 split logs + 2 in the embers, built in Blender for this pit,
# bark + end-grain materials) at the pit centre, butts 1 cm into the ember bed. The fire VFX, light, rocks and decals
# are untouched. Tag FIX451_FIREWOOD on the new actor.
#   py firepit_fix_ue.py --dry-run | --apply | --revert       (backup firepit_fix_backup.json)
import json, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]
BK = H + 'firepit_fix_backup.json'
FW = '/Game/CastleDefender/Props/FirePit451/SM_FirePitLogs451'      # built for this pit: blender/campfire_logs451.py
CEN, SCALE, YAW = unreal.Vector(3948, 2603, 3.0), 1.0, 35.0         # ember bed top ~4 cm: log butts sink 1 cm
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = EAS.get_all_level_actors()
logs = [a for a in acts if a.get_actor_label().startswith('FirePit_Log_') and a.get_class().get_name() == 'StaticMeshActor']
new = [a for a in acts if 'FIX451_FIREWOOD' in [str(t) for t in a.tags]]
if '--revert' in A:
    bk = json.load(open(BK)) if os.path.exists(BK) else {}
    for a in logs:
        if a.get_path_name() in bk:
            c = a.static_mesh_component; a.modify(); a.set_actor_hidden_in_game(False); c.set_visibility(True)
            c.set_collision_enabled(getattr(unreal.CollisionEnabled, bk[a.get_path_name()]))
    for a in new: EAS.destroy_actor(a)
    print('reverted: %d logs shown, %d firewood removed' % (len(logs), len(new))); raise SystemExit
print('%s: hide %d cylinder logs, place firewood x%.2f at %s (exists: %d)' % ('APPLY' if '--apply' in A else 'DRY RUN', len(logs), SCALE, CEN, len(new)))
if '--apply' in A:
    bk = json.load(open(BK)) if os.path.exists(BK) else {}
    for a in logs:
        c = a.static_mesh_component
        bk.setdefault(a.get_path_name(), c.get_collision_enabled().name)
        a.modify(); a.set_actor_hidden_in_game(True); c.set_visibility(False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    json.dump(bk, open(BK, 'w'), indent=0)
    if not new:
        m = unreal.load_asset(FW); b = m.get_bounding_box()
        cx, cy = (b.min.x + b.max.x) / 2 * SCALE, (b.min.y + b.max.y) / 2 * SCALE
        r = unreal.Rotator(0, 0, YAW)
        fw = EAS.spawn_actor_from_class(unreal.StaticMeshActor, CEN, r)        # mesh pivot = pit centre on the ground
        fw.static_mesh_component.set_static_mesh(m); fw.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
        fw.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        fw.set_actor_label('FirePit_Firewood451'); fw.tags = [unreal.Name('FIX451_FIREWOOD')]; fw.set_folder_path('CastleArena/Courtyard')
        print('placed', fw.get_actor_label(), fw.get_actor_location())
