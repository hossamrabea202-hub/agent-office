# #487 E2 (i5, read-only): does the live BP_ZombieWaveManager have fix A's ZombieReg?
import unreal
bp = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager')
names = [str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]
print('WM vars', len(names), 'ZombieReg' in names, 'RegHost' in names)
