import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in eas.get_all_level_actors():
    if a.get_actor_label() == 'RevengeTestBall': eas.destroy_actor(a); n += 1
ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(os.path.join(D, 'rv_clean_log.txt'), 'w').write('removed %d, saved %s, gw %s' % (n, ok, unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()))
