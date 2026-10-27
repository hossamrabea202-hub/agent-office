import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
v = open(os.path.join(D, 'pie_slomo_val.txt')).read().strip()
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
unreal.SystemLibrary.execute_console_command(w, 'slomo %s' % v)
open(os.path.join(D, 'pie_slomo.txt'), 'w').write('slomo %s on %s' % (v, w.get_name() if w else None))
