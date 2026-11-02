# #435 (i5): face lookdev. Spawns SM_HeroHead alone (its own materials) + a 0.18 grey ball 200 m above the castle, lit by
# a 5500 K point light in front, renders it at locked exposure, then deletes everything (tag LD435). Nothing saved.
# Also prints the textures the skin material uses.   py lookdev_face435_ue.py <name> [ev=0]
import sys, unreal
sys.path.insert(0, 'C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425')
import lookdev_cap
H = 'C:/Users/hossam.rabea/agent-office/handoffs/black-faces-435/'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); MEL = unreal.MaterialEditingLibrary
name = sys.argv[1] if len(sys.argv) > 1 else 'head'; ev = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
O = unreal.Vector(-3000, 3000, 20000)
skin = unreal.load_asset('/Game/CastleDefender/Characters/Greystone/Characters/Heroes/Greystone/Materials/M_Greystone_Flesh_head')
for t in MEL.get_used_textures(skin):
    print('skin tex', t.get_path_name(), t.blueprint_get_size_x(), t.blueprint_get_size_y(), t.get_editor_property('srgb'))
print('skin usage skel', skin.get_editor_property('used_with_skeletal_mesh'), 'sss profile', skin.get_editor_property('subsurface_profile'))
made = []
try:
    head = EAS.spawn_actor_from_class(unreal.StaticMeshActor, O, unreal.Rotator(0, 0, 0)); made.append(head)
    head.static_mesh_component.set_static_mesh(unreal.load_asset('/Game/CastleDefender/Characters/Knight/SM_HeroHead'))
    SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); hb = unreal.load_asset('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
    for hh in SDS.k2_gather_subobject_data_for_blueprint(hb):
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(hh))
        if o and o.get_name().startswith('HeroHead'):
            print('template', o.get_name(), 'scale', o.get_editor_property('relative_scale3d'), 'rot', o.get_editor_property('relative_rotation'), 'socket', o.get_attach_socket_name(), 'cast_shadow', o.get_editor_property('cast_shadow'))
            head.set_actor_scale3d(o.get_editor_property('relative_scale3d')); head.set_actor_rotation(o.get_editor_property('relative_rotation'), False)
    b = head.get_actor_bounds(False); c, e = b[0], b[1]; print('head bounds centre', c, 'extent', e)
    ball = EAS.spawn_actor_from_class(unreal.StaticMeshActor, c + unreal.Vector(0, e.y * 2.2 + 10, 0), unreal.Rotator()); made.append(ball)
    ball.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Sphere'))
    ball.static_mesh_component.set_material(0, unreal.load_asset('/Game/CastleDefender/Environment/ContactDecals425/M_LD_Grey18_425'))
    ball.set_actor_scale3d(unreal.Vector(0.15, 0.15, 0.15))
    # find the face direction: try both +X and -X, render each
    for sgn, tag in ((1, 'px'), (-1, 'nx'), ):
        L = EAS.spawn_actor_from_class(unreal.PointLight, c + unreal.Vector(sgn * (e.x + 60), -20, 20), unreal.Rotator()); made.append(L)
        lc = L.point_light_component; lc.set_editor_property('intensity', 3000.0); lc.set_editor_property('use_temperature', True)
        lc.set_editor_property('temperature', 5500.0); lc.set_editor_property('attenuation_radius', 600.0)
        lookdev_cap.shot(H + 'ld435_%s_%s.png' % (name, tag), c + unreal.Vector(sgn * (e.x * 3 + 40), 0, 0), c, ev, 40.0)
        EAS.destroy_actor(L); made.remove(L)
    for sgn, tag in ((1, 'py'), (-1, 'ny')):
        L = EAS.spawn_actor_from_class(unreal.PointLight, c + unreal.Vector(-20, sgn * (e.y + 60), 20), unreal.Rotator()); made.append(L)
        lc = L.point_light_component; lc.set_editor_property('intensity', 3000.0); lc.set_editor_property('use_temperature', True)
        lc.set_editor_property('temperature', 5500.0); lc.set_editor_property('attenuation_radius', 600.0)
        lookdev_cap.shot(H + 'ld435_%s_%s.png' % (name, tag), c + unreal.Vector(0, sgn * (e.y * 3 + 40), 0), c, ev, 40.0)
        EAS.destroy_actor(L); made.remove(L)
finally:
    for a in made: EAS.destroy_actor(a)
