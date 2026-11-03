# #472 fix B step 1 (Master, editor idle): one montage per zombie death clip, blend in 0.15 s, NO auto blend out, so the corpse holds its last pose
# inside ABP_Zombie instead of leaving AnimBP mode with a PlayAnimation pop. New assets only; the clips are not touched. Safe to re-run.
#   py make_death_montages_ue.py --dry-run | --apply | --revert        (--root <folder>: i5 tests in a temporary folder)
import sys, unreal
ARGS = sys.argv[1:]
ROOT = ARGS[ARGS.index('--root') + 1] if '--root' in ARGS else '/Game/CastleDefender/Characters/Enemies/Zombie/Anim/Death'
ANIMS = '/Game/CastleDefender/Characters/Enemies/Zombie/Anims/'
CLIPS = ['ZA_Laying_Idle_B', 'A_Death', 'ZA_Burst_A', 'ZA_Burst_B', 'ZA_Burst_C', 'ZA_Burst_D', 'ZA_Burst_E', 'ZA_Burst_F', 'ZA_Burst_G', 'ZA_Burst_H', 'ZA_Burst_I', 'ZA_Burst_K']
E = unreal.EditorAssetLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()
by = {str(d.asset_name): d for d in AR.get_assets(unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'AnimSequence')], package_paths=['/Game/CastleDefender/Characters/Enemies/Zombie'], recursive_paths=True))}
for c in CLIPS:
    p = ROOT + '/AM_ZDeath_' + c
    if '--revert' in ARGS:
        if E.does_asset_exist(p): print('delete', p, E.delete_asset(p))
        continue
    if c not in by: raise SystemExit('clip missing: ' + c)
    if E.does_asset_exist(p): print('there ', p); continue
    if '--apply' not in ARGS: print('WOULD make', p); continue
    clip = by[c].get_asset()
    f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', clip); f.set_editor_property('target_skeleton', clip.get_editor_property('skeleton'))
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset('AM_ZDeath_' + c, ROOT, unreal.AnimMontage, f)
    bi = m.get_editor_property('blend_in'); bi.set_editor_property('blend_time', 0.15); m.set_editor_property('blend_in', bi)
    m.set_editor_property('enable_auto_blend_out', False)
    E.save_asset(p, only_if_is_dirty=False)
    print('made', p, m.get_editor_property('enable_auto_blend_out'), m.get_editor_property('blend_in').get_editor_property('blend_time'), 'len', round(m.get_play_length(), 2), 'slot', [str(t.get_editor_property('slot_name')) for t in m.get_editor_property('slot_anim_tracks')])
