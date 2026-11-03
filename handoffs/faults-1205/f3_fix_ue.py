# F3 (Alien's Play test, i9 chat 1205): "hero must start in the FULL Obsidian set; Vesna shows all 4 bundles as FORGING".
# Cause (i5 probe, f3_probe_ue.py): the HERO's own copy of BPC_ObsidianSet (BP_ThirdPersonCharacter > ObsidianSet) has
# AvailMask = 0 and PieceId = [] saved on it. Those override the class data (AvailMask 991, 15 piece rows), so nothing is
# available (Vesna: FORGING x4) and no piece mesh is ever attached to the hero (only the cuirass via MPC Armor).
# Fix (data only, no graph): reset the hero copy's data variables to the class values, and start the set OWNED + WORN
# (ObsOwned = ObsWorn = AvailMask). A new game starts in every Obsidian piece that has art; the Helm stays FORGING until
# its mesh exists. Old saves keep what they saved (LoadSaved overrides the defaults, same as i9's cuirass start).
#   py f3_fix_ue.py --dry-run | --apply | --revert          backup: f3_backup.json (the hero copy's old values). Master only.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
H = next((h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/faults-1205/', 'C:/Users/hossa/Documents/agent-office/handoffs/faults-1205/')
          if os.path.isdir(h)), None)
BK = H + 'f3_backup.json'
DATA = ('AvailMask', 'PieceId', 'PieceBone', 'PieceOffset', 'KnightCover')       # reset to the class values
START = ('ObsOwned', 'ObsWorn')                                                  # = AvailMask (all pieces with art)
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
setc = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet').generated_class()
cdo = unreal.get_default_object(setc)
hero = unreal.load_asset(HERO)
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
tpl = next((L.get_object(L.get_data(h)) for h in sub.k2_gather_subobject_data_for_blueprint(hero)
            if L.get_object(L.get_data(h)) and L.get_object(L.get_data(h)).get_class() == setc), None)
if not tpl: print('NO ObsidianSet component on the hero'); raise SystemExit
def ser(v):
    if isinstance(v, unreal.Transform):
        t, r, s = v.translation, v.rotation.rotator(), v.scale3d; return ['XF', t.x, t.y, t.z, r.roll, r.pitch, r.yaw, s.x, s.y, s.z]
    if isinstance(v, unreal.Name): return ['N', str(v)]
    if hasattr(v, '__iter__') and not isinstance(v, str): return [ser(x) for x in v]
    return v
def de(v):
    if isinstance(v, list) and v and v[0] == 'XF': return unreal.Transform(unreal.Vector(*v[1:4]), unreal.Rotator(*v[4:7]), unreal.Vector(*v[7:10]))
    if isinstance(v, list) and v and v[0] == 'N': return unreal.Name(v[1])
    if isinstance(v, list): return [de(x) for x in v]
    return v
cur = {n: tpl.get_editor_property(n) for n in DATA + START}
if '--revert' in A:
    bk = json.load(open(BK)); hero.modify(); tpl.modify()
    for n, v in bk.items(): tpl.set_editor_property(n, de(v))
    unreal.BlueprintEditorLibrary.compile_blueprint(hero); unreal.EditorAssetLibrary.save_loaded_asset(hero)
    print('REVERTED hero ObsidianSet to', {n: (len(v) if isinstance(v, list) else v) for n, v in bk.items()}); raise SystemExit
want = {n: cdo.get_editor_property(n) for n in DATA}
avail = want['AvailMask']; want['ObsOwned'] = avail; want['ObsWorn'] = avail
for n in DATA + START:
    a, b = cur[n], want[n]
    la = len(a) if hasattr(a, '__len__') and not isinstance(a, (str, int)) else a
    lb = len(b) if hasattr(b, '__len__') and not isinstance(b, (str, int)) else b
    print('%-12s hero %-10s -> %s' % (n, la, lb))
bits = [i + 10 for i in range(11) if avail & (1 << i)]
print('start worn piece ids:', bits, '(15 = helm: %s)' % ('art' if avail & 32 else 'no art yet, stays FORGING'))
if '--dry-run' in A or '--apply' not in A: print('DRY RUN: nothing changed'); raise SystemExit
if not os.path.exists(BK): json.dump({n: ser(v) for n, v in cur.items()}, open(BK, 'w'))
hero.modify(); tpl.modify()
for n, v in want.items(): tpl.set_editor_property(n, v)
unreal.BlueprintEditorLibrary.compile_blueprint(hero); unreal.EditorAssetLibrary.save_loaded_asset(hero)
print('APPLIED + SAVED hero BP. Check in Play (NEW game, no old save): every Obsidian piece with art is on the hero, Vesna shows Torso / Gauntlets / Legs owned.')
