# Read-only (#485): head bone ref pose, HeroHead / Gorget / KnightMesh templates. No spawn, no save.
import unreal
hero=unreal.load_asset('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);L=unreal.SubobjectDataBlueprintFunctionLibrary
comps={}
for h in sub.k2_gather_subobject_data_for_blueprint(hero):
    d=L.get_data(h);o=L.get_object(d)
    if o: comps[str(L.get_variable_name(d))]=(o,h,d)
def xf(t):
    r=t.rotation.rotator();return [round(x,4) for x in (t.translation.x,t.translation.y,t.translation.z,r.roll,r.pitch,r.yaw,t.scale3d.x)]
for n in ('Mesh','KnightMesh','HeroHead','GorgetNeck','GorgetSpine','ChestRemnant','HeaterShield'):
    o,h,d=comps[n]
    print(n,o.get_class().get_name(),'rel',xf(o.get_editor_property('relative_transform')) if False else (o.get_editor_property('relative_location'),o.get_editor_property('relative_rotation'),o.get_editor_property('relative_scale3d')))
    print('  attach',o.get_editor_property('attach_parent') if False else '', 'socket',o.get_attach_socket_name() if hasattr(o,'get_attach_socket_name') else '?','vis',o.get_editor_property('visible'),'hiddenGame',o.get_editor_property('hidden_in_game'))
    m=None
    for p in ('skeletal_mesh_asset','skeletal_mesh','static_mesh'):
        try:
            m=o.get_editor_property(p)
            if m: break
        except Exception: pass
    print('  mesh',m)
    if m:
        try:
            b=m.get_bounds(); print('  bounds origin',b.origin,'ext',b.box_extent)
        except Exception as e: print('  b err',e)
        try:
            bb=m.get_bounding_box(); print('  bbox',bb.min,bb.max)
        except Exception: pass
    if n in('KnightMesh',): print('  mats',[str(x) for x in o.get_materials()])
K=unreal.load_asset('/Game/ShadowKight/Mesh/ShadowknightUE_SK')
sk=K.get_editor_property('skeleton');print('skeleton',sk)
print('AnimPoseExtensions', hasattr(unreal,'AnimPoseExtensions'))
pose=unreal.AnimPoseExtensions.get_reference_pose(sk)
sp=unreal.AnimPoseSpaces.WORLD
for b in ('pelvis','neck_01','head','upperarm_l','foot_l'):
    t=unreal.AnimPoseExtensions.get_bone_pose(pose,b,sp)
    q=t.rotation;print(b,xf(t),'quat',[round(x,5) for x in (q.x,q.y,q.z,q.w)])
print('mats',[ (str(m.material_slot_name),m.material_interface.get_name() if m.material_interface else None) for m in K.get_editor_property('materials')])
print('b',K.get_bounds().origin,K.get_bounds().box_extent)
