# #488 (i5, read-only): is the merlon kit in the live session, and where are its pieces placed?
import unreal
EA = unreal.EditorAssetLibrary; F = '/Game/CastleDefender/Environment/Castle/Battlements488'
print('kit folder', EA.does_directory_exist(F), [a.split('/')[-1].split('.')[0] for a in EA.list_assets(F, False)] if EA.does_directory_exist(F) else [])
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); n = 0
for a in sub.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.static_mesh
        if m and '488' in m.get_name():
            n += 1
            if n <= 60:
                t = c.get_world_transform(); print(a.get_actor_label(), m.get_name(), [round(x) for x in (t.translation.x, t.translation.y, t.translation.z)], round(t.rotation.rotator().yaw), str(a.get_folder_path()))
print('pieces placed', n)
labs = sorted({a.get_actor_label() for a in sub.get_all_level_actors() if 'curtain' in a.get_actor_label().lower() and 'masonry' in str(a.get_folder_path()).lower()})
print('curtain masonry actors', len(labs), labs[:20])
