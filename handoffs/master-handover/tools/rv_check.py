import unreal, os, json
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
GS = unreal.GameplayStatics
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
ids = json.load(open(os.path.join(D, 'rv_ids.json')))
L = []
for c in GS.get_all_actors_of_class(gw, unreal.Actor):
    if c.get_class().get_name() != 'BP_Cannon_C': continue
    k = [x for x in c.get_components_by_class(unreal.ActorComponent) if x.get_class().get_name() == 'BPC_CannonBreak_C']
    hp = k[0].get_editor_property('HP') if k else None
    p = c.get_path_name()
    L.append('%s HP=%s attacker=%s nearest=%s' % (c.get_actor_label(), hp, p == ids['A'][1], p == ids['A'][2]))
unreal.SystemLibrary.execute_console_command(None, 'FlushLog')
open(os.path.join(D, 'rv_check_log.txt'), 'w').write('\n'.join(L))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
