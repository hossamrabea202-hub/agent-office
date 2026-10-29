# #41 step 1 (laptop2, 2026-10-29): creates the new assets for "Fallen soldiers rise as zombies".
#   /Game/CastleDefender/Gameplay/Castle/BP_RisenDirector                (Actor: fallen list + wave rise + rest notice)
#   /Game/CastleDefender/Characters/Enemies/Zombie/BP_ZombieRisen        (child of BP_Zombie, + KnightMesh component)
#   /Game/CastleDefender/Characters/Enemies/Zombie/Risen/M_RisenOverlay  (overlay material, simple pale fresnel glow)
#   /Game/CastleDefender/Characters/Enemies/Zombie/Risen/MI_RisenOverlay_Boss (Boss = 1: dark purple, commander)
# with all variables and their defaults. Safe to re-run (existing assets/variables/components are reused).
# Run in the editor:  py "<repo>/handoffs/risen-soldiers-41/bp/create_risen41.py"
# Then paste the graphs (README.md steps 2-4). Anything this script cannot do is printed as "MANUAL:" in the log.
import unreal

EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = []

P_DIR = '/Game/CastleDefender/Gameplay/Castle/BP_RisenDirector'
P_ZOMBIE = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
P_RISEN = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_ZombieRisen'
D_FX = '/Game/CastleDefender/Characters/Enemies/Zombie/Risen'
P_OVL, P_OVL_BOSS = D_FX + '/M_RisenOverlay', D_FX + '/MI_RisenOverlay_Boss'
KNIGHT_SK = '/Game/ShadowKight/Mesh/ShadowknightUE_SK'
# KnightMesh materials of BP_SoldierSword (from the 10-28 MANIFEST): slot 2 is the cloth with RankLevel
KNIGHT_MATS = ['/Game/CastleDefender/Characters/Knight/Materials/AAA/MI_Hero_Arms', '/Game/CastleDefender/Characters/Knight/Materials/AAA/MI_Hero_Chest',
               '/Game/CastleDefender/Characters/Knight/Materials/AAA/MI_Hero_Cloth_Crimson', '/Game/CastleDefender/Characters/Knight/Materials/AAA/MI_Hero_HelmetWorn',
               '/Game/CastleDefender/Characters/Knight/Materials/AAA/MI_Hero_Pants']

# name -> (type, default). type: int real bool string | vector | <UClass name> (object ref) ; "[]" = array
VARS_DIRECTOR = {
    'FallenLoc': ('vector[]', None), 'FallenRank': ('real[]', None), 'FallenKind': ('int[]', None),
    'FallenWave': ('int[]', None), 'FallenTime': ('real[]', None), 'FallenCloth': ('MaterialInterface[]', None),
    'NextIdx': ('int', 0), 'LastWave': ('int', 0), 'RiseLeft': ('int', 0), 'MaxPerWave': ('int', 12),
    'InsideMinX': ('real', 0.0), 'InsideMaxX': ('real', 4600.0), 'InsideMinY': ('real', 0.0), 'InsideMaxY': ('real', 3450.0),
    'RescueWindow': ('real', 10.0), 'RescueRadius': ('real', 300.0), 'RiseRadius': ('real', 200.0),
    'BaseHP': ('real', 100.0), 'BaseDamage': ('real', 12.0), 'WalkSpeed': ('real', 110.0),
    'NoticeTime': ('real', 2.4), 'NoticeWidget': ('UserWidget', None),
}
VARS_RISEN = {
    'Rank': ('real', 1.0), 'Kind': ('int', 0), 'ClothMat': ('MaterialInterface', None), 'RankMult': ('real', 1.0),
    'RestTitle': ('string', 'A FALLEN SOLDIER IS AT REST'), 'UseLeaderPose': ('bool', True),
    'RiseTime': ('real', 1.2), 'RiseDepth': ('real', 120.0), 'RiseT0': ('real', 0.0), 'BaseRel': ('vector', None),
    'OverlayMat': ('MaterialInterface', P_OVL), 'OverlayBossMat': ('MaterialInterface', P_OVL_BOSS),
}


