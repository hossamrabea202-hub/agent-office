# #402 destrier + tack, #403 cavalry knight kit (checkking (Claude), 2026-11-01): import into UE 5.3.
# Original procedural work (source/). Run in the editor:
#   py "<repo>/assets/checkking/Cavalry/import_cavalry_ue.py" --dry-run      (checks the files, prints the plan, writes nothing)
#   py "<repo>/assets/checkking/Cavalry/import_cavalry_ue.py"                (imports; re-running re-imports the same files)
# Creates ONLY new assets under /Game/CastleDefender/Characters/Cavalry (nothing existing is touched):
#   SK_Destrier (+ _Skeleton, _PhysicsAsset) with 6 anims A_Destrier_Idle / _Walk / _Trot / _Gallop (lance couched) /
#     _Rear (forehooves strike on frame 22) / _Death; slots M_DestrierCoat, M_DestrierTail, M_DestrierMane
#   SK_Destrier_Tack, SK_Destrier_Lance, SK_Destrier_RiderLegs on the SAME skeleton (use SetLeaderPoseComponent in the BP)
#   M_CavalryPBR (BC / ORM / N + Wetness) -> MI_Destrier_Bay / _Grey / _Black, MI_DestrierTack, MI_Lance, MI_RiderLegs
#   M_DestrierHair (masked, two-sided) -> MI_DestrierHair_Bay / _Grey / _Black;  M_CavalryInvisible (hides the mane under
#   the neck cover: set slot M_DestrierMane to it on barded horses)
# Bones the Blueprint uses: 'RiderSocket' (the knight's upper body attaches here, legs hidden: the RiderLegs mesh gives him
# legs in the stirrups), 'lance' (already drives SK_Destrier_Lance), 'head', 'spine_01'.
import os, sys
import unreal

DRY = '--dry-run' in sys.argv
try: SRC = os.path.dirname(os.path.abspath(__file__))
except NameError: SRC = os.path.join(os.environ.get('AGENT_OFFICE', r'C:\Users\hossam.rabea\agent-office'), r'assets\checkking\Cavalry')
DST = '/Game/CastleDefender/Characters/Cavalry'
SKINS = ('Bay', 'Grey', 'Black')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = lambda m: unreal.log('[Cavalry] ' + ('DRY-RUN ' if DRY else '') + m)
D_, K_ = os.path.join(SRC, 'Destrier'), os.path.join(SRC, 'Knight')
TEX = [(os.path.join(D_, 'textures', 'T_Destrier_%s_%s.png' % (s, k)), k) for s in SKINS for k in ('BC', 'ORM')]
TEX += [(os.path.join(D_, 'textures', 'T_DestrierHair_%s_BCA.png' % s), 'BCA') for s in SKINS]
TEX += [(os.path.join(D_, 'textures', 'T_Destrier_N.png'), 'N')] + [(os.path.join(D_, 'textures', 'T_DestrierTack_%s.png' % k), k) for k in ('BC', 'ORM', 'N')]
TEX += [(os.path.join(K_, 'textures', 'T_%s_%s.png' % (n, k)), k) for n in ('Lance', 'RiderLegs') for k in ('BC', 'ORM', 'N')]
FBX = [os.path.join(D_, 'SK_Destrier.fbx'), os.path.join(D_, 'SK_Destrier_Tack.fbx'), os.path.join(K_, 'SK_Destrier_Lance.fbx'), os.path.join(K_, 'SK_Destrier_RiderLegs.fbx')]
missing = [f for f, _ in TEX if not os.path.isfile(f)] + [f for f in FBX if not os.path.isfile(f)]
if missing: raise RuntimeError('[Cavalry] missing files: ' + ', '.join(missing))
log('%d textures + %d FBX found in %s -> %s' % (len(TEX), len(FBX), SRC, DST))
if DRY:
    there = [n for n in ('SK_Destrier', 'SK_Destrier_Tack', 'SK_Destrier_Lance', 'SK_Destrier_RiderLegs', 'M_CavalryPBR', 'M_DestrierHair') if EAL.does_asset_exist(DST + '/' + n)]
    log('already in the project (re-imported / kept): %s' % (there or 'none'))
    log('would import the textures, SK_Destrier (+6 anims, physics asset), then Tack / Lance / RiderLegs on SK_Destrier_Skeleton, build 3 materials + 11 instances and assign slots')

def task(path, opts=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
def tex_name(f): return os.path.splitext(os.path.basename(f))[0]
def fbx_ui(skeletal_skeleton=None, anims=False, physics=False):
    f = unreal.FbxImportUI()
    f.import_mesh = True; f.import_as_skeletal = True; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    f.import_materials = False; f.import_textures = False; f.import_animations = anims; f.create_physics_asset = physics
    if skeletal_skeleton: f.skeleton = skeletal_skeleton
    f.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return f

def build_pbr():
    path = DST + '/M_CavalryPBR'
    if EAL.does_asset_exist(path): return path
    m = tools.create_asset('M_CavalryPBR', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None, default=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        if default is not None: e.set_editor_property('default_value', default)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -1000, -250, DST + '/T_DestrierTack_BC')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -1000, 150, DST + '/T_DestrierTack_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -1000, 500, DST + '/T_DestrierTack_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1000, 380, default=0.0)
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, -180)
    MEL.connect_material_expressions(bc, 'RGB', half, 'A'); half.set_editor_property('const_b', 0.6)        # rain-soaked hair / wool / leather darken
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -400, -260)
    MEL.connect_material_expressions(bc, 'RGB', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -400, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.3); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    m.set_editor_property('used_with_skeletal_mesh', True)
    MEL.recompile_material(m); EAL.save_asset(path); return path
