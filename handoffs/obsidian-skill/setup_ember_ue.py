# #477 setup (i5, 2026-11-03): run BEFORE pasting ember_merged.txt. Adds the Ember variables to BPC_ObsidianSet, imports the icon, sets the defaults.
#   py setup_ember_ue.py --dry-run                what is missing (nothing changed)
#   py setup_ember_ue.py --apply [--bp <path>]    backup BPC_ObsidianSet_bak477 (once), add + compile, NOT saved until the paste compiles
# Tune on the class defaults, no paste: EmberCooldown 15, EmberDamage 80, EmberRadius 600, EmberKey Seven, badge EmberX / EmberY (fraction of the screen).
# None is a SaveGame variable: the save slot is unchanged. Aborts in PIE.
import os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
BEL, EAL = unreal.BlueprintEditorLibrary, unreal.EditorAssetLibrary
PATH = A[A.index('--bp') + 1] if '--bp' in A else '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
HERE = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/obsidian-skill/', 'C:/Users/hossa/Documents/agent-office/handoffs/obsidian-skill/') if os.path.isdir(h))
UI = '/Game/CastleDefender/UI/HUD'
bp = unreal.load_asset(PATH)
dbl = BEL.get_basic_type_by_name('real')
VARS = {'EmberCooldown': dbl, 'EmberDamage': dbl, 'EmberRadius': dbl, 'EmberRefuseAt': dbl, 'EmberX': dbl, 'EmberY': dbl,
        'EmberKey': BEL.get_struct_type(unreal.Key.static_struct()),
        'EmberMat': BEL.get_object_reference_type(unreal.MaterialInterface.static_class()),
        'EmberMID': BEL.get_object_reference_type(unreal.MaterialInstanceDynamic.static_class()),
        'EmberIcon': BEL.get_object_reference_type(unreal.Texture2D.static_class())}
cdo = unreal.get_default_object(bp.generated_class())
def has(n):
    try: cdo.get_editor_property(n); return True
    except Exception: return False
missing = [n for n in VARS if not has(n)]
print('BP', PATH, '| missing vars:', missing, '| badge material:', EAL.does_asset_exist(UI + '/M_UI_PotionBadge'), '| icon there:', EAL.does_asset_exist(UI + '/T_UI_EmberSkill'))
if '--apply' not in A: print('dry run: nothing changed'); raise SystemExit
if '--bp' not in A and not EAL.does_asset_exist(PATH + '_bak477'): print('backup', EAL.duplicate_asset(PATH, PATH + '_bak477') is not None)
if not EAL.does_asset_exist(UI + '/T_UI_EmberSkill'):
    t = unreal.AssetImportTask(); t.filename = HERE + 'T_UI_EmberSkill.png'; t.destination_path = UI; t.destination_name = 'T_UI_EmberSkill'; t.automated = True; t.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
for n in missing: print('add', n, BEL.add_member_variable(bp, n, VARS[n]))
BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
KEYD = unreal.Key(); KEYD.set_editor_property('key_name', 'Seven')
for k, v in (('EmberCooldown', 15.0), ('EmberDamage', 80.0), ('EmberRadius', 600.0), ('EmberRefuseAt', -100.0), ('EmberX', 0.546), ('EmberY', 0.929),
             ('EmberKey', KEYD), ('EmberMat', unreal.load_asset(UI + '/M_UI_PotionBadge')), ('EmberIcon', unreal.load_asset(UI + '/T_UI_EmberSkill'))):
    cdo.set_editor_property(k, v)
print('defaults:', {k: str(cdo.get_editor_property(k))[:60] for k in ('EmberCooldown', 'EmberDamage', 'EmberRadius', 'EmberRefuseAt', 'EmberX', 'EmberY', 'EmberKey', 'EmberMat', 'EmberIcon')})
print('SETUP OK. Next: paste ember_merged.txt, Refresh All Nodes, compile, save')
print('EmberKey =', cdo.get_editor_property('EmberKey').get_editor_property('key_name'))
