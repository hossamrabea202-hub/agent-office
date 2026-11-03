import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); n = {}
for a in EAS.get_all_level_actors():
    if a.get_actor_label() not in ('Env_GrassTall', 'Env_BaseRubble', 'Meadow351'): continue
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        m = c.get_material(0); k = (c.get_editor_property('static_mesh').get_name()[:14], m.get_name() if m else None)
        n[k] = n.get(k, 0) + 1
for k, v in sorted(n.items()):
    if 'vcz' in k[0] or 'vlk' in k[0] or 'MWAM' in k[0]: print(v, k)
