# #545 i5 assets for BP_TentacleEruption (adjustedfilm, 2026-11-06). Editor idle, not in Play. New assets only, in /Game/CastleDefender/Gameplay/Tentacle/Eruption. Places nothing in the level.
#   py eruption_assets_ue.py --dry-run | (no flag: import and build; re-running replaces the imports) | --revert (deletes this folder's assets)
# AS/AM_Tentacle_Rise (6.5 s), AS/AM_Tentacle_RiseFast (4.2 s); SM_EruptSlab_S|M|L (source for Fracture Mode); SM_EruptDome + M_EruptDome (param Heave 0-1, HeightCm 100);
# T_EruptCrack_* + M_EruptCrack (deferred decal, param Reveal 0-1, opens from the centre along the cracks; animate through a dynamic material instance).
import os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split(); DRY, REV = '--dry-run' in A, '--revert' in A
D_ = '/Game/CastleDefender/Gameplay/Tentacle/Eruption'; RIG = '/Game/CastleDefender/Environment/Tentacles/Rig'; SB = '/Game/CastleDefender/Environment/Tentacles/SporeBase/M_TentacleSporeBase'
EAL, AT, MEL = unreal.EditorAssetLibrary, unreal.AssetToolsHelpers.get_asset_tools(), unreal.MaterialEditingLibrary
def say(*a): print('ERUPT545', ' '.join(str(x) for x in a))
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): raise SystemExit('ERUPT545 stop Play first')
if REV: say('deleted', EAL.delete_directory(D_)); raise SystemExit(0)
files = [os.path.join(HERE, 'fbx', f) for f in ('Tentacle_RISE.fbx', 'Tentacle_RISE_FAST.fbx', 'SM_EruptDome.fbx', 'SM_EruptSlab_S.fbx', 'SM_EruptSlab_M.fbx', 'SM_EruptSlab_L.fbx')] + [os.path.join(HERE, 'tex', 'T_EruptCrack_%s.png' % t) for t in ('BC', 'N', 'ORM', 'Mask')]
missing = [f for f in files if not os.path.exists(f)]
if missing: raise SystemExit('ERUPT545 missing (git pull?): %s' % missing)
if DRY:
    say('would import', len(files), 'files into', D_, '| skeleton', EAL.does_asset_exist(RIG + '/SK_CorruptedTentacle_01_Skeleton'), '| base material', EAL.does_asset_exist(SB)); say('DONE dry-run'); raise SystemExit(0)
skel = unreal.load_asset(RIG + '/SK_CorruptedTentacle_01_Skeleton')
for fbx, nm, mon, bi, bo in (('Tentacle_RISE.fbx', 'AS_Tentacle_Rise', 'AM_Tentacle_Rise', 0.05, 0.8), ('Tentacle_RISE_FAST.fbx', 'AS_Tentacle_RiseFast', 'AM_Tentacle_RiseFast', 0.05, 0.6)):
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_as_skeletal', True); ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME); ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', fbx); t.destination_path = D_; t.destination_name = nm; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; AT.import_asset_tasks([t]); a = unreal.load_asset(D_ + '/' + nm)
    if not a: raise SystemExit('ERUPT545 import failed ' + nm)
    a.set_editor_property('enable_root_motion', False); EAL.save_loaded_asset(a); say(nm, 'frames', unreal.AnimationLibrary.get_num_frames(a), 'len', round(a.get_play_length(), 2))
    if not EAL.does_asset_exist(D_ + '/' + mon):
        f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', a); f.set_editor_property('target_skeleton', skel); m = AT.create_asset(mon, D_, unreal.AnimMontage, f)
        for k, v in (('blend_in', bi), ('blend_out', bo)):
            b = m.get_editor_property(k); b.set_editor_property('blend_time', v); m.set_editor_property(k, b)
        EAL.save_loaded_asset(m)
for nm in ('SM_EruptDome', 'SM_EruptSlab_S', 'SM_EruptSlab_M', 'SM_EruptSlab_L'):
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_animations', False); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.get_editor_property('static_mesh_import_data'); d.set_editor_property('import_uniform_scale', 0.01); d.set_editor_property('vertex_color_import_option', unreal.VertexColorImportOption.REPLACE); d.set_editor_property('generate_lightmap_u_vs', False); d.set_editor_property('combine_meshes', True); d.set_editor_property('auto_generate_collision', 'Slab' in nm)
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', nm + '.fbx'); t.destination_path = D_; t.destination_name = nm; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; AT.import_asset_tasks([t]); me = unreal.load_asset(D_ + '/' + nm)
    if not me: raise SystemExit('ERUPT545 import failed ' + nm)
    b = me.get_bounds(); say(nm, 'extent cm', round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z))
for nm, srgb, comp in (('BC', True, unreal.TextureCompressionSettings.TC_DEFAULT), ('N', False, unreal.TextureCompressionSettings.TC_NORMALMAP), ('ORM', False, unreal.TextureCompressionSettings.TC_MASKS), ('Mask', False, unreal.TextureCompressionSettings.TC_MASKS)):
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'tex', 'T_EruptCrack_%s.png' % nm); t.destination_path = D_; t.destination_name = 'T_EruptCrack_' + nm; t.automated = True; t.replace_existing = True; t.save = True; AT.import_asset_tasks([t]); tx = unreal.load_asset(D_ + '/T_EruptCrack_' + nm)
    if not tx: raise SystemExit('ERUPT545 import failed T_EruptCrack_' + nm)
    tx.set_editor_property('srgb', srgb); tx.set_editor_property('compression_settings', comp); EAL.save_loaded_asset(tx)
