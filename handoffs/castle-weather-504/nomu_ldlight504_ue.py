# temporary lookdev daylight for judging #504 on the castle map (tag LD504). py nomu_ldlight504_ue.py on|off
import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for x in [x for x in EAS.get_all_level_actors() if 'LD504' in [str(t) for t in x.tags]]: EAS.destroy_actor(x)
if 'on' in sys.argv[1:]:
    s = EAS.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(2000, 2000, 5000), unreal.Rotator(roll=0, pitch=-38, yaw=-140))
    s.light_component.set_intensity(8.0); s.light_component.set_editor_property('temperature', 5600.0)
    s.light_component.set_editor_property('use_temperature', True); s.tags = [unreal.Name('LD504')]
    f = EAS.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(2000, 2000, 5000), unreal.Rotator(roll=0, pitch=-20, yaw=40))
    f.light_component.set_intensity(2.0); f.light_component.set_cast_shadows(False); f.tags = [unreal.Name('LD504')]
    f.light_component.set_editor_property('atmosphere_sun_light', False); s.light_component.set_editor_property('atmosphere_sun_light', False)
print('lookdev light', sys.argv[1:])
