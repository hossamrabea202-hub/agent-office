# #461 castle harmony, material pass (i5, 2026-11-03). One stone family, one look: the 4 stone MIs on M_Castle_StoneWall_World
# (Stone, Trim, WalkFlag, StepCap: 565 visible components on the Master, 5 different looks, 2 different stones) become plain
# children of ONE new MI, MI_Castle_Stone_Harmony461. Nothing in the map changes, no actor is touched: only 5 material assets.
# Tune the whole family by editing that one MI. Values = the AAA wall modules (MI_WallFrontL_AAA on the Master): tint, moss, grime,
# dirt band, macro, lime 0. Stone = T_vdbhdju (mean albedo 0.209, measured; keep-entrance bake 0.207: same stone).
# TileSize 240: the texture has 6 courses per tile, so 40 cm courses / ~44 cm blocks (medieval ashlar 25-45 cm, #469).
# MI_Castle_Planks_World is wood (keep door, floors): NOT touched. BP_Forge keeps its Trim stop-gap until i9's #456.
#   py harmony461_ue.py --dry-run             what would change (nothing changed)
#   py harmony461_ue.py --apply [--nosave]    do it (--nosave: in memory only, for a test); backup harmony461_backup.json
#   py harmony461_ue.py --revert [--nosave]   the 4 MIs back to their exact old parent + values
#   py harmony461_ue.py --tile 280 --apply    other stone size, same everything else
# Works before and after #470 (crack params are only set while the parent still has them). Aborts in PIE.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
HERE = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/castle-harmony-461/', 'C:/Users/hossa/Documents/agent-office/handoffs/castle-harmony-461/') if os.path.isdir(h))
BK = HERE + ('harmony461_backup.test.json' if '--nosave' in A else 'harmony461_backup.json')   # a test never touches the real backup
BASE = '/Game/CastleDefender/Shared/Materials/Castle/M_Castle_StoneWall_World'
TEX = '/Game/CastleDefender/AssetPacks/Fab/Megascans/Surfaces/'
NEW_NAME = 'MI_Castle_Stone_Harmony461'
SCALARS = {'GrimeHeight_cm': 260.0, 'TileSize_cm': 240.0, 'MacroSize_cm': 2300.0, 'MossAmount': 1.0, 'MacroStrength': 0.35, 'SoilSize_cm': 220.0,
           'DirtBand_cm': 150.0, 'DirtAmount': 1.0, 'MossHeight_cm': 650.0, 'AntiTile_SatLo': 0.38, 'AntiTile_SatHi': 0.62, 'AntiTile_Amount': 0.85,
           'AntiTile_AvgLum': 0.16, 'Detile_Contrast': 5.0, 'Detile_Amount': 1.0, 'LimewashAmount': 0.0, 'CrackAmount': 0.0}
VECTORS = {'Tint': (0.5332, 0.5146, 0.4836), 'MossColor': (0.16, 0.17, 0.12), 'GrimeColor': (0.45, 0.38, 0.3)}
TEXTURES = {'BaseColor': TEX + 'Stone_Wall_vdbhdju/Medium/T_vdbhdju_2K_B', 'ORM': TEX + 'Stone_Wall_vdbhdju/Medium/T_vdbhdju_2K_ORM',
            'Normal': TEX + 'Stone_Wall_vdbhdju/Medium/T_vdbhdju_2K_N', 'SoilTex': TEX + 'Rocky_Soil_Ground_vb2qdgwew/Raw/T_vb2qdgwew_8K_B'}
CHILD_NAMES = ('MI_Castle_StoneWall_World', 'MI_Castle_Trim_World', 'MI_Castle_WalkFlag_World', 'MI_Castle_StepCap')
if '--tile' in A: SCALARS['TileSize_cm'] = float(A[A.index('--tile') + 1])

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
    print('reverted', len(bk), '(%s left in place, unused)' % NEW_NAME); raise SystemExit

names = {'s': [str(x) for x in MEL.get_scalar_parameter_names(base)], 'v': [str(x) for x in MEL.get_vector_parameter_names(base)], 't': [str(x) for x in MEL.get_texture_parameter_names(base)]}
skip = [k for k in SCALARS if k not in names['s']]
print('harmony MI:', NEW_PATH, '| Tile', SCALARS['TileSize_cm'], '| params not on this base, skipped:', skip)
for n, mi in kids.items():
    s = snapshot(mi)
    print('CHILD', n, 'parent', s['parent'].split('.')[-1], '| old Tint', [round(x, 3) for x in s['vectors'].get('Tint', [])], 'Tile', s['scalars'].get('TileSize_cm'), 'Lime', s['scalars'].get('LimewashAmount'), 'Moss', s['scalars'].get('MossAmount'), '| BaseColor', (s['textures'].get('BaseColor') or '').split('.')[-1])
for k, p in TEXTURES.items():
    if not EAL.does_asset_exist(p): print('MISSING TEXTURE', p); raise SystemExit
if '--apply' not in A:
    print('dry run: nothing changed'); raise SystemExit

bk = json.load(open(BK)) if os.path.exists(BK) else {}
for n, mi in kids.items():
    if n not in bk and mi.get_editor_property('parent').get_name() != NEW_NAME: bk[n] = snapshot(mi)
json.dump(bk, open(BK, 'w'), indent=1)
new = unreal.load_asset(NEW_PATH) if EAL.does_asset_exist(NEW_PATH) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(NEW_NAME, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(new, base)
for k, v in SCALARS.items():
    if k in names['s']: MEL.set_material_instance_scalar_parameter_value(new, k, v)
for k, v in VECTORS.items(): MEL.set_material_instance_vector_parameter_value(new, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
for k, p in TEXTURES.items(): MEL.set_material_instance_texture_parameter_value(new, k, unreal.load_asset(p))
MEL.update_material_instance(new)
for n, mi in kids.items():
    MEL.clear_all_material_instance_parameters(mi)
    MEL.set_material_instance_parent(mi, new)
    MEL.update_material_instance(mi)
    print('CHILD OK', n, '-> parent', mi.get_editor_property('parent').get_name(), '| Tile now', MEL.get_material_instance_scalar_parameter_value(mi, 'TileSize_cm'), '| Tint now', [round(x, 3) for x in MEL.get_material_instance_vector_parameter_value(mi, 'Tint').to_tuple()[:3]])
    if '--nosave' not in A: EAL.save_loaded_asset(mi)
if '--nosave' not in A: EAL.save_loaded_asset(new)
print('APPLIED', 'in memory only' if '--nosave' in A else 'saved 5 assets; no map save needed')
