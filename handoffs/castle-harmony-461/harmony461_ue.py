# #461 castle harmony, material pass (i5, 2026-11-03; v2 after i9's tone pass, chat 1286). One stone family: the 4 stone MIs on
# M_Castle_StoneWall_World (Stone, Trim, WalkFlag, StepCap: 565 visible components on the Master's 11-03 scan, 2 different stones)
# become plain children of ONE new MI, MI_Castle_Stone_Harmony461. No actor is touched, no map save: only 5 material assets.
# NO fixed look values: the new MI COPIES the live overrides of MI_Castle_StoneWall_World (i9's tone pass: tint, tile 320, moss, lime),
# so the walls keep their look exactly and Trim / WalkFlag / StepCap join them (rubble T_tinifauaw -> the walls' T_vdbhdju).
# Only exception: CrackAmount 0 while the parent still has it (#470). Tune the whole family afterwards by editing that one MI.
# MI_Castle_Planks_World is wood (keep door, floors): NOT touched.
#   py harmony461_ue.py --dry-run             what would change (nothing changed)
#   py harmony461_ue.py --apply [--nosave]    do it (--nosave: in memory only, for a test); backup harmony461_backup.json
#   py harmony461_ue.py --revert [--nosave]   the 4 MIs back to their exact old parent + values
#   py harmony461_ue.py --tile 280 --apply    other stone size, everything else as above
# Works before and after #470. Aborts in PIE.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
HERE = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/castle-harmony-461/', 'C:/Users/hossa/Documents/agent-office/handoffs/castle-harmony-461/') if os.path.isdir(h))
BK = HERE + ('harmony461_backup.test.json' if '--nosave' in A else 'harmony461_backup.json')   # a test never touches the real backup
BASE = '/Game/CastleDefender/Shared/Materials/Castle/M_Castle_StoneWall_World'
NEW_NAME = 'MI_Castle_Stone_Harmony461'
SOURCE = 'MI_Castle_StoneWall_World'                                  # the look every family member takes
CHILD_NAMES = ('MI_Castle_StoneWall_World', 'MI_Castle_Trim_World', 'MI_Castle_WalkFlag_World', 'MI_Castle_StepCap')
TILE = float(A[A.index('--tile') + 1]) if '--tile' in A else None

ar = unreal.AssetRegistryHelpers.get_asset_registry()
def find_mi(name):
    hits = [ad for ad in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')) if str(ad.asset_name) == name]
    return unreal.load_asset(str(hits[0].package_name)) if hits else None
base = unreal.load_asset(BASE)
if not base: print('NO BASE MATERIAL', BASE); raise SystemExit
kids = {}
for n in CHILD_NAMES:
    mi = find_mi(n)
    if not mi: print('MISSING', n); raise SystemExit
    kids[n] = mi
folder = kids['MI_Castle_StoneWall_World'].get_path_name().rsplit('/', 1)[0]
NEW_PATH = folder + '/' + NEW_NAME

def snapshot(mi):
    # only this MI's own overrides: inherited values must stay inherited after a revert
    d = {'parent': mi.get_editor_property('parent').get_path_name(), 'scalars': {}, 'vectors': {}, 'textures': {}}
    for p in mi.get_editor_property('scalar_parameter_values'):
        d['scalars'][str(p.parameter_info.name)] = p.parameter_value
    for p in mi.get_editor_property('vector_parameter_values'):
        v = p.parameter_value; d['vectors'][str(p.parameter_info.name)] = [v.r, v.g, v.b, v.a]
    for p in mi.get_editor_property('texture_parameter_values'):
        d['textures'][str(p.parameter_info.name)] = p.parameter_value.get_path_name() if p.parameter_value else None
    return d

def restore(mi, d):
    MEL.clear_all_material_instance_parameters(mi)
    MEL.set_material_instance_parent(mi, unreal.load_asset(d['parent'].split('.')[0]))
    for k, v in d['scalars'].items(): MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in d['vectors'].items(): MEL.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*v))
    for k, v in d['textures'].items():
        if v: MEL.set_material_instance_texture_parameter_value(mi, k, unreal.load_asset(v.split('.')[0]))
    MEL.update_material_instance(mi)