def pin_type(t):
    is_arr = t.endswith('[]')
    base = t[:-2] if is_arr else t
    if base in ('int', 'bool', 'string', 'real'):
        pt = BEL.get_basic_type_by_name(base)
        if base == 'real':
            pt.set_editor_property('pin_sub_category', 'double')
    elif base == 'vector':
        pt = BEL.get_struct_type(unreal.Vector.static_struct())
    else:
        pt = BEL.get_object_reference_type(getattr(unreal, base).static_class())
    if is_arr:
        if hasattr(BEL, 'get_array_type'):
            pt = BEL.get_array_type(pt)
        else:
            pt.set_editor_property('container_type', unreal.PinContainerType.ARRAY)
    return pt


def add_vars(bp, vars_):
    have = set()
    try:
        have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
    except Exception:
        pass
    for n, (t, _) in vars_.items():
        if n in have:
            continue
        try:
            if not BEL.add_member_variable(bp, n, pin_type(t)):
                raise RuntimeError('add_member_variable returned False')
            log.append('  + %s (%s)' % (n, t))
        except Exception as e:
            log.append('  MANUAL: add variable %s : %s  (%s)' % (n, t, e))


def set_defaults(bp, vars_):
    cdo = unreal.get_default_object(bp.generated_class())
    for n, (t, v) in vars_.items():
        if v is None:
            continue
        try:
            if isinstance(v, str) and v.startswith('/Game/'):
                v = unreal.load_asset(v)
            cdo.set_editor_property(n, v)
        except Exception as e:
            log.append('  MANUAL: default %s = %s not set (%s); set it in Class Defaults' % (n, v, e))


def make_bp(path, parent_class):
    if EAL.does_asset_exist(path):
        log.append('reusing ' + path)
        return unreal.load_asset(path)
    f = unreal.BlueprintFactory()
    f.set_editor_property('parent_class', parent_class)
    d, n = path.rsplit('/', 1)
    bp = tools.create_asset(n, d, unreal.Blueprint, f)
    log.append('created ' + path)
    return bp


