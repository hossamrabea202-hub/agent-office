# Weapon kit wiring, editor setup (checkking, 2026-10-31). Safe to re-run.
#   py "<repo>/handoffs/weapon-kit-wiring/setup_weaponkit_ue.py"
# Run 1 (before the BPVar paste): creates /Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit, adds it to the hero as
#   "WeaponKit", and adds a StaticMeshComponent "KitWeapon" under KnightMesh (tag KitWeapon, hidden, no collision).
# Run 2 (after the 9 BPVar lines are pasted and compiled): fills Names / Prices / Damage / Meshes from weapons.json
#   (meshes from /Game/CastleDefender/Weapons/CK/<Folder>/SM_CK_<Folder>; run assets/checkking/Weapons/import_weapons_ue.py first).
import json, os, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'weapon-kit-wiring')
D, NAME = '/Game/CastleDefender/Gameplay/Castle', 'BPC_WeaponKit'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
log = []
path = D + '/' + NAME
if EAL.does_asset_exist(path):
    bp = unreal.load_asset(path)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, D, unreal.Blueprint, f); EAL.save_asset(path); log.append('created ' + path)

# ---- defaults (only once the BPVars exist)
have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
if {'Names', 'Prices', 'Damage', 'Meshes'} <= have:
    BEL.compile_blueprint(bp)
    W = json.load(open(os.path.join(HERE, 'weapons.json')))
    meshes = []
    for w in W:
        p = '/Game/CastleDefender/Weapons/CK/%s/SM_CK_%s' % (w['folder'], w['folder'])
        meshes.append(unreal.load_asset(p) if EAL.does_asset_exist(p) else None)
        if meshes[-1] is None: log.append('  missing mesh ' + p + ' (run import_weapons_ue.py)')
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('Names', [w['name'] for w in W]); cdo.set_editor_property('Prices', [w['price'] for w in W])
    cdo.set_editor_property('Damage', [w['damage'] for w in W]); cdo.set_editor_property('Meshes', meshes)
    EAL.save_asset(path); log.append('defaults: %d weapons, %d meshes found' % (len(W), sum(1 for m in meshes if m)))
else:
    log.append('BPVars not pasted yet: paste VARIABLES_BPVar.txt on BPC_WeaponKit, compile, then run this again for the defaults')

# ---- hero: WeaponKit component + KitWeapon mesh under KnightMesh
hero = unreal.load_asset(HERO)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
handles = sds.k2_gather_subobject_data_for_blueprint(hero)
by = {str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))): h for h in handles}
if 'WeaponKit' not in by:
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=bp.generated_class(), blueprint_context=hero))
    sds.rename_subobject(h, unreal.Text('WeaponKit')); log.append('hero: + WeaponKit')
if 'KitWeapon' not in by:
    parent = by.get('KnightMesh', handles[0])
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=unreal.StaticMeshComponent, blueprint_context=hero))
    sds.rename_subobject(h, unreal.Text('KitWeapon'))
    c = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
    c.set_editor_property('component_tags', [unreal.Name('KitWeapon')]); c.set_editor_property('visible', False)
    c.set_collision_profile_name('NoCollision'); log.append('hero: + KitWeapon (tag KitWeapon)')
BEL.compile_blueprint(hero); EAL.save_asset(HERO)
out = 'Weapon kit wiring setup\n' + '\n'.join(log)
open(os.path.join(HERE, 'setup_weaponkit.txt'), 'w').write(out); unreal.log(out)
