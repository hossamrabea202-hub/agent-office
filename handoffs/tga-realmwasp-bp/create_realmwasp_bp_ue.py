# MASTER ONLY (UE 5.3). Creates the empty BP_RealmWasp shell: a child of BP_Zombie, so cannons, soldiers, the hero's
# hits, wave counts and XP all treat the wasp as a zombie with no other change. Idempotent: an existing asset is kept.
#   py "<repo>/handoffs/tga-realmwasp-bp/create_realmwasp_bp_ue.py"
# Then: paste the BPVar lines, then the EventGraph (README).
import unreal
DST, NAME = '/Game/CastleDefender/Characters/Enemies/RealmWasp', 'BP_RealmWasp'
EAL = unreal.EditorAssetLibrary
path = DST + '/' + NAME
if EAL.does_asset_exist(path):
    unreal.log('BP_RealmWasp already exists, kept as is: ' + path)
else:
    parent = unreal.load_asset('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie')
    if not parent: raise RuntimeError('BP_Zombie not found; nothing created')
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent.generated_class())
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, DST, unreal.Blueprint, f)
    if not bp: raise RuntimeError('create_asset failed for ' + path)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_loaded_asset(bp)
    unreal.log('Created ' + path + ' (child of BP_Zombie). Next: open it, paste BP_RealmWasp_vars.txt line by line in My Blueprint, '
               'then in the EventGraph press Ctrl+A, Delete, and paste BP_RealmWasp_EventGraph.txt. Compile.')