# ---- overlay materials ----
def make_overlay():
    if EAL.does_asset_exist(P_OVL):
        log.append('reusing ' + P_OVL)
        mat = unreal.load_asset(P_OVL)
    else:
        mat = tools.create_asset('M_RisenOverlay', D_FX, unreal.Material, unreal.MaterialFactoryNew())
        try:
            mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
            E = lambda cls, x, y: MEL.create_material_expression(mat, cls, x, y)
            fres = E(unreal.MaterialExpressionFresnel, -700, 0)
            fres.set_editor_property('exponent', 2.5)
            pale = E(unreal.MaterialExpressionVectorParameter, -700, -250)
            pale.set_editor_property('parameter_name', 'PaleTint'); pale.set_editor_property('default_value', unreal.LinearColor(0.55, 0.78, 0.45, 1))
            dark = E(unreal.MaterialExpressionVectorParameter, -700, -450)
            dark.set_editor_property('parameter_name', 'BossTint'); dark.set_editor_property('default_value', unreal.LinearColor(0.35, 0.03, 0.55, 1))
            boss = E(unreal.MaterialExpressionScalarParameter, -700, -600)
            boss.set_editor_property('parameter_name', 'Boss'); boss.set_editor_property('default_value', 0.0)
            glow = E(unreal.MaterialExpressionScalarParameter, -450, 200)
            glow.set_editor_property('parameter_name', 'Glow'); glow.set_editor_property('default_value', 3.0)
            opac = E(unreal.MaterialExpressionScalarParameter, -450, 350)
            opac.set_editor_property('parameter_name', 'Opacity'); opac.set_editor_property('default_value', 0.55)
            lerp = E(unreal.MaterialExpressionLinearInterpolate, -450, -350)
            MEL.connect_material_expressions(pale, '', lerp, 'A'); MEL.connect_material_expressions(dark, '', lerp, 'B')
            MEL.connect_material_expressions(boss, '', lerp, 'Alpha')
            m1 = E(unreal.MaterialExpressionMultiply, -250, -200)
            MEL.connect_material_expressions(lerp, '', m1, 'A'); MEL.connect_material_expressions(fres, '', m1, 'B')
            m2 = E(unreal.MaterialExpressionMultiply, -100, -100)
            MEL.connect_material_expressions(m1, '', m2, 'A'); MEL.connect_material_expressions(glow, '', m2, 'B')
            m3 = E(unreal.MaterialExpressionMultiply, -250, 300)
            MEL.connect_material_expressions(fres, '', m3, 'A'); MEL.connect_material_expressions(opac, '', m3, 'B')
            MEL.connect_material_property(m2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            MEL.connect_material_property(m3, '', unreal.MaterialProperty.MP_OPACITY)
            MEL.recompile_material(mat)
            log.append('created ' + P_OVL + ' (pale fresnel glow; Boss=1 -> dark purple)')
        except Exception as e:
            log.append('  MANUAL: build M_RisenOverlay by hand (translucent unlit, emissive = lerp(PaleTint,BossTint,Boss)*Fresnel*Glow, opacity = Fresnel*Opacity): %s' % e)
        EAL.save_asset(P_OVL)
    if not EAL.does_asset_exist(P_OVL_BOSS):
        mi = tools.create_asset('MI_RisenOverlay_Boss', D_FX, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, mat)
        MEL.set_material_instance_scalar_parameter_value(mi, 'Boss', 1.0)
        EAL.save_asset(P_OVL_BOSS)
        log.append('created ' + P_OVL_BOSS)


# ---- KnightMesh on BP_ZombieRisen, child of the inherited Mesh ----
def add_knight(bp):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    mesh_h, names = None, []
    for h in handles:
        data = sds.k2_find_subobject_data_from_handle(h)
        vn = str(lib.get_variable_name(data))
        names.append(vn)
        if vn in ('KnightMesh',):
            log.append('BP_ZombieRisen already has KnightMesh')
            return
        if vn in ('Mesh', 'CharacterMesh0') and mesh_h is None:
            mesh_h = h
    if mesh_h is None:
        log.append('  MANUAL: inherited Mesh not found (%s); KnightMesh attached to the root instead, re-parent it under Mesh' % names)
        mesh_h = handles[0]
    p = unreal.AddNewSubobjectParams(parent_handle=mesh_h, new_class=unreal.SkeletalMeshComponent, blueprint_context=bp)
    h, fail = sds.add_new_subobject(p)
    if not fail.is_empty():
        log.append('  MANUAL: add SkeletalMeshComponent KnightMesh under Mesh (%s)' % fail)
        return
    sds.rename_subobject(h, unreal.Text('KnightMesh'))
    comp = lib.get_object(sds.k2_find_subobject_data_from_handle(h))
    sk = unreal.load_asset(KNIGHT_SK)
    for prop in ('skeletal_mesh_asset', 'skeletal_mesh'):
        try:
            comp.set_editor_property(prop, sk); break
        except Exception:
            continue
    else:
        log.append('  MANUAL: set KnightMesh Skeletal Mesh = ShadowknightUE_SK')
    try:
        comp.set_editor_property('override_materials', [unreal.load_asset(m) for m in KNIGHT_MATS])
    except Exception as e:
        log.append('  MANUAL: KnightMesh materials 0..4 = MI_Hero_Arms, MI_Hero_Chest, MI_Hero_Cloth_Crimson, MI_Hero_HelmetWorn, MI_Hero_Pants (%s)' % e)
    try:
        comp.set_editor_property('collision_enabled', unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    log.append('BP_ZombieRisen: added KnightMesh (ShadowknightUE_SK) under Mesh')


make_overlay()

director = make_bp(P_DIR, unreal.Actor)
add_vars(director, VARS_DIRECTOR)
BEL.compile_blueprint(director)
set_defaults(director, VARS_DIRECTOR)
EAL.save_asset(P_DIR)

zombie = unreal.load_asset(P_ZOMBIE)
risen = make_bp(P_RISEN, zombie.generated_class())
add_vars(risen, VARS_RISEN)
add_knight(risen)
BEL.compile_blueprint(risen)
set_defaults(risen, VARS_RISEN)
EAL.save_asset(P_RISEN)

unreal.log('#41 Risen soldiers setup:\n' + '\n'.join(log) +
           '\nNext: paste BP_RisenDirector_graph.txt, then BP_ZombieRisen_graph.txt, then the soldier hook (README steps 2-4).')
