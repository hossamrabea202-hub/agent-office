import unreal
L=lambda n: unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/'+n).generated_class()
N=L('BP_NoticeHUD')
for n in ['BP_ArmoryHUD','BP_ZombieHUD','BP_SkillTreeHUD','BP_QueueHUD','BP_BarracksHUD']:
    try: print(n, unreal.MathLibrary.class_is_child_of(N, L(n)))
    except Exception as e: print(n,'ERR',e)
