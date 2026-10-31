# #297 Cave door, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/cave-296-297/setup_cavedoor297_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/cave-296-297/setup_cavedoor297_ue.py"
# Makes /Game/CastleDefender/Gameplay/Cave/BP_CaveDoor (Actor):
#   Door  StaticMeshComponent, stand-in slab 1.2 x 0.15 x 2.2 m (engine cube) until the #309 mine door mesh lands;
#         blocks like a wall (BlockAll)
#   Exit  ArrowComponent (editor only): points where the hero comes out when he arrives at this door
# Nothing else is changed (no level, hero or HUD edit). Placing the two doors is README step 4.
import os, sys, unreal

try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\cave-296-297'
DRY = '--dry-run' in sys.argv
DST, NAME = '/Game/CastleDefender/Gameplay/Cave', 'BP_CaveDoor'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#297 cave door setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add_comp(bp, cls, name):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(bp)[0], new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


path = DST + '/' + NAME
if EAL.does_asset_exist(path):
    log.append('reusing ' + path); bp = unreal.load_asset(path)
else:
    log.append('create ' + path)
    bp = None
    if not DRY:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        bp = AT.create_asset(NAME, DST, unreal.Blueprint, f)
if bp and not DRY:
    door = add_comp(bp, unreal.StaticMeshComponent, 'Door')
    if not door.get_editor_property('static_mesh'):
        door.set_editor_property('static_mesh', unreal.load_asset('/Engine/BasicShapes/Cube'))
        door.set_editor_property('relative_scale3d', unreal.Vector(0.15, 1.2, 2.2))     # thin along X (the door faces +X)
        door.set_editor_property('relative_location', unreal.Vector(0, 0, 110))
        log.append('  Door: stand-in cube slab (swap the mesh when #309 lands)')
    door.set_collision_profile_name('BlockAll')
    arrow = add_comp(bp, unreal.ArrowComponent, 'Exit')
    arrow.set_editor_property('arrow_size', 2.0); arrow.set_editor_property('relative_location', unreal.Vector(0, 0, 40))
    BEL.compile_blueprint(bp); EAL.save_asset(path)
elif bp is None and not DRY:
    log.append('FAILED to create ' + path)

out = '\n'.join(log) + '\nNext: README step 2 (8 BPVar lines on BP_CaveDoor, Compile), then step 3 (paste BP_CaveDoor_graph.txt).'
if not DRY: open(os.path.join(HERE, 'setup_cavedoor297.txt'), 'w').write(out)
unreal.log(out)
