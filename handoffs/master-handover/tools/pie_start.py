import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if gw is None:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
    msg = 'requested Simulate'
else:
    msg = 'PIE already running'
open(os.path.join(D, 'pie_start.txt'), 'w').write(msg)
