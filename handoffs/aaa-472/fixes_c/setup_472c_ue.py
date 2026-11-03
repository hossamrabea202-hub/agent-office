# #472 fix C step 1 (Master, editor idle): BP_Zombie variables + additive flinch clips and montages (new assets; the source clips are not touched). Safe to re-run.
#   py setup_472c_ue.py --dry-run | --apply | --revert     (--root <folder>: i5 tests in a temporary folder and skips the variables)
import sys, unreal
ARGS = sys.argv[1:]
ROOT = ARGS[ARGS.index('--root') + 1] if '--root' in ARGS else '/Game/CastleDefender/Characters/Enemies/Zombie/Anim/Hit'
TEST = '--root' in ARGS
P_Z = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
E, L, BEL = unreal.EditorAssetLibrary, unreal.AnimationLibrary, unreal.BlueprintEditorLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()
by = {str(d.asset_name): d for d in AR.get_assets(unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'AnimSequence')], package_paths=['/Game/CastleDefender/Characters/Enemies/Zombie'], recursive_paths=True))}
FLINCH = [('Front', 'ZA_Taking_Damage_B'), ('Back', 'ZA_Taking_Damage_C')]      # B's hips jolt back (hit from the front), C's jolt forward
apply_, revert = '--apply' in ARGS, '--revert' in ARGS
for side, src in FLINCH:
    seq, mon = ROOT + '/AS_ZFlinch_' + side, ROOT + '/AM_ZFlinch_' + side
    if revert:
        for p in (mon, seq):
            if E.does_asset_exist(p): print('delete', p, E.delete_asset(p))
        continue
    if E.does_asset_exist(mon): print('there ', mon); continue
    if not apply_: print('WOULD make', seq, mon, 'from', src); continue
    if not E.does_asset_exist(seq):
        if not E.duplicate_asset(by[src].get_asset().get_path_name().split('.')[0], seq): raise SystemExit('duplicate failed ' + seq)
    a = unreal.load_asset(seq)
    L.set_additive_animation_type(a, unreal.AdditiveAnimationType.AAT_LOCAL_SPACE_BASE)
    L.set_additive_base_pose_type(a, unreal.AdditiveBasePoseType.ABPT_LOCAL_ANIM_FRAME)     # own first frame: only the jolt is added
    E.save_asset(seq, only_if_is_dirty=False)
    f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', a); f.set_editor_property('target_skeleton', a.get_editor_property('skeleton'))
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset('AM_ZFlinch_' + side, ROOT, unreal.AnimMontage, f)
    bi = m.get_editor_property('blend_in'); bi.set_editor_property('blend_time', 0.05); m.set_editor_property('blend_in', bi)
    bo = m.get_editor_property('blend_out'); bo.set_editor_property('blend_time', 0.15); m.set_editor_property('blend_out', bo)
    E.save_asset(mon, only_if_is_dirty=False)
    print('made', mon, L.get_additive_animation_type(a), L.get_additive_base_pose_type(a), 'len', round(m.get_play_length(), 2), 'slot', [str(t.get_editor_property('slot_name')) for t in m.get_editor_property('slot_anim_tracks')])
if not TEST:
    bp = unreal.load_asset(P_Z); have = [str(n) for n in BEL.list_member_variable_names(bp, False)]; changed = False
    for name, typ in [('ThinkTick', BEL.get_basic_type_by_name('int')), ('LastFlinchAt', BEL.get_basic_type_by_name('real'))]:
        if revert: print('keep  ', name, '(harmless, delete by hand if wanted)')
        elif name in have: print('there ', name)
        elif apply_: print('add   ', name, BEL.add_member_variable(bp, name, typ)); changed = True
        else: print('WOULD add', name)
    if changed: BEL.compile_blueprint(bp); E.save_asset(P_Z, only_if_is_dirty=False); print('compiled + saved BP_Zombie')
