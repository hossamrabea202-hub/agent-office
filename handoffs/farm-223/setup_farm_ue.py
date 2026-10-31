# MASTER ONLY (UE 5.3). #223 farming system setup, idempotent, run twice:
#  run 1 (Blueprints missing): creates in /Game/CastleDefender/Gameplay/Farm/
#     BP_FarmPlot      (Actor)     Ground = SM_Field_Plot, Crops = InstancedStaticMesh (no collision), Zone = Box 210x210x120 overlap
#     BP_Farmer        (Character) skeletal mesh + anim class copied from BP_SoldierSword (no weapons), AI possess on spawn,
#                                  AIController, walk 180, RVO on
#     BP_FarmDirector  (Actor)     Granary = StaticMesh (pick a shed / barn mesh; the farmers deliver and shelter here)
#     BP_FarmerHire    (Actor)     Zone = Sphere r 250 overlap (place it next to the barracks NPC)
#  then paste VARIABLES.md lines + the graphs (README order), compile all four.
#  run 2 (Blueprints exist): fills BP_FarmPlot.StageMeshes from TGA's FarmCrops (/Game/CastleDefender/Props/Farm) and
#     re-applies the farmer class defaults. Compile + save are done here.
#   py "<repo>/handoffs/farm-223/setup_farm_ue.py"
import unreal
DST = '/Game/CastleDefender/Gameplay/Farm'
CROPS = '/Game/CastleDefender/Props/Farm/'
SOLDIER = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary


def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): return unreal.load_asset(path), False
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DST, unreal.Blueprint, f), True


def add_comp(bp, cls, name, parent_handle=None):
    root = parent_handle or SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: adding %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


def farmer_defaults(bp):
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('auto_possess_ai', unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    cdo.set_editor_property('ai_controller_class', unreal.AIController)
    mv = cdo.get_editor_property('character_movement'); mv.set_editor_property('max_walk_speed', 180.0); mv.set_editor_property('use_rvo_avoidance', True)
    sold = unreal.load_asset(SOLDIER)
    if sold:
        sm = unreal.get_default_object(sold.generated_class()).get_editor_property('mesh')
        me = cdo.get_editor_property('mesh')
        me.set_editor_property('skeletal_mesh_asset', sm.get_editor_property('skeletal_mesh_asset'))
        me.set_editor_property('anim_class', sm.get_editor_property('anim_class'))
        me.set_editor_property('relative_location', sm.get_editor_property('relative_location'))
        me.set_editor_property('relative_rotation', sm.get_editor_property('relative_rotation'))
    else:
        unreal.log_warning('BP_SoldierSword not found: set BP_Farmer Mesh (skeletal mesh + anim class) by hand')


made = []
plot, new = make_bp('BP_FarmPlot', unreal.Actor)
if new:
    g = add_comp(plot, unreal.StaticMeshComponent, 'Ground'); m = unreal.load_asset(CROPS + 'SM_Field_Plot')
    if m: g.set_editor_property('static_mesh', m)
    c = add_comp(plot, unreal.InstancedStaticMeshComponent, 'Crops'); c.set_collision_profile_name('NoCollision')
    z = add_comp(plot, unreal.BoxComponent, 'Zone'); z.set_editor_property('box_extent', unreal.Vector(210, 210, 120))
    z.set_collision_profile_name('OverlapAllDynamic'); z.set_editor_property('generate_overlap_events', True)
    made.append('BP_FarmPlot')
farmer, new = make_bp('BP_Farmer', unreal.Character)
if new: made.append('BP_Farmer')
farmer_defaults(farmer)
dirb, new = make_bp('BP_FarmDirector', unreal.Actor)
if new: add_comp(dirb, unreal.StaticMeshComponent, 'Granary'); made.append('BP_FarmDirector')
hire, new = make_bp('BP_FarmerHire', unreal.Actor)
if new:
    s = add_comp(hire, unreal.SphereComponent, 'Zone'); s.set_editor_property('sphere_radius', 250.0)
    s.set_collision_profile_name('OverlapAllDynamic'); s.set_editor_property('generate_overlap_events', True)
    made.append('BP_FarmerHire')

if not made:   # run 2: the variables exist now
    names = ['', 'SM_Crop_Wheat_Sown', 'SM_Crop_Wheat_Growing', 'SM_Crop_Wheat_Ripe', 'SM_Crop_Wheat_Harvested',
             '', 'SM_Crop_Cabbage_Young', 'SM_Crop_Cabbage_Young', 'SM_Crop_Cabbage_Ripe', '']
    meshes = [unreal.load_asset(CROPS + n) if n else None for n in names]
    missing = [n for n, m in zip(names, meshes) if n and not m]
    if missing: unreal.log_warning('FarmCrops not imported (run assets/tga/FarmCrops/import_farm_ue.py first): ' + ', '.join(missing))
    try:
        unreal.get_default_object(plot.generated_class()).set_editor_property('StageMeshes', meshes)
    except Exception as e:
        unreal.log_warning('StageMeshes not set (%s): paste the BP_FarmPlot variables and compile, then run again' % e)
for bp in (plot, farmer, dirb, hire):
    BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp)
unreal.log('Farm setup: created %s. %s' % (', '.join(made) or 'nothing new',
           'Next: paste VARIABLES.md + graphs (README), compile, run this again.' if made else 'StageMeshes + farmer defaults applied.'))
