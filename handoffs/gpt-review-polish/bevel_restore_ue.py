# #451 bevel restore (i5, 2026-11-03). The castle's "Restored/SM_Bevel_NNN" actors are stand-ins: plain SM_Cube_Nanite boxes
# (razor-sharp 90 deg edges, the "cube faces" the owner sees) put where the original bevelled meshes SM_Bevel_NNN were.
# Real dressed stone never has a CG-sharp arris: masons chamfer it and weather rounds it (RESEARCH_seams.md). Many of the
# original meshes still exist in /Game/CastleDefender/Environment/Castle/Beveled/. This puts each one back on its stand-in
# at the SAME world size, position and rotation, with the stand-in's material on every slot (castle materials are
# world-aligned, so the stone pattern doesn't move). Size check: if the bevel mesh's proportions differ from the box by
# more than MAXSKEW the bevel would be stretched, so that actor is skipped and reported. Decals untouched. Does NOT save.
#   py bevel_restore_ue.py [--only SM_Bevel_023,...] --dry-run | --apply | --revert          (backup bevel_restore_backup.json)
import json, os, re, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]
BK = H + 'bevel_restore_backup.json'
BEV = '/Game/CastleDefender/Environment/Castle/Beveled/'
CUBE = 'SM_Cube_Nanite'
ONLY = A[A.index('--only') + 1].split(',') if '--only' in A else None   # e.g. --only SM_Bevel_023
MAXSKEW = 4.0          # max ratio between the per-axis scales needed (1 = the bevel mesh was authored at this size)
EAS, EAL = unreal.get_editor_subsystem(unreal.EditorActorSubsystem), unreal.EditorAssetLibrary
acts = EAS.get_all_level_actors()
by_path = {a.get_path_name(): a for a in acts}
if '--revert' in A:
    for path, b in json.load(open(BK)).items():
        a = by_path.get(path)
        if not a: print('missing', path); continue
        c = a.static_mesh_component; a.modify()
        c.set_static_mesh(unreal.load_asset(b['mesh']))
        for i, m in enumerate(b['mats']): c.set_material(i, unreal.load_asset(m) if m else None)
        if 'rot' in b: a.set_actor_rotation(unreal.Rotator(*b['rot']), False)
        a.set_actor_scale3d(unreal.Vector(*b['scale'])); a.set_actor_location(unreal.Vector(*b['loc']), False, False)
        print('reverted', b['label'])
    raise SystemExit
