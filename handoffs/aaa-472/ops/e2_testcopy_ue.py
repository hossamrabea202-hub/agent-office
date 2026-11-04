# #487 E2 (i5 test only): copy BP_ZombieVariety, BP_JellyShieldAll, BP_HitFeel and a stub wave manager (ZombieReg only) into a NEW temp folder,
# save them, and write ops files that point at the copies. Then run graph_ops_ue.py on each with --apply --nosave. Never on the real assets.
#   py e2_testcopy_ue.py /Game/_i5tmpE2c
import json, os, sys, unreal
F = sys.argv[1]; EA, B_ = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary; HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/ops/'
WMP, ZP = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager', '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
if not EA.does_asset_exist(F + '/WMstub'):
    st = B_.create_blueprint_asset_with_parent(F + '/WMstub', unreal.Actor)
    B_.add_member_variable(st, 'ZombieReg', B_.get_array_type(B_.get_object_reference_type(unreal.load_asset(ZP).generated_class())))
    B_.compile_blueprint(st); EA.save_asset(F + '/WMstub', only_if_is_dirty=False)
for tag in ('variety', 'shield', 'hitfeel'):
    raw = open(HERE + 'ops_E2_%s.json' % tag, encoding='utf-8').read(); bp = json.loads(raw)['bp']; cp = F + '/' + bp.split('/')[-1] + 'c'
    if not EA.does_asset_exist(cp): EA.duplicate_asset(bp, cp); EA.save_asset(cp, only_if_is_dirty=False)
    raw = raw.replace(WMP + '.BP_ZombieWaveManager_C', F + '/WMstub.WMstub_C').replace('"' + bp + '"', '"' + cp + '"')
    out = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'e2test_%s.json' % tag
    open(out, 'w', encoding='utf-8').write(raw); print('copy', cp, '->', out)
