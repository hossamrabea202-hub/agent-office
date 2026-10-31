# #224 Castle upgrades, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/castle-upgrades-224/setup_castle224_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/castle-upgrades-224/setup_castle224_ue.py"
# Makes in /Game/CastleDefender/Gameplay/Castle:
#   BPC_CastleUpgrades  ActorComponent, added to the hero as "CastleUpgrades"
#   BP_TowerBallista    actor from laptop2's FireBallista kit (/Game/CastleDefender/Weapons/FireBallista, #10 - run its
#                       import_kit_ue.py first if missing): Base, Frame (yaws, tag BallistaFrame, pivot 1.42 m), Slider on the
#                       Frame, Spear on the Frame at the muzzle (tag BallistaSpear), Coals point light at the brazier
#                       (tag BallistaCoals, 1900 K, candela, flickers in the graph). No collision on the parts except Base.
#   SFX_Ballista_Shot   (assets/adjustedfilm/Castle224/sfx)
# Nothing else is changed. The level gets BP_TowerBallista only when the Master places them (README step 5).
import os, sys, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'castle-upgrades-224')
DRY = '--dry-run' in sys.argv
SFX = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'adjustedfilm', 'Castle224', 'sfx', 'SFX_Ballista_Shot.wav'))
DST = '/Game/CastleDefender/Gameplay/Castle'
KIT = '/Game/CastleDefender/Weapons/FireBallista/'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#224 castle upgrades setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return AT.create_asset(name, DST, unreal.Blueprint, f)


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add_comp(bp, cls, name, parent=None):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name])), have[name]
    ph = have[parent] if parent else SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=ph, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h)), h


def mesh(n):
    p = KIT + n
    if EAL.does_asset_exist(p): return unreal.load_asset(p)
    log.append('  MISSING %s (run assets/laptop2/FireBallista/import_kit_ue.py)' % p); return None


# ---- sound
if os.path.exists(SFX):
    log.append('import SFX_Ballista_Shot')
    if not DRY:
        t = unreal.AssetImportTask()
        for k, v in (('filename', SFX), ('destination_path', DST), ('destination_name', 'SFX_Ballista_Shot'), ('replace_existing', True), ('automated', True), ('save', True)):
            t.set_editor_property(k, v)
        AT.import_asset_tasks([t])
else:
    log.append('MISSING ' + SFX)

# ---- BP_TowerBallista
tb = make_bp('BP_TowerBallista', unreal.Actor)
if tb:
    for n in ('SM_FireBallista_Base', 'SM_FireBallista_Frame', 'SM_FireBallista_Slider', 'SM_FireBallista_Spear'): mesh(n)
    base, _ = add_comp(tb, unreal.StaticMeshComponent, 'Base')
    m = mesh('SM_FireBallista_Base')
    if m: base.set_editor_property('static_mesh', m)
    frame, _ = add_comp(tb, unreal.StaticMeshComponent, 'Frame')
    frame.set_editor_property('relative_location', unreal.Vector(0, 0, 142)); frame.set_editor_property('component_tags', [unreal.Name('BallistaFrame')])
    m = mesh('SM_FireBallista_Frame')
    if m: frame.set_editor_property('static_mesh', m)
    frame.set_collision_profile_name('NoCollision')
    slider, _ = add_comp(tb, unreal.StaticMeshComponent, 'Slider', 'Frame')
    m = mesh('SM_FireBallista_Slider')
    if m: slider.set_editor_property('static_mesh', m)
    slider.set_collision_profile_name('NoCollision')
    spear, _ = add_comp(tb, unreal.StaticMeshComponent, 'Spear', 'Frame')
    spear.set_editor_property('relative_location', unreal.Vector(135, 0, 18)); spear.set_editor_property('component_tags', [unreal.Name('BallistaSpear')])
    m = mesh('SM_FireBallista_Spear')
    if m: spear.set_editor_property('static_mesh', m)
    spear.set_collision_profile_name('NoCollision'); spear.set_editor_property('cast_shadow', False)
    coals, _ = add_comp(tb, unreal.PointLightComponent, 'Coals')
    coals.set_editor_property('relative_location', unreal.Vector(-55, -75, 80)); coals.set_editor_property('component_tags', [unreal.Name('BallistaCoals')])
    coals.set_editor_property('intensity_units', enum(unreal.LightUnits, 'CANDELAS')); coals.set_editor_property('intensity', 1200.0)
    coals.set_editor_property('use_temperature', True); coals.set_editor_property('temperature', 1900.0)
    coals.set_editor_property('attenuation_radius', 900.0); coals.set_editor_property('source_radius', 15.0); coals.set_editor_property('cast_shadows', False)
    BEL.compile_blueprint(tb); EAL.save_asset(DST + '/BP_TowerBallista')

# ---- BPC_CastleUpgrades + hero
comp = make_bp('BPC_CastleUpgrades', unreal.ActorComponent)
if comp: BEL.compile_blueprint(comp); EAL.save_asset(DST + '/BPC_CastleUpgrades')
hero = unreal.load_asset(HERO)
if 'CastleUpgrades' in names(hero): log.append('hero already has CastleUpgrades')
else:
    log.append('hero: + CastleUpgrades (BPC_CastleUpgrades)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0],
                                                                     new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add CastleUpgrades: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('CastleUpgrades'))
        BEL.compile_blueprint(hero); EAL.save_asset(HERO)

out = '\n'.join(log) + '\nNext: README step 3 (BPVar lines, then the graph pastes and the BP_ZombieWallBreaker merge).'
if not DRY: open(os.path.join(HERE, 'setup_castle224.txt'), 'w').write(out)
unreal.log(out)