cache, log, stats = {}, [], {}
DIMS = json.load(open(H + 'bevel_dims.json'))          # bevel mesh name -> [x, y, z] size (cm), from the Beveled folder
backup = json.load(open(BK)) if os.path.exists(BK) and '--apply' in A else {}
for a in acts:
    if a.get_class().get_name() != 'StaticMeshActor': continue
    folder = str(a.get_folder_path()); lab = a.get_actor_label()
    m = re.search(r'Restored/(SM_Bevel_\d+)', folder) or re.match(r'(SM_Bevel_\d+)_\d+$', lab)
    if not m: continue
    c = a.static_mesh_component; cur = c.get_editor_property('static_mesh')
    if not cur or cur.get_name() != CUBE: continue
    name = m.group(1); path = BEV + name
    if ONLY and name not in ONLY: continue
    if name not in cache: cache[name] = unreal.load_asset(path) if EAL.does_asset_exist(path) else None
    bm, turn = cache[name], 0
    st = stats.setdefault(name, [0, 0, 0])            # restored, missing mesh, skewed
    cb = cur.get_bounding_box(); s = c.get_world_scale()
    dims = [(cb.max.x - cb.min.x) * abs(s.x), (cb.max.y - cb.min.y) * abs(s.y), (cb.max.z - cb.min.z) * abs(s.z)]
    if not bm:
        # the original is gone: use another bevel mesh authored at the same size turned 90 deg (x/y swapped), e.g.
        # SM_Bevel_024 (90x95x160) = SM_Bevel_023 (95x90x160) turned, SM_Bevel_007 (245x120x540) = SM_Bevel_013 turned
        for alt, d in DIMS.items():
            if abs(d[0] - dims[1]) < 1.0 and abs(d[1] - dims[0]) < 1.0 and abs(d[2] - dims[2]) < 1.0:
                bm, turn = unreal.load_asset(BEV + alt), 90; break
        if not bm: st[1] += 1; continue
        dims = [dims[1], dims[0], dims[2]]
    bb = bm.get_bounding_box()
    bd = [bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z]
    if min(bd) < 0.01: st[2] += 1; continue
    if min(s.x, s.y, s.z) < 0: st[2] += 1; continue                                      # mirrored stand-ins: leave alone
    ns = [dims[i] / bd[i] for i in range(3)]
    skew = max(abs(x) for x in ns) / max(1e-6, min(abs(x) for x in ns))
    if skew > MAXSKEW:
        st[2] += 1; log.append('SKEW   %-22s %-16s dims %s vs mesh %s (scales %s)' % (lab, name, [round(x) for x in dims], [round(x) for x in bd], [round(x, 2) for x in ns])); continue
    # same world centre: cube pivot is its centre; bevel mesh centre may be off its pivot
    t = c.get_world_transform(); r0 = t.rotation.rotator()
    if turn and (abs(r0.roll) > 0.5 or abs(r0.pitch) > 0.5): st[2] += 1; continue      # only level pieces are turned
    r = unreal.Rotator(r0.roll, r0.pitch, r0.yaw + turn)
    cen = unreal.MathLibrary.transform_location(t, unreal.Vector((cb.min.x + cb.max.x) / 2, (cb.min.y + cb.max.y) / 2, (cb.min.z + cb.max.z) / 2))
    bc = unreal.Vector((bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2, (bb.min.z + bb.max.z) / 2)
    off = unreal.MathLibrary.transform_direction(unreal.Transform(unreal.Vector(0, 0, 0), r, unreal.Vector(*ns)), bc)
    mats = [x.get_path_name() if x else '' for x in c.get_materials()]
    st[0] += 1
    if '--apply' in A:
        l0, s0, q0 = a.get_actor_location(), a.get_actor_scale3d(), a.get_actor_rotation()
        backup.setdefault(a.get_path_name(), {'label': lab, 'mesh': cur.get_path_name(), 'mats': mats, 'loc': [l0.x, l0.y, l0.z],
                                              'scale': [s0.x, s0.y, s0.z], 'rot': [q0.roll, q0.pitch, q0.yaw]})
        a.modify(); c.set_static_mesh(bm)
        mat0 = unreal.load_asset(mats[0]) if mats and mats[0] else None
        for i in range(len(bm.static_materials)): c.set_material(i, mat0)
        if turn: a.set_actor_rotation(r, False)
        a.set_actor_scale3d(unreal.Vector(*ns)); a.set_actor_location(cen - off, False, False)
    if turn: log.append('TURNED %-22s %s -> %s +90 deg' % (lab, name, bm.get_name()))
for name, (ok, miss, sk) in sorted(stats.items()):
    log.append('%-14s restore %3d   no mesh %3d   skewed %3d' % (name, ok, miss, sk))
tot = [sum(v[i] for v in stats.values()) for i in range(3)]
if '--apply' in A: json.dump(backup, open(BK, 'w'), indent=0)
out = '\n'.join(log) + '\n%s: %d stand-ins %s, %d have no bevel mesh left, %d skipped (bevel would stretch)' % (
    'APPLIED' if '--apply' in A else 'DRY RUN', tot[0], 'restored' if '--apply' in A else 'can be restored', tot[1], tot[2])
open(H + 'bevel_restore_log.txt', 'w', encoding='utf-8').write(out)
print(out)