E = MEL.create_material_expression
def scalar(m, n, v, x, y): s = E(m, unreal.MaterialExpressionScalarParameter, x, y); s.set_editor_property('parameter_name', n); s.set_editor_property('default_value', v); return s
def fresh(nm):
    p = D_ + '/' + nm; m = unreal.load_asset(p) if EAL.does_asset_exist(p) else AT.create_asset(nm, D_, unreal.Material, unreal.MaterialFactoryNew()); MEL.delete_all_material_expressions(m); return m
# dome: colours as the spore base; lifted by World Position Offset, weighted by vertex alpha
m = fresh('M_EruptDome'); vc = E(m, unreal.MaterialExpressionVertexColor, -900, -100); pw = E(m, unreal.MaterialExpressionPower, -650, -100); c = E(m, unreal.MaterialExpressionConstant, -850, 40); c.set_editor_property('r', 2.2); MEL.connect_material_expressions(vc, '', pw, 'Base'); MEL.connect_material_expressions(c, '', pw, 'Exponent'); MEL.connect_material_property(pw, '', unreal.MaterialProperty.MP_BASE_COLOR)
ro = E(m, unreal.MaterialExpressionConstant, -300, 60); ro.set_editor_property('r', 0.92); MEL.connect_material_property(ro, '', unreal.MaterialProperty.MP_ROUGHNESS)
h1 = scalar(m, 'Heave', 0.0, -900, 250); h2 = scalar(m, 'HeightCm', 100.0, -900, 370); mu1 = E(m, unreal.MaterialExpressionMultiply, -650, 300); MEL.connect_material_expressions(h1, '', mu1, 'A'); MEL.connect_material_expressions(h2, '', mu1, 'B'); mu2 = E(m, unreal.MaterialExpressionMultiply, -450, 250); MEL.connect_material_expressions(vc, 'A', mu2, 'A'); MEL.connect_material_expressions(mu1, '', mu2, 'B')
up = E(m, unreal.MaterialExpressionConstant3Vector, -450, 420); up.set_editor_property('constant', unreal.LinearColor(0, 0, 1, 1)); wp = E(m, unreal.MaterialExpressionMultiply, -250, 300); MEL.connect_material_expressions(up, '', wp, 'A'); MEL.connect_material_expressions(mu2, '', wp, 'B')
say('dome WPO link', MEL.connect_material_property(wp, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)); MEL.recompile_material(m); EAL.save_loaded_asset(m); dm = unreal.load_asset(D_ + '/SM_EruptDome'); dm.set_material(0, m); EAL.save_loaded_asset(dm)
# crack decal
m = fresh('M_EruptCrack'); m.set_editor_property('material_domain', unreal.MaterialDomain.MD_DEFERRED_DECAL); m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
def tex(n, x, y, t=None):
    s = E(m, unreal.MaterialExpressionTextureSample, x, y); s.set_editor_property('texture', unreal.load_asset(D_ + '/T_EruptCrack_' + n)); s.set_editor_property('sampler_type', t or unreal.MaterialSamplerType.SAMPLERTYPE_COLOR); return s
bc = tex('BC', -500, -300); MEL.connect_material_property(bc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR); nr = tex('N', -500, -60, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL); MEL.connect_material_property(nr, 'RGB', unreal.MaterialProperty.MP_NORMAL); orm = tex('ORM', -500, 180, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS); MEL.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS); mk = tex('Mask', -900, 420, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
rv = scalar(m, 'Reveal', 0.0, -900, 660); sf = scalar(m, 'RevealSoft', 0.04, -700, 760); su = E(m, unreal.MaterialExpressionSubtract, -650, 620); MEL.connect_material_expressions(rv, '', su, 'A'); MEL.connect_material_expressions(mk, 'G', su, 'B'); dv = E(m, unreal.MaterialExpressionDivide, -480, 660); MEL.connect_material_expressions(su, '', dv, 'A'); MEL.connect_material_expressions(sf, '', dv, 'B'); sa = E(m, unreal.MaterialExpressionSaturate, -320, 660); MEL.connect_material_expressions(dv, '', sa, ''); op = E(m, unreal.MaterialExpressionMultiply, -180, 520); MEL.connect_material_expressions(mk, 'R', op, 'A'); MEL.connect_material_expressions(sa, '', op, 'B')
MEL.connect_material_property(op, '', unreal.MaterialProperty.MP_OPACITY); MEL.recompile_material(m); EAL.save_loaded_asset(m)
if EAL.does_asset_exist(SB):
    for nm in ('SM_EruptSlab_S', 'SM_EruptSlab_M', 'SM_EruptSlab_L'):
        s = unreal.load_asset(D_ + '/' + nm); s.set_material(0, unreal.load_asset(SB)); EAL.save_loaded_asset(s)
else: say('note: M_TentacleSporeBase missing, slabs keep the default material until sporebase_ue.py has run')
say('assets', sorted(a.rsplit('/', 1)[1].split('.')[0] for a in EAL.list_assets(D_, False))); say('DONE')
