# #11 Survivors, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/survivors-11/setup_survivors11_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/survivors-11/setup_survivors11_ue.py"
# Creates in /Game/CastleDefender/Gameplay/Survivors:
#   BP_Survivor    (Character) stand-in body: BP_SoldierSword's Mesh (skeletal mesh + anim class + offset), AI possess on
#                  spawn, walk 130, RVO on; a TextRenderComponent "Label" (tag SurvLabel) 115 cm over the capsule, gold.
#                  The owner swaps the body for a MetaHuman later: only the Mesh changes, the graph stays.
#   BPC_Survivors  (ActorComponent) and adds it to the hero as "Survivors".
# Nothing else is touched: no level edit, no soldier / zombie / HUD change.
import os, sys, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'survivors-11')
DRY = '--dry-run' in sys.argv
DST = '/Game/CastleDefender/Gameplay/Survivors'
SOLDIER = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#11 survivors setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path):
        log.append('reusing ' + path); return unreal.load_asset(path), False
    log.append('create ' + path)
    if DRY: return None, True
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DST, unreal.Blueprint, f), True


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add_comp(bp, cls, name):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    root = SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: adding %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


# ---- the stand-in body, read from the soldier
sold = unreal.load_asset(SOLDIER) if EAL.does_asset_exist(SOLDIER) else None
sm = unreal.get_default_object(sold.generated_class()).get_editor_property('mesh') if sold else None
if sm:
    mesh_asset = sm.get_editor_property('skeletal_mesh_asset')
    log.append('soldier body: %s, anim %s' % (mesh_asset.get_path_name() if mesh_asset else None, sm.get_editor_property('anim_class')))
else:
    log.append('WARNING: BP_SoldierSword not found: set BP_Survivor Mesh (skeletal mesh + anim class) by hand')

surv, _ = make_bp('BP_Survivor', unreal.Character)
if surv:
    cdo = unreal.get_default_object(surv.generated_class())
    cdo.set_editor_property('auto_possess_ai', unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    cdo.set_editor_property('ai_controller_class', unreal.AIController)
    cdo.set_editor_property('use_controller_rotation_yaw', False)
    mv = cdo.get_editor_property('character_movement')
    mv.set_editor_property('max_walk_speed', 130.0); mv.set_editor_property('use_rvo_avoidance', True)
    mv.set_editor_property('orient_rotation_to_movement', True)
    if sm:
        me = cdo.get_editor_property('mesh')
        for k in ('skeletal_mesh_asset', 'anim_class', 'relative_location', 'relative_rotation', 'relative_scale3d'):
            me.set_editor_property(k, sm.get_editor_property(k))
    lab = add_comp(surv, unreal.TextRenderComponent, 'Label')
    lab.set_editor_property('component_tags', [unreal.Name('SurvLabel')])
    lab.set_editor_property('relative_location', unreal.Vector(0, 0, 115))
    lab.set_editor_property('text', unreal.Text('Wounded soldier'))
    lab.set_editor_property('world_size', 16.0)
    lab.set_editor_property('horizontal_alignment', unreal.HorizTextAligment.EHTA_CENTER)
    lab.set_editor_property('vertical_alignment', unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    lab.set_editor_property('text_render_color', unreal.Color(r=255, g=190, b=90, a=255))
    lab.set_collision_profile_name('NoCollision')
    BEL.compile_blueprint(surv); EAL.save_asset(DST + '/BP_Survivor')

comp, _ = make_bp('BPC_Survivors', unreal.ActorComponent)
if comp:
    BEL.compile_blueprint(comp); EAL.save_asset(DST + '/BPC_Survivors')

hero = unreal.load_asset(HERO)
if 'Survivors' in names(hero):
    log.append('hero already has Survivors')
else:
    log.append('hero: + Survivors (BPC_Survivors)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0],
                                                                     new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add Survivors: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('Survivors'))
        BEL.compile_blueprint(hero); EAL.save_asset(HERO)

out = '\n'.join(log) + '\nNext: README step 3 (BPVar lines on both Blueprints, then the two graph pastes).'
if not DRY: open(os.path.join(HERE, 'setup_survivors11.txt'), 'w').write(out)
unreal.log(out)