def build_hair():
    path = DST + '/M_DestrierHair'
    if EAL.does_asset_exist(path): return path
    m = tools.create_asset('M_DestrierHair', DST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED); m.set_editor_property('two_sided', True)
    t = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
    t.set_editor_property('parameter_name', 'HairBCA'); t.set_editor_property('texture', unreal.load_asset(DST + '/T_DestrierHair_Bay_BCA'))
    r = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 300); r.set_editor_property('parameter_name', 'Roughness'); r.set_editor_property('default_value', 0.45)
    MEL.connect_material_property(t, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(t, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
    m.set_editor_property('used_with_skeletal_mesh', True); MEL.recompile_material(m); EAL.save_asset(path); return path
def build_invisible():
    path = DST + '/M_CavalryInvisible'
    if EAL.does_asset_exist(path): return path
    m = tools.create_asset('M_CavalryInvisible', DST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 0); c.set_editor_property('r', 0.0)
    MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    m.set_editor_property('used_with_skeletal_mesh', True); MEL.recompile_material(m); EAL.save_asset(path); return path
def mi(name, parent, params):
    path = DST + '/' + name
    inst = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, unreal.load_asset(parent))
    for k, v in params.items(): MEL.set_material_instance_texture_parameter_value(inst, k, unreal.load_asset(DST + '/' + v))
    EAL.save_asset(path); return inst
def set_slots(sk_path, by_name):
    sk = unreal.load_asset(sk_path); mats = sk.get_editor_property('materials')
    for sm in mats:
        n = str(sm.get_editor_property('material_slot_name'))
        if n in by_name: sm.set_editor_property('material_interface', by_name[n])
    sk.set_editor_property('materials', mats); EAL.save_loaded_asset(sk)

def main():
    tools.import_asset_tasks([task(f) for f, _ in TEX])
    for f, kind in TEX:
        t = unreal.load_asset(DST + '/' + tex_name(f)); t.modify()
        if kind in ('BC', 'BCA'):
            t.set_editor_property('srgb', True)
            if kind == 'BC': t.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_SHARPEN4)
        elif kind == 'ORM':
            t.set_editor_property('srgb', False); t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
        else:
            t.set_editor_property('srgb', False); t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
            t.set_editor_property('flip_green_channel', False)                      # already DirectX
        EAL.save_loaded_asset(t)
    tools.import_asset_tasks([task(FBX[0], fbx_ui(anims=True, physics=True))])
    for path in EAL.list_assets(DST, recursive=False):                              # FBX takes -> A_Destrier_<Clip>
        name = path.split('.')[-1]
        if 'A_Destrier_' in name and not name.startswith('A_Destrier_'):
            new = DST + '/' + name[name.index('A_Destrier_'):]
            if EAL.does_asset_exist(new): EAL.delete_asset(new)
            EAL.rename_asset(path.split('.')[0], new)
    skel = unreal.load_asset(DST + '/SK_Destrier').get_editor_property('skeleton')
    tools.import_asset_tasks([task(f, fbx_ui(skeletal_skeleton=skel)) for f in FBX[1:]])
    pbr, hair, inv = build_pbr(), build_hair(), build_invisible()
    for s in SKINS:
        mi('MI_Destrier_' + s, pbr, {'BaseColor': 'T_Destrier_%s_BC' % s, 'ORM': 'T_Destrier_%s_ORM' % s, 'Normal': 'T_Destrier_N'})
        mi('MI_DestrierHair_' + s, hair, {'HairBCA': 'T_DestrierHair_%s_BCA' % s})
    tack = mi('MI_DestrierTack', pbr, {'BaseColor': 'T_DestrierTack_BC', 'ORM': 'T_DestrierTack_ORM', 'Normal': 'T_DestrierTack_N'})
    lance = mi('MI_Lance', pbr, {'BaseColor': 'T_Lance_BC', 'ORM': 'T_Lance_ORM', 'Normal': 'T_Lance_N'})
    legs = mi('MI_RiderLegs', pbr, {'BaseColor': 'T_RiderLegs_BC', 'ORM': 'T_RiderLegs_ORM', 'Normal': 'T_RiderLegs_N'})
    set_slots(DST + '/SK_Destrier', {'M_DestrierCoat': unreal.load_asset(DST + '/MI_Destrier_Bay'),
                                     'M_DestrierTail': unreal.load_asset(DST + '/MI_DestrierHair_Bay'), 'M_DestrierMane': unreal.load_asset(DST + '/MI_DestrierHair_Bay')})
    set_slots(DST + '/SK_Destrier_Tack', {'M_DestrierTack': tack})
    set_slots(DST + '/SK_Destrier_Lance', {'M_Lance': lance})
    set_slots(DST + '/SK_Destrier_RiderLegs', {'M_RiderLegs': legs})
    log('done: %s (SK_Destrier + 6 anims, Tack, Lance, RiderLegs). Check: open SK_Destrier, play A_Destrier_Gallop; preview Tack/Lance/RiderLegs on the same skeleton.' % DST)

if not DRY:
    main()
