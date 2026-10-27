import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
open(os.path.join(D, 'pie_end.txt'), 'w').write('ended')
