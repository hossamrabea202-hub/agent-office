# #185 Medics, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/medics-185/setup_medics185_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/medics-185/setup_medics185_ue.py"
# Makes in /Game/CastleDefender/Gameplay/Medics:
#   BP_Medic    (Character) stand-in body = BP_SoldierSword's Mesh (skeletal mesh + anim class + offset), AI possess, walk 380,
#               RVO; "Satchel" (tag MedicSatchel) and "Armband" (tag MedicArmband) StaticMeshComponents with TGA's
#               SM_MedicSatchel / SM_MedicArmband (#248: /Game/CastleDefender/Characters/NPC/MedicGear - run
#               assets/tga/MedicGear/import_medicgear_ue.py first if missing; the graph attaches them to the bones);
#               "HealFX" TextRender (tag HealFX) "+ HEAL", green, 130 cm up, hidden (the graph shows it while healing).
#   BPC_Medics  (ActorComponent), added to the hero as "Medics".
import os, sys, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'medics-185')
DRY = '--dry-run' in sys.argv
DST = '/Game/CastleDefender/Gameplay/Medics'
GEAR = '/Game/CastleDefender/Characters/NPC/MedicGear/'
SOLDIER = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#185 medics setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return AT.create_asset(name, DST, unreal.Blueprint, f)


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add_comp(bp, cls, name):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(bp)[0], new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


sold = unreal.load_asset(SOLDIER) if EAL.does_asset_exist(SOLDIER) else None
sm = unreal.get_default_object(sold.generated_class()).get_editor_property('mesh') if sold else None
if not sm: log.append('WARNING: BP_SoldierSword not found - set BP_Medic Mesh by hand')
med = make_bp('BP_Medic', unreal.Character)
if med:
    cdo = unreal.get_default_object(med.generated_class())
    cdo.set_editor_property('auto_possess_ai', unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    cdo.set_editor_property('ai_controller_class', unreal.AIController)
    cdo.set_editor_property('use_controller_rotation_yaw', False)
    mv = cdo.get_editor_property('character_movement')
    mv.set_editor_property('max_walk_speed', 380.0); mv.set_editor_property('use_rvo_avoidance', True); mv.set_editor_property('orient_rotation_to_movement', True)
    if sm:
        me = cdo.get_editor_property('mesh')
        for k in ('skeletal_mesh_asset', 'anim_class', 'relative_location', 'relative_rotation', 'relative_scale3d'):
            me.set_editor_property(k, sm.get_editor_property(k))
    for name, tag, mesh in (('Satchel', 'MedicSatchel', 'SM_MedicSatchel'), ('Armband', 'MedicArmband', 'SM_MedicArmband')):
        c = add_comp(med, unreal.StaticMeshComponent, name)
        c.set_editor_property('component_tags', [unreal.Name(tag)]); c.set_collision_profile_name('NoCollision')
        if EAL.does_asset_exist(GEAR + mesh): c.set_editor_property('static_mesh', unreal.load_asset(GEAR + mesh))
        else: log.append('  MISSING %s%s (run assets/tga/MedicGear/import_medicgear_ue.py)' % (GEAR, mesh))
    fx = add_comp(med, unreal.TextRenderComponent, 'HealFX')
    fx.set_editor_property('component_tags', [unreal.Name('HealFX')]); fx.set_editor_property('relative_location', unreal.Vector(0, 0, 130))
    fx.set_editor_property('text', unreal.Text('+ HEAL')); fx.set_editor_property('world_size', 22.0)
    fx.set_editor_property('horizontal_alignment', unreal.HorizTextAligment.EHTA_CENTER)
    fx.set_editor_property('text_render_color', unreal.Color(r=150, g=255, b=160, a=255)); fx.set_editor_property('visible', False)
    fx.set_collision_profile_name('NoCollision')
    BEL.compile_blueprint(med); EAL.save_asset(DST + '/BP_Medic')
comp = make_bp('BPC_Medics', unreal.ActorComponent)
if comp: BEL.compile_blueprint(comp); EAL.save_asset(DST + '/BPC_Medics')
hero = unreal.load_asset(HERO)
if 'Medics' in names(hero): log.append('hero already has Medics')
else:
    log.append('hero: + Medics (BPC_Medics)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0], new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add Medics: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('Medics')); BEL.compile_blueprint(hero); EAL.save_asset(HERO)
out = '\n'.join(log) + '\nNext: README step 3 (BPVar lines, the two graphs, then the BPC_MotionFX merge).'
if not DRY: open(os.path.join(HERE, 'setup_medics185.txt'), 'w').write(out)
unreal.log(out)
