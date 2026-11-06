import unreal
EAL=unreal.EditorAssetLibrary; BEL=unreal.BlueprintEditorLibrary
SDS=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L=unreal.SubobjectDataBlueprintFunctionLibrary
HERO='/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
hero=unreal.load_asset(HERO)
for h in SDS.k2_gather_subobject_data_for_blueprint(hero):
    d=SDS.k2_find_subobject_data_from_handle(h); o=L.get_object(d)
    if o is None: continue
    try: v=o.get_editor_property('MaxHP')
    except Exception: continue
    print('comp %s (%s) MaxHP was %s'%(L.get_variable_name(d),o.get_class().get_name(),v))
    o.set_editor_property('MaxHP',250.0)
    print('  now %s'%o.get_editor_property('MaxHP'))
BEL.compile_blueprint(hero); print('saved hero', EAL.save_asset(HERO))
# also level instances of the hero
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for c in a.get_components_by_class(unreal.ActorComponent):
        try:
            v=c.get_editor_property('MaxHP')
            if v!=250.0 and 'Infection' in c.get_class().get_name(): print('level actor %s comp MaxHP %s -> 250'%(a.get_actor_label(),v)); c.set_editor_property('MaxHP',250.0)
        except Exception: pass
exec(open(r'C:/Users/hossa/Documents/agent-office/_bz.py').read())
