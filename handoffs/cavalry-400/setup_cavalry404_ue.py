# #404 Heavy cavalry, editor setup (checkking (Claude), 2026-11-01). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/cavalry-400/setup_cavalry404_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/cavalry-400/setup_cavalry404_ue.py"
# Needs the #402/#403 import first: py "<repo>/assets/checkking/Cavalry/import_cavalry_ue.py" (SK_Destrier & co.).
# Makes in /Game/CastleDefender/Gameplay/Cavalry:
#   BP_Cavalry  (Character) capsule 70 / 115; Mesh = SK_Destrier (0, 0, -115, yaw -90, single-node animation); AI possess,
#               walk 450 (the graph sets 450-950), RVO, orient to movement, turn rate 160 deg/s;
#               components Tack / Lance / RiderLegs (SkeletalMeshComponent under Mesh: SK_Destrier_Tack / _Lance /
#               _RiderLegs, the graph gives them Mesh as leader pose) and Rider (SkeletalMeshComponent = BP_SoldierSword's
#               Mesh: skeletal mesh + anim class + scale; the graph attaches it to bone RiderSocket and hides its legs).
#               No collision on the parts.
#   BPC_Cavalry (ActorComponent), added to the hero as "Cavalry".
# Nothing existing is changed except the hero gets the new "Cavalry" component (like #185 "Medics").
import os, sys, unreal

REPO = r'C:\Users\hossam.rabea\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'cavalry-400')
DRY = '--dry-run' in sys.argv
DST = '/Game/CastleDefender/Gameplay/Cavalry'
CAV = '/Game/CastleDefender/Characters/Cavalry/'
SOLDIER = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#404 cavalry setup' + (' (DRY RUN, nothing written)' if DRY else '')]

need = [CAV + n for n in ('SK_Destrier', 'SK_Destrier_Tack', 'SK_Destrier_Lance', 'SK_Destrier_RiderLegs', 'A_Destrier_Idle', 'A_Destrier_Gallop', 'M_CavalryInvisible')]
miss = [p for p in need if not EAL.does_asset_exist(p)]
if miss: log.append('MISSING (run assets/checkking/Cavalry/import_cavalry_ue.py first): ' + ', '.join(miss))


def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return AT.create_asset(name, DST, unreal.Blueprint, f)


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add_comp(bp, cls, name, parent_name=None):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    parent = have.get(parent_name) if parent_name else None
    if parent is None: parent = SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


sold = unreal.load_asset(SOLDIER) if EAL.does_asset_exist(SOLDIER) else None
sm = unreal.get_default_object(sold.generated_class()).get_editor_property('mesh') if sold else None
if not sm: log.append('WARNING: BP_SoldierSword not found - set BP_Cavalry Rider mesh by hand')
cav = make_bp('BP_Cavalry', unreal.Character)
if cav and not miss:
    cdo = unreal.get_default_object(cav.generated_class())
    cdo.set_editor_property('auto_possess_ai', unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    cdo.set_editor_property('ai_controller_class', unreal.AIController)
    cdo.set_editor_property('use_controller_rotation_yaw', False)
    cap = cdo.get_editor_property('capsule_component')
    cap.set_editor_property('capsule_radius', 70.0); cap.set_editor_property('capsule_half_height', 115.0)
    mv = cdo.get_editor_property('character_movement')
    mv.set_editor_property('max_walk_speed', 450.0); mv.set_editor_property('use_rvo_avoidance', True)
    mv.set_editor_property('orient_rotation_to_movement', True); mv.set_editor_property('rotation_rate', unreal.Rotator(0.0, 0.0, 160.0))
    mv.set_editor_property('max_acceleration', 900.0); mv.set_editor_property('braking_deceleration_walking', 900.0)
    me = cdo.get_editor_property('mesh')
    me.set_editor_property('skeletal_mesh_asset', unreal.load_asset(CAV + 'SK_Destrier'))
    me.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    me.set_editor_property('relative_location', unreal.Vector(0, 0, -115)); me.set_editor_property('relative_rotation', unreal.Rotator(0.0, 0.0, -90.0))
    for name, asset in (('Tack', 'SK_Destrier_Tack'), ('Lance', 'SK_Destrier_Lance'), ('RiderLegs', 'SK_Destrier_RiderLegs')):
        c = add_comp(cav, unreal.SkeletalMeshComponent, name, 'CharacterMesh0' if 'CharacterMesh0' in names(cav) else 'Mesh')
        c.set_editor_property('skeletal_mesh_asset', unreal.load_asset(CAV + asset)); c.set_collision_profile_name('NoCollision')
    r = add_comp(cav, unreal.SkeletalMeshComponent, 'Rider')
    r.set_collision_profile_name('NoCollision')
    if sm:
        for k in ('skeletal_mesh_asset', 'anim_class', 'relative_rotation', 'relative_scale3d'):   # rotation: the soldier mesh's yaw -90 (faces +X like the horse)
            r.set_editor_property(k, sm.get_editor_property(k))
        r.set_editor_property('relative_location', unreal.Vector(0, 0, 0))
    BEL.compile_blueprint(cav); EAL.save_asset(DST + '/BP_Cavalry')
comp = make_bp('BPC_Cavalry', unreal.ActorComponent)
if comp: BEL.compile_blueprint(comp); EAL.save_asset(DST + '/BPC_Cavalry')
hero = unreal.load_asset(HERO)
if 'Cavalry' in names(hero): log.append('hero already has Cavalry')
else:
    log.append('hero: + Cavalry (BPC_Cavalry)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0], new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add Cavalry: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('Cavalry')); BEL.compile_blueprint(hero); EAL.save_asset(HERO)
out = '\n'.join(log) + '\nNext: README steps 3-4 (BPVar lines, then the two graphs).'
if not DRY:
    try: open(os.path.join(HERE, 'setup_cavalry404.txt'), 'w').write(out)
    except OSError: pass
unreal.log(out)
