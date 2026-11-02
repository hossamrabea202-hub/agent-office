# #425 step 0 (i5): read-only inventory of wall-mounted props + existing soot cards / decals in the open level.
# Writes inventory.txt next to this script. Changes nothing.
import collections, unreal
KEYS = ('torch', 'sconce', 'sign', 'banner', 'shield', 'lantern', 'lamp', 'bracket', 'soot', 'decal', 'flag', 'plaque', 'hook', 'chain')
out, cnt = [], collections.Counter()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    lab, cls = a.get_actor_label(), a.get_class().get_name()
    meshes = []
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if m: meshes.append(m.get_name())
    if isinstance(a, unreal.DecalActor):
        mat = a.decal.get_editor_property('decal_material'); meshes.append('DECAL:' + (mat.get_name() if mat else '-'))
    hay = (lab + ' ' + cls + ' ' + ' '.join(meshes[:4])).lower()
    k = next((k for k in KEYS if k in hay), None)
    if not k: continue
    cnt[k] += 1
    l = a.get_actor_location(); r = a.get_actor_rotation()
    out.append('%-8s %-40s %-28s %-50s loc=(%.0f,%.0f,%.0f) yaw=%.0f' % (k, lab[:40], cls[:28], ','.join(sorted(set(meshes)))[:50], l.x, l.y, l.z, r.yaw))
open('C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425/inventory.txt', 'w', encoding='utf-8').write('\n'.join(sorted(out)))
print(dict(cnt))
