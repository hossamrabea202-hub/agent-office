import unreal, _mh
L = []
for name in ('BP_CastleMainGate', 'BP_CastleGateControl', 'BP_GateBreachLeaf'):
    p = _mh.find(name)
    if not p: L.append(name + ' not found'); continue
    bp = unreal.load_asset(p)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    L.append('== ' + name)
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        d = sds.k2_find_subobject_data_from_handle(h); o = SDL.get_object(d)
        if o is None or not isinstance(o, unreal.SceneComponent): continue
        par = o.get_attach_parent()
        extra = ''
        if isinstance(o, unreal.PrimitiveComponent): extra = ' coll=%s prof=%s' % (o.get_collision_enabled(), o.get_collision_profile_name())
        L.append('   %s [%s] parent=%s inherited=%s%s' % (SDL.get_variable_name(d), o.get_class().get_name(), par.get_name() if par else None, SDL.is_inherited_component(d), extra))
open(r'C:\Users\hossa\Documents\agent-office\_gate_diag6.txt', 'w').write('\n'.join(L)); print('GD5')
