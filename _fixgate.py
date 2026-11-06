import unreal, _mh
EAL = unreal.EditorAssetLibrary; L = []
IGN = unreal.CollisionResponseType.ECR_IGNORE; PAWN = unreal.CollisionChannel.ECC_PAWN
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
def fix_bp(name, pred):
    p = _mh.find(name); bp = unreal.load_asset(p); n = 0
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
        if isinstance(o, unreal.PrimitiveComponent) and pred(o):
            o.set_collision_response_to_channel(PAWN, IGN); o.set_editor_property('can_ever_affect_navigation', False); n += 1
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_asset(p); L.append('%s template comps fixed: %d' % (name, n))
fix_bp('BP_CastleMainGate', lambda o: o.get_name().startswith('LeafCol'))
fix_bp('BP_GateBreachLeaf', lambda o: isinstance(o, unreal.SkeletalMeshComponent))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); m = 0
for a in eas.get_all_level_actors():
    cn = a.get_class().get_name()
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        if (cn == 'BP_CastleMainGate_C' and c.get_name().startswith('LeafCol')) or (cn == 'BP_GateBreachLeaf_C' and isinstance(c, unreal.SkeletalMeshComponent)):
            c.modify(); c.set_collision_response_to_channel(PAWN, IGN); c.set_editor_property('can_ever_affect_navigation', False); m += 1
            L.append('  placed %s.%s pawn=%s' % (a.get_actor_label(), c.get_name(), c.get_collision_response_to_channel(PAWN)))
L.append('placed comps fixed: %d' % m)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(w, 'RebuildNavigation')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); L.append('nav rebuild started, saved')
open(r'C:\Users\hossa\Documents\agent-office\_fixgate.txt', 'w').write('\n'.join(L)); print('FIXGATE', L)
