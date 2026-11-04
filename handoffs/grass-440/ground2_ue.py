# #440 ground, round 2 (i5, 2026-11-04), from i9's BaseColor measure (chat 1458): road 41/36/32 sRGB, covering 45-58 % of the view, meadow 53/58/29, covering 16 %.
# Bare soil should sit near 100 sRGB. The road is hard-coded in M_MountainBackdrop (soilCol, mudCol x 0.5), so no tint could reach it: that was the real dark ground.
# All in one recompile: road + mud x 3 (about 70 sRGB, still dirty and damp), meadow tints x 2 (about 78 sRGB), and the tyre tread removal, so skip no_tread_ue.py.
# Tentacle corrupted earth is deliberate and stays as it is. Backup of the old values: ground2_backup.json.
#   py ground2_ue.py --dry-run                 finds all 3 lines + the MI, changes nothing
#   py ground2_ue.py --apply                   edits, recompiles the landscape material (can take minutes), saves 2 assets. No map save
#   py ground2_ue.py --apply --road 1.0 --tint 1.5   softer: road factor (0.5 = before), meadow tint multiplier on today's values
#   py ground2_ue.py --revert                  everything back
# Aborts in PIE.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
H = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/grass-440/', 'C:/Users/hossa/Documents/agent-office/handoffs/grass-440/') if os.path.isdir(h))
BK = H + 'ground2_backup.json'
D = '/Game/CastleDefender/Environment/Mountains/Materials/'
arg = lambda k, d: float(A[A.index(k) + 1]) if k in A else d
ROAD, TINT = arg('--road', 1.5), arg('--tint', 2.0)
m = unreal.load_asset(D + 'M_MountainBackdrop'); mi = unreal.load_asset(D + 'MI_MountainBackdrop_Near'); pp = m.get_path_name()
nodes = [x for x in unreal.ObjectIterator(unreal.MaterialExpressionCustom) if x.get_path_name().startswith(pp + ':') or x.get_path_name().startswith(pp + '.')]
if len(nodes) != 1: print('STOP: expected 1 Custom node, found', len(nodes)); raise SystemExit
n = nodes[0]; code = n.get_editor_property('code')
SOIL = 'float3 soilCol = lerp(sL.xxx, sB, 0.4000) * float3(0.90, 0.88, 0.84) * %s;'
MUD = 'float3 mudCol = lerp(sL.xxx, sB, 0.3) * float3(0.80, 0.76, 0.72) * %s * 0.5;'
TREAD_OLD = 'float tA = 1.3 * tread * gx * step(abs(x), tw * 1.1) * dep / 9.0;'
TREAD_NEW = 'float tA = 0.0;   // #482: no tyre tread on medieval cart ruts. Was: 1.3 * tread * gx * step(abs(x), tw * 1.1) * dep / 9.0'
get = lambda k: list(MEL.get_material_instance_vector_parameter_value(mi, k).to_tuple())
def put(k, v): MEL.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
if '--revert' in A:
    if not os.path.exists(BK): print('NO BACKUP', BK); raise SystemExit
    d = json.load(open(BK)); n.set_editor_property('code', d['code']); put('GrassTint', d['GrassTint']); put('ForestTint', d['ForestTint'])
    MEL.update_material_instance(mi); MEL.recompile_material(m); print('saved', EAL.save_loaded_asset(m), EAL.save_loaded_asset(mi)); os.remove(BK); print('REVERTED'); raise SystemExit
if os.path.exists(BK): print('ALREADY APPLIED (ground2_backup.json exists): --revert first'); raise SystemExit
soil0, mud0 = SOIL % '0.5000', MUD % '0.5000'
counts = {'soil': code.count(soil0), 'mud': code.count(mud0), 'tread old': code.count(TREAD_OLD), 'tread new': code.count(TREAD_NEW)}
print('lines found:', counts)
if counts['soil'] != 1 or counts['mud'] != 1 or counts['tread old'] + counts['tread new'] != 1: print('STOP: shader differs from what this was built on, nothing changed'); raise SystemExit
g, f = get('GrassTint'), get('ForestTint')
ng, nf = [round(v * TINT, 3) for v in g[:3]], [round(v * TINT, 3) for v in f[:3]]
print('road factor 0.5 ->', ROAD, '| GrassTint', [round(v, 3) for v in g[:3]], '->', ng, '| ForestTint', [round(v, 3) for v in f[:3]], '->', nf)
if '--apply' not in A: print('dry run: nothing changed'); raise SystemExit
json.dump({'code': code, 'GrassTint': g, 'ForestTint': f}, open(BK, 'w'))
new = code.replace(soil0, SOIL % ('%.4f' % ROAD)).replace(mud0, MUD % ('%.4f' % ROAD)).replace(TREAD_OLD, TREAD_NEW)
n.set_editor_property('code', new); put('GrassTint', ng); put('ForestTint', nf)
MEL.update_material_instance(mi); MEL.recompile_material(m)
print('saved', EAL.save_loaded_asset(m), EAL.save_loaded_asset(mi), '| same 2 spots please, lit + BaseColor, plus one close shot of the gate road')
