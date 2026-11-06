# Weapons at Vesna (audit seat, 2026-11-06): re-import TGA's 5 AAA FBX at import scale 0.01 so they match the live CK kit, which was
# imported from metre files as centimetres (live meshes are ~1 cm long; the hero's kit component carries the x100). Same folder, same names,
# the MI_CK_<Name>_AAA material is re-assigned, so step A's textures and MIs stay. Safe to re-run.
#   py "<repo>/handoffs/weapons-vensa-1106/reimport_aaa_scale_ue.py"             dry run: prints live vs AAA full bounds, imports nothing
#   py ".../reimport_aaa_scale_ue.py" --apply                                      re-imports the 5 meshes at 0.01, saves, prints bounds again
# Then re-run swap_aaa_weapons_ue.py (dry, --apply). Syntax-checked only, never run in UE.
import os, sys, unreal

SRC = r'C:\Users\hossa\Documents\agent-office\assets\tga\WeaponsAAA'
ROOT, LIVE = '/Game/CastleDefender/Weapons/CK_AAA', '/Game/CastleDefender/Weapons/CK'
NAMES = ['ArmingSword', 'Longsword', 'WarAxe', 'FlangedMace', 'Halberd']
SCALE = 0.01
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
apply = '--apply' in sys.argv
log = ['reimport AAA at scale %s: %s' % (SCALE, 'APPLY' if apply else 'dry run')]

def box(path):
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else None
    if not m: return 'MISSING'
    b = m.get_bounding_box()
    return 'x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f cm' % (b.min.x, b.max.x, b.min.y, b.max.y, b.min.z, b.max.z)

def fbx_ui():
    fbx = unreal.FbxImportUI()
    fbx.import_mesh = True; fbx.import_as_skeletal = False; fbx.import_materials = False; fbx.import_textures = False
    d = fbx.static_mesh_import_data
    d.combine_meshes = True; d.generate_lightmap_u_vs = True
    d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    d.import_uniform_scale = SCALE
    return fbx

for n in NAMES:
    live = '%s/%s/SM_CK_%s' % (LIVE, n, n); aaa = '%s/%s/SM_CK_%s' % (ROOT, n, n)
    log.append('%-12s live %s' % (n, box(live)))
    log.append('%-12s aaa  %s' % ('', box(aaa)))
    if not apply: continue
    f = os.path.join(SRC, n, 'SM_CK_%s.fbx' % n)
    if not os.path.isfile(f): log.append('   MISSING fbx ' + f); continue
    t = unreal.AssetImportTask()
    t.filename = f; t.destination_path = '%s/%s' % (ROOT, n); t.automated = True; t.save = True; t.replace_existing = True; t.options = fbx_ui()
    tools.import_asset_tasks([t])
    sm = unreal.load_asset(aaa)
    mi = '%s/%s/MI_CK_%s_AAA' % (ROOT, n, n)
    if sm and EAL.does_asset_exist(mi): sm.set_material(0, unreal.load_asset(mi)); EAL.save_loaded_asset(sm)
    log.append('%-12s re-imported at %s -> %s' % ('', SCALE, box(aaa)))
log.append('rule: after --apply every AAA box must match the live box within ~0.02 cm on all three axes (same pivot, same length); then swap_aaa_weapons_ue.py.')
out = '\n'.join(log); open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reimport_aaa_scale.txt'), 'w').write(out); unreal.log(out)
