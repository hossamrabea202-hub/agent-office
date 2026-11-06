import unreal, collections
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); C = collections.Counter(); ex = {}
for a in eas.get_all_level_actors():
    if not isinstance(a, unreal.StaticMeshActor): continue
    c = a.static_mesh_component; m = c.static_mesh
    if not m: continue
    s = a.get_actor_scale3d(); r = max(s.x, s.y, s.z) / max(0.001, min(s.x, s.y, s.z))
    if r < 3: continue
    mats = ','.join(sorted(set((c.get_material(i).get_name() if c.get_material(i) else 'None') for i in range(c.get_num_materials()))))
    if any(k in mats.lower() for k in ('decal', 'grime', 'soot', 'moss', 'dust', 'weather')): continue
    k = (m.get_name(), mats); C[k] += 1; ex.setdefault(k, (a.get_actor_label(), str(a.get_folder_path()), '%.1f,%.1f,%.1f' % (s.x, s.y, s.z)))
L = ['%4d  %s | %s | e.g. %s' % (n, k[0], k[1], ex[k]) for k, n in C.most_common(40)]
open(r'C:\Users\hossa\Documents\agent-office\_overhang_diag.txt', 'w').write('\n'.join(L)); print('OHD')
