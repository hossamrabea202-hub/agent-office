import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); w=unreal.EditorLevelLibrary.get_editor_world()
M=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
NS=unreal.load_asset('/Game/CastleDefender/Environment/Tentacles/MI_CorruptedTentacle_NoStretch')
SK='/Game/CastleDefender/Environment/Tentacles/M_CorruptedTentacle_Ripple2'
for a in E.get_all_level_actors():
    if not (isinstance(a, unreal.SkeletalMeshActor) and 'CorruptedTentacle' in a.get_actor_label()): continue
    c=a.skeletal_mesh_component; mats=c.get_materials(); a.modify(); c.modify()
    for i,m in enumerate(mats):
        if m and m.get_path_name().split('.')[0]==SK: c.set_material(i, NS)
        if m and 'JellyShell' in m.get_name():
            s=abs(a.get_actor_scale3d().x); old=M.get_material_instance_scalar_parameter_value(m,'TentScale')
            if abs(old-s)>0.01:
                M.set_material_instance_scalar_parameter_value(m,'TentScale',s); M.update_material_instance(m); EAL.save_asset(m.get_path_name().split('.')[0])
            print(a.get_actor_label(), m.get_name(), 'TentScale', round(old,3), '->', s)
# realm pieces that sat on tentacle T_5 -> ground (by name; ignore tentacles, fog, bubble)
NAMES=['Realm_Gate_Torch_1','Realm_Wall_015','Realm_BlobMine_10','Realm_BlobMine_08','Realm_Gate_Tower_1','Realm_Wall_014']
SKIP=('Tentacle','Fog','Dome','Bubble')
L={a.get_actor_label():a for a in E.get_all_level_actors()}
for n in NAMES:
    a=L[n]; p=a.get_actor_location(); ign=[a]; z=None
    for _ in range(20):
        h=unreal.SystemLibrary.line_trace_single(w, unreal.Vector(p.x,p.y,30000), unreal.Vector(p.x,p.y,-30000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ign, unreal.DrawDebugTrace.NONE, True)
        t=h.to_tuple() if h else None
        if not t or not t[0] or not t[9]: break
        lab=t[9].get_actor_label()
        if any(k in lab for k in SKIP) or t[9].get_class().get_name()!='Landscape' and 'Landscape' not in t[9].get_class().get_name(): ign.append(t[9]); continue
        z=t[4].z; break
    if z is not None:
        a.modify(); a.set_actor_location(unreal.Vector(p.x,p.y,z), False, False)
    print(n, 'z', round(p.z), '->', z)
print('save', unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