if '--revert' in A:
    if not os.path.exists(BK): print('NO BACKUP', BK); raise SystemExit
    bk = json.load(open(BK))
    for n, d in bk.items():
        restore(kids[n], d); print('REVERT', n, '->', d['parent'].split('.')[-1], len(d['scalars']), 'scalars', len(d['vectors']), 'vectors', len(d['textures']), 'textures')
        if '--nosave' not in A: EAL.save_loaded_asset(kids[n])
    os.remove(BK)                                                    # a later --apply takes the then-live look
    print('reverted', len(bk), '(%s left in place, unused)' % NEW_NAME); raise SystemExit

names = [str(x) for x in MEL.get_scalar_parameter_names(base)]
applied = kids[SOURCE].get_editor_property('parent').get_name() == NEW_NAME
if applied and '--tile' not in A: print('ALREADY APPLIED: the 4 MIs are children of', NEW_NAME, '| nothing to do'); raise SystemExit
src = None if applied else snapshot(kids[SOURCE])
if src and src['parent'].split('.')[-1] != base.get_name(): print('UNEXPECTED PARENT of', SOURCE, src['parent'], 'abort'); raise SystemExit
print('harmony MI:', NEW_PATH, '| look copied from', SOURCE, '| source overrides:', json.dumps(src) if src else '(already applied)')
for n, mi in kids.items():
    s = snapshot(mi)
    print('CHILD', n, 'parent', s['parent'].split('.')[-1], '| old Tint', [round(x, 3) for x in s['vectors'].get('Tint', [])], 'Tile', s['scalars'].get('TileSize_cm'), 'Lime', s['scalars'].get('LimewashAmount'), 'Moss', s['scalars'].get('MossAmount'), '| BaseColor', (s['textures'].get('BaseColor') or '').split('.')[-1])
if '--apply' not in A:
    print('dry run: nothing changed'); raise SystemExit

bk = json.load(open(BK)) if os.path.exists(BK) else {}
for n, mi in kids.items():
    if n not in bk and mi.get_editor_property('parent').get_name() != NEW_NAME: bk[n] = snapshot(mi)
json.dump(bk, open(BK, 'w'), indent=1)
new = unreal.load_asset(NEW_PATH) if EAL.does_asset_exist(NEW_PATH) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(NEW_NAME, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(new, base)
if src:
    for k, v in src['scalars'].items(): MEL.set_material_instance_scalar_parameter_value(new, k, v)
    for k, v in src['vectors'].items(): MEL.set_material_instance_vector_parameter_value(new, k, unreal.LinearColor(*v))
    for k, v in src['textures'].items():
        if v: MEL.set_material_instance_texture_parameter_value(new, k, unreal.load_asset(v.split('.')[0]))
    if 'CrackAmount' in names: MEL.set_material_instance_scalar_parameter_value(new, 'CrackAmount', 0.0)
if TILE: MEL.set_material_instance_scalar_parameter_value(new, 'TileSize_cm', TILE)
MEL.update_material_instance(new)
for n, mi in kids.items():
    MEL.clear_all_material_instance_parameters(mi)
    MEL.set_material_instance_parent(mi, new)
    MEL.update_material_instance(mi)
    print('CHILD OK', n, '-> parent', mi.get_editor_property('parent').get_name(), '| Tile now', MEL.get_material_instance_scalar_parameter_value(mi, 'TileSize_cm'), '| Tint now', [round(x, 3) for x in MEL.get_material_instance_vector_parameter_value(mi, 'Tint').to_tuple()[:3]])
    if '--nosave' not in A: EAL.save_loaded_asset(mi)
if '--nosave' not in A: EAL.save_loaded_asset(new)
print('APPLIED', 'in memory only' if '--nosave' in A else 'saved 5 assets; no map save needed')
