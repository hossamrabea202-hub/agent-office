# #472 step 1 (Master, editor idle, not in Play): add the new member variables the crowd pastes read. Safe to re-run.
#   py add_vars_472_ue.py --dry-run     lists what it would add
#   py add_vars_472_ue.py --apply       adds them, compiles, saves both Blueprints
#   py add_vars_472_ue.py --revert      removes them again, compiles, saves (ONLY after the old graphs are pasted back: README)
# Optional: --wm <asset path> --zombie <asset path> (i5 tests on temporary duplicates).
import sys, unreal
BEL = unreal.BlueprintEditorLibrary
ARGS = sys.argv[1:]
def arg(k, d):
    return ARGS[ARGS.index(k) + 1] if k in ARGS else d
P_WM = arg('--wm', '/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager')
P_Z = arg('--zombie', '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie')
def cls(p): return unreal.load_asset(p).generated_class()
C_WM, C_Z = cls('/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager'), cls('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie')
C_S, C_F = cls('/Game/CastleDefender/Characters/Knight/BP_SoldierSword'), cls('/Game/CastleDefender/Gameplay/Farm/BP_Farmer')
C_G = cls('/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl')
OBJ = BEL.get_object_reference_type
PLAN = {P_WM: [('RegHost', OBJ(C_WM)), ('ZombieReg', BEL.get_array_type(OBJ(C_Z))), ('SoldierCache', BEL.get_array_type(OBJ(C_S))),
               ('FarmerCache', BEL.get_array_type(OBJ(C_F))), ('GateCache', OBJ(C_G))],
        P_Z: [('WMRef', OBJ(C_WM)), ('LastMoveGoal', OBJ(unreal.Actor)), ('LastMoveAt', BEL.get_basic_type_by_name('real'))]}
apply_, revert = '--apply' in ARGS, '--revert' in ARGS
for path, rows in PLAN.items():
    bp = unreal.load_asset(path); cdo = unreal.get_default_object(bp.generated_class())
    def has(n):
        try: cdo.get_editor_property(n); return True
        except Exception: return False
    changed = False
    for name, typ in rows:
        there = has(name)
        if revert:
            if there:
                BEL.remove_member_variable(bp, name) if hasattr(BEL, 'remove_member_variable') else print('remove by hand:', name)
                changed = True
            print('remove' if there else 'absent', path.split('/')[-1], name)
        elif there: print('there ', path.split('/')[-1], name)
        elif apply_:
            print('add   ', path.split('/')[-1], name, BEL.add_member_variable(bp, name, typ)); changed = True
        else: print('WOULD add', path.split('/')[-1], name)
    if changed:
        BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False); print('compiled + saved', path)
