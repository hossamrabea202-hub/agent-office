import unreal
hero = unreal.load_asset('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
out = []
for h in sub.k2_gather_subobject_data_for_blueprint(hero):
    o = L.get_object(L.get_data(h))
    if isinstance(o, unreal.StaticMeshComponent):
        tags = [str(t) for t in o.get_editor_property('component_tags') if str(t).startswith('ObsK')]
        if tags: m = o.get_editor_property('static_mesh'); out.append((tags[0], m.get_name() if m else None))
print('OBSK', len(out), sorted(out))
