# #301/#447 masonry stairs in UE (i5, 2026-11-03).
#   py stair_mason_ue.py import [13 20 31]                          import out/SM_StairMason451_N*.fbx as NEW assets (no Nanite, UCX
#                                                                   collision, both slots MI_CastleAshlar, the keep)
#   py stair_mason_ue.py swap [--only Stair279_03,...] --dry-run | --apply | --revert
#       every placed kit flight SM_Stair_W200_Solid_N<n> -> SM_StairMason451_N<n> (same footprint and pivot, actor scale kept,
#       its material overrides set to the ashlar MIs). Backup stair_mason_backup.json. The kit meshes are not edited.
import json, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/stairs-masonry/'
A = sys.argv[1:]; mode = A[0]
DST = '/Game/CastleDefender/Props/StairMason451'
TREAD = '/Game/CastleDefender/Environment/Castle/KeepMasonry/MI_CastleAshlar'   # the keep's own stone (owner: like the keep)
WALL = '/Game/CastleDefender/Environment/Castle/KeepMasonry/MI_CastleAshlar'
BK = H + 'stair_mason_backup.json'
EAL = unreal.EditorAssetLibrary
if mode == 'import':
    for n in [int(x) for x in A[1:]] or [13, 20, 31]:
        t = unreal.AssetImportTask(); t.filename = H + 'out/SM_StairMason451_N%d.fbx' % n; t.destination_path = DST
        t.automated = True; t.replace_existing = True; t.save = False
        o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
        d = o.static_mesh_import_data; d.combine_meshes = True; d.auto_generate_collision = False; d.generate_lightmap_u_vs = False
        d.import_mesh_lo_ds = False; d.build_nanite = False; t.options = o      # ~5k faces: no Nanite needed
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        p = DST + '/SM_StairMason451_N%d' % n; m = unreal.load_asset(p)
        m.set_material(0, unreal.load_asset(TREAD)); m.set_material(1, unreal.load_asset(WALL))
        b = m.get_bounding_box(); EAL.save_asset(p)
        print('imported', p, 'bbox', [round(v, 1) for v in (b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z)],
              'slots', [s.material_interface.get_name() if s.material_interface else None for s in m.static_materials])
    raise SystemExit
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
only = A[A.index('--only') + 1].split(',') if '--only' in A else None
acts = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
if '--revert' in A:
    for path, b in json.load(open(BK)).items():
        a = acts.get(path)
        if not a or (only and a.get_actor_label() not in only): continue
        c = a.static_mesh_component; a.modify(); c.set_static_mesh(unreal.load_asset(b['mesh']))
        for i, m in enumerate(b['mats']): c.set_material(i, unreal.load_asset(m) if m else None)
        print('reverted', b['label'])
    raise SystemExit
bk = json.load(open(BK)) if os.path.exists(BK) else {}
n_done = 0
for a in acts.values():
    if a.get_class().get_name() != 'StaticMeshActor': continue
    c = a.static_mesh_component; m = c.get_editor_property('static_mesh')
    if not m or not m.get_name().startswith('SM_Stair_W200_Solid_N'): continue
    if only and a.get_actor_label() not in only: continue
    n = m.get_name().split('_N')[-1]; newp = DST + '/SM_StairMason451_N' + n
    if not EAL.does_asset_exist(newp): print('SKIP no mesh', newp, a.get_actor_label()); continue
    print('%s %s: %s -> SM_StairMason451_N%s' % ('SWAP' if '--apply' in A else 'WOULD', a.get_actor_label(), m.get_name(), n))
    if '--apply' in A:
        bk.setdefault(a.get_path_name(), {'label': a.get_actor_label(), 'mesh': m.get_path_name(), 'mats': [x.get_path_name() if x else '' for x in c.get_materials()]})
        a.modify(); c.set_static_mesh(unreal.load_asset(newp))
        c.set_material(0, unreal.load_asset(TREAD)); c.set_material(1, unreal.load_asset(WALL))
    n_done += 1
if '--apply' in A: json.dump(bk, open(BK, 'w'), indent=0)
print('%s: %d flights' % ('APPLIED' if '--apply' in A else 'DRY RUN', n_done))
