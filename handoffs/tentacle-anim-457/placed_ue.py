# #457 (i5): read-only: every placed component on SK_CorruptedTentacle_01 and how it animates. Aborts in PIE.
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
n = 0
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
        m = c.get_editor_property('skinned_asset')
        if not m or 'Tentacle' not in m.get_name(): continue
        n += 1
        mode = c.get_editor_property('animation_mode')
        ad = c.get_editor_property('animation_data')
        abp = c.get_editor_property('anim_class')
        pp = c.get_editor_property('post_process_anim_blueprint') if hasattr(c, 'post_process_anim_blueprint') else None
        print(n, a.get_actor_label(), a.get_class().get_name(), c.get_name(), str(mode).split('.')[-1],
              ad.anim_to_play.get_name() if ad.anim_to_play else None, 'rate', round(ad.saved_play_rate, 2), 'pos', round(ad.saved_position, 2),
              'loop', ad.saved_looping, 'abp', abp.get_name() if abp else None, 'loc', [round(v) for v in a.get_actor_location().to_tuple()],
              'scale', [round(v, 2) for v in c.get_world_scale().to_tuple()])
print('total', n)
