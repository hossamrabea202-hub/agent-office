# #455 fire pit logs without overlaps (i5, 2026-11-03). NEW asset; the #451 mesh stays for revert. Aborts in PIE.
#   py firepit455_ue.py import                         out/SM_FirePitLogs455.fbx -> /Game/CastleDefender/Props/FirePit451/SM_FirePitLogs455
#                                                      (bark / end-grain materials copied from SM_FirePitLogs451), saved
#   py firepit455_ue.py swap --dry-run | --apply | --revert   the placed actor tagged FIX451_FIREWOOD: mesh 451 <-> 455 (map: Master saves)
import os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]; mode = A[0]
H = next((h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/firepit-455/', 'C:/Users/hossa/Documents/agent-office/handoffs/firepit-455/')
          if os.path.isdir(h)), None)
D = '/Game/CastleDefender/Props/FirePit451/'
OLD, NEW = D + 'SM_FirePitLogs451', D + 'SM_FirePitLogs455'
EAL = unreal.EditorAssetLibrary
if mode == 'import':
    t = unreal.AssetImportTask(); t.filename = H + 'out/SM_FirePitLogs455.fbx'; t.destination_path = D[:-1]; t.automated = True; t.replace_existing = True; t.save = False
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
    o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.auto_generate_collision = False
    o.static_mesh_import_data.generate_lightmap_u_vs = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    m, old = unreal.load_asset(NEW), unreal.load_asset(OLD)
    for i, s in enumerate(old.static_materials): m.set_material(i, s.material_interface)
    EAL.save_asset(NEW)
    b = m.get_bounding_box()
    print('IMPORT OK', NEW, 'tris', m.get_num_triangles(0), 'mats', [s.material_interface.get_name() for s in m.static_materials],
          'bbox cm', [round(v, 1) for v in (b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z)])
    raise SystemExit
if mode == 'swap':
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if 'FIX451_FIREWOOD' not in [str(t) for t in a.tags]: continue
        c = a.get_component_by_class(unreal.StaticMeshComponent); cur = c.get_editor_property('static_mesh')
        want = unreal.load_asset(OLD if '--revert' in A else NEW)
        print('FIREPIT', a.get_actor_label(), cur.get_name() if cur else None, '->', want.get_name(), [round(v) for v in a.get_actor_location().to_tuple()])
        n += 1
        if '--dry-run' in A: continue
        a.modify(); c.modify(); c.set_static_mesh(want)
        for i, s in enumerate(want.static_materials): c.set_material(i, s.material_interface)    # no stale overrides (#301 lesson)
    print(('would swap ' if '--dry-run' in A else 'swapped ') + str(n))
    raise SystemExit
