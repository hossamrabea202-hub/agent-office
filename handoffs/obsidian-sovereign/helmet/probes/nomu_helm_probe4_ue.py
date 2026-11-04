# Read-only (#485): how close does the rest of the worn set come to the helm's rim? Cuirass + shoulders near the neck.
import unreal
R = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign'
for p in (R + '/Chest/SK_ObsidianSovereign_Chest', R + '/Chest/SK_Knight_ChestRemnant'):
    m = unreal.load_asset(p); b = m.get_bounds()
    print(p.rsplit('/', 1)[1], 'bounds z', round(b.origin.z - b.box_extent.z, 1), round(b.origin.z + b.box_extent.z, 1), 'x +-', round(b.box_extent.x, 1), 'y', round(b.origin.y - b.box_extent.y, 1), round(b.origin.y + b.box_extent.y, 1))
for p in (R + '/Chest/SM_ObsidianSovereign_Chest', R + '/Shoulders/SM_ObsidianSovereign_Shoulders_L', R + '/Shoulders/SM_ObsidianSovereign_Shoulders_R'):
    m = unreal.load_asset(p); d = m.get_static_mesh_description(0); n = d.get_vertex_count()
    best = {}
    for i in range(n):
        q = d.get_vertex_position(unreal.VertexID(i))
        if q.z > 140:
            k = int(q.z // 2 * 2); e = best.setdefault(k, [q.x, q.x, q.y, q.y])
            e[0] = min(e[0], q.x); e[1] = max(e[1], q.x); e[2] = min(e[2], q.y); e[3] = max(e[3], q.y)
    print(p.rsplit('/', 1)[1], 'verts', n, {k: [round(v, 1) for v in best[k]] for k in sorted(best)})
