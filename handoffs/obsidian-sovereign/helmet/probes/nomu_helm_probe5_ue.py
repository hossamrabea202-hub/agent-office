# Read-only (#485): top of the fitted cuirass (skeletal) by height band: does its collar reach the helm's rim (z 149.6-151.2)?
import unreal
R = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/Chest/SK_ObsidianSovereign_Chest'
m = unreal.load_asset(R)
print([n for n in dir(m) if 'desc' in n.lower() or 'vertex' in n.lower()])
d = None
for f in ('get_mesh_description', 'get_skeletal_mesh_description'):
    if hasattr(m, f):
        try:
            d = getattr(m, f)(0); print('via', f, d); break
        except Exception as e: print(f, 'ERR', e)
if d is None:
    s = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem) if hasattr(unreal, 'SkeletalMeshEditorSubsystem') else None
    print('subsystem', [n for n in dir(s) if 'vert' in n.lower() or 'desc' in n.lower()] if s else None)
else:
    best = {}
    for i in range(d.get_vertex_count()):
        q = d.get_vertex_position(unreal.VertexID(i))
        if q.z > 144:
            k = int(q.z // 2 * 2); e = best.setdefault(k, [q.x, q.x, q.y, q.y])
            e[0] = min(e[0], q.x); e[1] = max(e[1], q.x); e[2] = min(e[2], q.y); e[3] = max(e[3], q.y)
    print({k: [round(v, 1) for v in best[k]] for k in sorted(best)})
