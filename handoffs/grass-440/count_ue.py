import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); t = {}
for a in EAS.get_all_level_actors():
    if a.get_actor_label() in ('Env_GrassTall', 'Env_BaseRubble', 'Meadow351'):
        n = sum(c.get_instance_count() for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent))
        m = sum(1 for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent) if c.get_material(0) and '_440' in c.get_material(0).get_name())
        t[a.get_actor_label() + '#' + a.get_name()[-6:]] = (n, m)
print('COUNT', t, 'total', sum(v[0] for v in t.values()))
