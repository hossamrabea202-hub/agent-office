# #488 carved merlon kit: import as NEW assets (i5, 2026-11-04). Places nothing; i9 places.
#   py import_merlon_kit_ue.py --dry-run     checks files, parents, mortar material, names; changes nothing
#   py import_merlon_kit_ue.py --apply       imports fbx/*.fbx (Nanite, complex-as-simple, vertex colours) + MI_CastleMerlon488, saves those assets only
#   py import_merlon_kit_ue.py --revert      deletes exactly what --apply created, refuses if anything still references it
# Aborts in PIE. Manifest of what was created: merlon488_manifest.json next to this script.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/battlements-488'
A = sys.argv[1:]
DST = '/Game/CastleDefender/Environment/Castle/Battlements488'
PARENT = '/Game/CastleDefender/Environment/Castle/KeepMasonry/MI_CastleAshlar'     # the keep's stone: T_vdbhdju, vertex colour contract
MI_NAME, STONE_SLOT, MORTAR_SLOT = 'MI_CastleMerlon488', 'MI_CastleMerlon488', 'M_CastleLimeMortar'
MANIFEST = os.path.join(HERE, 'merlon488_manifest.json')
EAL = unreal.EditorAssetLibrary
report = json.load(open(os.path.join(HERE, 'kit_report.json')))
NAMES = sorted(report)


def find_mortar():
    """i9's matte lime material, by name, wherever it lives."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    hits = [d for d in reg.get_assets_by_path('/Game', True) if str(d.asset_name) == MORTAR_SLOT]
    return str(hits[0].package_name) if hits else None


if '--revert' in A:
    if not os.path.exists(MANIFEST):
        print('nothing to revert: no manifest'); raise SystemExit
    made = json.load(open(MANIFEST)); left = []
    for p in made:                                        # meshes first: they reference the MI
        if not EAL.does_asset_exist(p): continue
        refs = [str(r) for r in EAL.find_package_referencers_for_asset(p, False) if str(r) not in made]
        if refs:
            print('KEEP', p, 'still used by', refs[:5]); left.append(p); continue
        print('delete', p, EAL.delete_asset(p))
    if left: json.dump(left, open(MANIFEST, 'w'), indent=0)
    else: os.remove(MANIFEST)
    print('REVERT done, kept', len(left)); raise SystemExit

parent = unreal.load_asset(PARENT); mortar_path = find_mortar(); bad = []
if not parent: bad.append('parent MI missing: ' + PARENT)
else:
    base = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(parent, 'BaseColor')
    print('stone MI parent', parent.get_name(), '-> BaseColor', base.get_name() if base else None)
    if not base or 'vdbhdju' not in base.get_name(): bad.append('parent BaseColor is not T_vdbhdju')
print('mortar slot', MORTAR_SLOT, '->', mortar_path or 'NOT FOUND in this project: --apply stops here (expected on i5, i9 has it)')
if not mortar_path and '--apply' in A: bad.append(MORTAR_SLOT + ' not found in this project: sync it first')
for n in NAMES:
    f = os.path.join(HERE, 'fbx', n + '.fbx'); p = DST + '/' + n
    if not os.path.exists(f): bad.append('missing ' + f)
    if EAL.does_asset_exist(p): bad.append('already exists, not overwritten: ' + p)
    print('%s %-24s %6d tris  %s' % ('IMPORT' if '--apply' in A else 'WOULD', n, report[n]['tris'], p))
if EAL.does_asset_exist(DST + '/' + MI_NAME): bad.append('already exists: ' + DST + '/' + MI_NAME)
# API check, transient objects only: fails here and not half way through --apply
ui = unreal.FbxImportUI(); d = ui.static_mesh_import_data
d.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE; d.build_nanite = True; d.combine_meshes = True
d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS; d.auto_generate_collision = False; d.generate_lightmap_u_vs = False
print('import options OK; complex as simple flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
if bad:
    print('STOP:'); [print(' ', b) for b in bad]; raise SystemExit
if '--apply' not in A:
    print('DRY RUN: nothing changed (%d meshes + 1 MI would be created in %s)' % (len(NAMES), DST)); raise SystemExit

at = unreal.AssetToolsHelpers.get_asset_tools(); made = []
mi = at.create_asset(MI_NAME, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)      # no overrides: follows i9's live keep stone values
EAL.save_asset(DST + '/' + MI_NAME); made.append(DST + '/' + MI_NAME)
mortar = unreal.load_asset(mortar_path)
for n in NAMES:
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', n + '.fbx'); t.destination_path = DST; t.destination_name = n
    t.automated = True; t.replace_existing = False; t.save = False
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
    s = o.static_mesh_import_data; s.combine_meshes = True; s.auto_generate_collision = False; s.generate_lightmap_u_vs = False; s.import_mesh_lo_ds = False
    s.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE     # R tone, G damp, B cavity
    s.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS; s.build_nanite = True
    t.options = o
    at.import_asset_tasks([t])
    p = DST + '/' + n; m = unreal.load_asset(p)
    if not m:
        print('FAILED', n); continue
    made.append(p); json.dump(made[::-1], open(MANIFEST, 'w'), indent=0)
    slots = m.static_materials
    for i, sl in enumerate(slots):
        m.set_material(i, mortar if str(sl.material_slot_name) == MORTAR_SLOT else mi)
    ns = m.get_editor_property('nanite_settings'); ns.enabled = True
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_nanite_settings(m, ns, apply_changes=True)
    m.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    EAL.save_asset(p)
    b = m.get_bounding_box()
    print('imported', n, 'bbox', [round(v, 1) for v in (b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z)],
          'slots', [(str(sl.material_slot_name), sl.material_interface.get_name() if sl.material_interface else None) for sl in m.static_materials],
          'fallback tris', m.get_num_triangles(0))
print('APPLIED: %d assets in %s. Nothing placed. Compare the bboxes with README.md.' % (len(made), DST))
