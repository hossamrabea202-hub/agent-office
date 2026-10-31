# #277 Crossbow flares, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/flares-277/setup_flares277_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/flares-277/setup_flares277_ue.py"
# Makes under /Game/CastleDefender/Gameplay/Flares:
#   M_FlareCore    unlit emissive, hot magnesium white-orange (the burning core you see in the sky)
#   BP_Flare       actor: root Scene, "Core" sphere 12 cm with M_FlareCore (no collision, no shadow) and "FlareLight"
#                  point light (tag FlareLight): 4500 K, candela units (the graph drives 0 -> 3500 cd), 60 m reach,
#                  10 cm source, casts shadows, volumetric scattering 2 (glows in fog / rain)
#   SFX_Flare_Launch / SFX_Flare_Ignite / SFX_Flare_Burn (loop)   from assets/adjustedfilm/Flares277/sfx
#   BPC_Flares     ActorComponent, added to the hero as "Flares"
# Nothing else is changed (no level, soldier or HUD edit).
import os, sys, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'flares-277')
DRY = '--dry-run' in sys.argv
SFX = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'adjustedfilm', 'Flares277', 'sfx'))
DST = '/Game/CastleDefender/Gameplay/Flares'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, MEL, BEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#277 flares setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


def fresh(name, cls, factory):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path), False
    log.append('create ' + path)
    if DRY: return None, True
    return AT.create_asset(name, DST, cls, factory), True


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add_comp(bp, cls, name):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(bp)[0], new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


# ---- M_FlareCore
m, made = fresh('M_FlareCore', unreal.Material, unreal.MaterialFactoryNew())
if m:
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('shading_model', enum(unreal.MaterialShadingModel, 'MSM_UNLIT'))
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, 0)
    c.set_editor_property('constant', unreal.LinearColor(1.0, 0.82, 0.62, 1.0))
    k = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 200)
    k.set_editor_property('parameter_name', 'Brightness'); k.set_editor_property('default_value', 80.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100)
    MEL.connect_material_expressions(c, '', mul, 'A'); MEL.connect_material_expressions(k, '', mul, 'B')
    MEL.connect_material_property(mul, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(DST + '/M_FlareCore')

# ---- sounds
tasks = []
for n in ('SFX_Flare_Launch', 'SFX_Flare_Ignite', 'SFX_Flare_Burn'):
    f = os.path.join(SFX, n + '.wav')
    if not os.path.exists(f): log.append('MISSING ' + f); continue
    t = unreal.AssetImportTask()
    for kk, v in (('filename', f), ('destination_path', DST), ('destination_name', n), ('replace_existing', True), ('automated', True), ('save', True)):
        t.set_editor_property(kk, v)
    tasks.append(t); log.append('import ' + n)
if tasks and not DRY:
    AT.import_asset_tasks(tasks)
    burn = unreal.load_asset(DST + '/SFX_Flare_Burn')
    if burn: burn.set_editor_property('looping', True); EAL.save_asset(DST + '/SFX_Flare_Burn')


# ---- Blueprints
def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return AT.create_asset(name, DST, unreal.Blueprint, f)


fbp = make_bp('BP_Flare', unreal.Actor)
if fbp:
    core = add_comp(fbp, unreal.StaticMeshComponent, 'Core')
    core.set_editor_property('static_mesh', unreal.load_asset('/Engine/BasicShapes/Sphere'))
    core.set_editor_property('relative_scale3d', unreal.Vector(0.12, 0.12, 0.12))
    if EAL.does_asset_exist(DST + '/M_FlareCore'): core.set_editor_property('override_materials', [unreal.load_asset(DST + '/M_FlareCore')])
    core.set_editor_property('cast_shadow', False); core.set_collision_profile_name('NoCollision')
    L = add_comp(fbp, unreal.PointLightComponent, 'FlareLight')
    L.set_editor_property('component_tags', [unreal.Name('FlareLight')])
    L.set_editor_property('intensity_units', enum(unreal.LightUnits, 'CANDELAS')); L.set_editor_property('intensity', 0.0)
    L.set_editor_property('use_temperature', True); L.set_editor_property('temperature', 4500.0)
    L.set_editor_property('attenuation_radius', 6000.0); L.set_editor_property('source_radius', 10.0)
    L.set_editor_property('cast_shadows', True); L.set_editor_property('volumetric_scattering_intensity', 2.0)
    L.set_editor_property('relative_location', unreal.Vector(0, 0, -20))   # just under the core, so the core itself does not block it
    BEL.compile_blueprint(fbp); EAL.save_asset(DST + '/BP_Flare')
comp = make_bp('BPC_Flares', unreal.ActorComponent)
if comp: BEL.compile_blueprint(comp); EAL.save_asset(DST + '/BPC_Flares')

hero = unreal.load_asset(HERO)
if 'Flares' in names(hero): log.append('hero already has Flares')
else:
    log.append('hero: + Flares (BPC_Flares)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0],
                                                                     new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add Flares: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('Flares'))
        BEL.compile_blueprint(hero); EAL.save_asset(HERO)

out = '\n'.join(log) + '\nNext: README step 3 (BPVar lines on BP_Flare and BPC_Flares, then the two graph pastes).'
if not DRY: open(os.path.join(HERE, 'setup_flares277.txt'), 'w').write(out)
unreal.log(out)
