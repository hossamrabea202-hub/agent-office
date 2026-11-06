# Inner shell (owner 00:49): a second, nearly invisible bubble inside the owner's bubble that carries the deep layers.
# Same mesh (owner's SM_RealmBubbleHi, not edited), 94% scale, centred on the outer bubble, attached to it.
import unreal, sys
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L=[]
try:
    acts=E.get_all_level_actors()
    for a in acts:
        if a.get_actor_label()=='Realm_Bubble_Inner': E.destroy_actor(a)
    bub=[a for a in acts if a.get_actor_label()=='Realm_Bubble_Owner'][0]
    outer_mi=bub.static_mesh_component.get_material(0)
    S=0.94
    # MIs: inner = deep layers only, outer = surface layers only
    base='/Game/CastleDefender/Realm/MI_RealmBubble3_Dream'
    ip='/Game/CastleDefender/Realm/MI_RealmBubble3_Inner'
    if not EAL.does_asset_exist(ip): EAL.duplicate_asset(base,ip)
    imi=unreal.load_asset(ip)
    inner_vals=[('OpacityHead',0.0),('OpacityRim',0.06),('FilmGlow',0.12),('VortexIntensity',0.0),('VortexOpacity',0.0),
        ('WormIntensity2',0.0),('WormOpacity',0.0),('PulseIntensity',0.0),('PulseOpacity',0.0),('Layer6_Sheen',0.0),('Layer9_Seam',0.0),
        ('CellIntensity',0.45),('CellOpacity',0.35),('CellDepth',0.0),('Layer7_Veins',0.7),('VeinDepth',120.0),('Layer4_Marble',0.18),('MarbleDepth',0.0),
        ('Layer5_Motes',3.0),('Layer8_Aurora',0.5)]
    for n,v in inner_vals: MEL.set_material_instance_scalar_parameter_value(imi,n,v)
    MEL.update_material_instance(imi); EAL.save_asset(ip)
    omi=outer_mi
    if 'Dream' in omi.get_name() and 'Inner' not in omi.get_name():
        for n,v in [('CellIntensity',0.0),('CellOpacity',0.0),('Layer7_Veins',0.0),('Layer4_Marble',0.08),('Layer8_Aurora',0.0),('Layer5_Motes',0.0)]:
            MEL.set_material_instance_scalar_parameter_value(omi,n,v)
        MEL.update_material_instance(omi); EAL.save_asset(omi.get_path_name().split('.')[0]); L.append('outer MI: surface layers only')
    # spawn inner shell
    tr=bub.get_actor_transform()
    o,e=bub.get_actor_bounds(False)
    inner=E.spawn_actor_from_class(unreal.StaticMeshActor, bub.get_actor_location(), bub.get_actor_rotation())
    inner.set_actor_label('Realm_Bubble_Inner'); inner.tags=[unreal.Name('laptop2_realm'),unreal.Name('RealmDream')]
    smc=inner.static_mesh_component
    smc.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    smc.set_static_mesh(bub.static_mesh_component.static_mesh); smc.set_material(0,imi)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); smc.set_editor_property('cast_shadow',False)
    inner.set_actor_scale3d(bub.get_actor_scale3d()*S)
    o2,e2=inner.get_actor_bounds(False)
    inner.set_actor_location(inner.get_actor_location()+(o-o2), False, False)       # centre it inside the outer skin
    inner.attach_to_actor(bub,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
    L.append('inner shell at %s scale %s'%(inner.get_actor_location(),inner.get_actor_scale3d()))
    L.append('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-600:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
