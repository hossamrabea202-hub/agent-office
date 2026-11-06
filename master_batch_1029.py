_gm=[a for a in EAS.get_all_level_actors() if isinstance(a,unreal.DecalActor) and a.get_actor_label() in ('GateMudPath',)][0]
_gm.get_component_by_class(unreal.DecalComponent).set_visibility(False); print('HIDGM')

