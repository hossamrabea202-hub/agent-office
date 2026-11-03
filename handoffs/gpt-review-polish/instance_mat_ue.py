# #451 per-INSTANCE material override (i5, 2026-11-03): one placed actor's component gets another existing material;
# no shared asset is edited. For props from the LP2 pipeline whose mesh has only a lightmap-style UV set, so their own
# texture smears or doesn't land (forge hearth, mine entrance rock). Backup per (actor, component, slot); --revert.
#   py instance_mat_ue.py <actor label> <mesh name> <material path> [--slot N] --dry-run | --apply | --revert
import json, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]; label, mesh, matp = A[0], A[1], A[2]
slot = int(A[A.index('--slot') + 1]) if '--slot' in A else 0
BK = H + 'instance_mat_backup.json'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
bk = json.load(open(BK)) if os.path.exists(BK) else {}
out = []
for a in EAS.get_all_level_actors():
    if a.get_actor_label() != label: continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if not m or m.get_name() != mesh: continue
        key = '%s|%s|%d' % (a.get_path_name(), c.get_name(), slot)
        cur = c.get_materials()[slot]
        if '--revert' in A:
            if key in bk: a.modify(); c.set_material(slot, unreal.load_asset(bk.pop(key))); out.append('reverted %s.%s' % (label, c.get_name()))
            continue
        out.append('%s %s.%s slot %d: %s -> %s' % ('APPLY' if '--apply' in A else 'WOULD', label, c.get_name(), slot, cur.get_name() if cur else None, matp.split('/')[-1]))
        if '--apply' in A:
            bk.setdefault(key, cur.get_path_name()); a.modify(); c.set_material(slot, unreal.load_asset(matp))
json.dump(bk, open(BK, 'w'), indent=0)
print('\n'.join(out) or 'no match')
