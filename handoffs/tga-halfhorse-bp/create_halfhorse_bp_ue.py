# MASTER ONLY (UE 5.3). Creates BP_HalfHorseZombie: a child of BP_Zombie plus one new component, 'Torso'
# (a SkeletalMeshComponent under the inherited Mesh), added with SubobjectDataSubsystem. The torso gets the zombie's
# own mesh and skin at runtime (BeginPlay copies them from the inherited Mesh before the horse body replaces it), so no
# licensed asset path is written anywhere. Idempotent: an existing asset is kept.
#   py "<repo>/handoffs/tga-halfhorse-bp/create_halfhorse_bp_ue.py"
import unreal
DST, NAME = '/Game/CastleDefender/Characters/Enemies/HalfHorseZombie', 'BP_HalfHorseZombie'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
path = DST + '/' + NAME
if EAL.does_asset_exist(path):
    unreal.log('BP_HalfHorseZombie already exists, kept as is: ' + path)
else:
    parent = unreal.load_asset('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie')
    if not parent: raise RuntimeError('BP_Zombie not found; nothing created')
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent.generated_class())
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, DST, unreal.Blueprint, f)
    if not bp: raise RuntimeError('create_asset failed for ' + path)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    mesh_h = None
    for h in handles:
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(sds.k2_find_subobject_data_from_handle(h))
        if isinstance(obj, unreal.SkeletalMeshComponent): mesh_h = h; break
    if mesh_h is None: raise RuntimeError('No inherited SkeletalMeshComponent (Mesh) found on the new child; asset kept for inspection: ' + path)
    params = unreal.AddNewSubobjectParams(parent_handle=mesh_h, new_class=unreal.SkeletalMeshComponent, blueprint_context=bp)
    new_h, reason = sds.add_new_subobject(params)
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(new_h): raise RuntimeError('Adding Torso failed: %s' % reason)
    sds.rename_subobject(new_h, unreal.Text('Torso'))
    BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp)
    unreal.log('Created ' + path + ' with a Torso component. Next: paste BP_HalfHorseZombie_vars.txt line by line, then Ctrl+A, Delete '
               'in the EventGraph and paste BP_HalfHorseZombie_EventGraph.txt. Compile.')
