import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == 'RevengeTestBall': eas.destroy_actor(a)
cls = unreal.load_class(None, '/Game/CastleDefender/Gameplay/Cannon/BP_Cannonball.BP_Cannonball_C')
b = eas.spawn_actor_from_class(cls, unreal.Vector(0, 0, 90000))
b.set_actor_label('RevengeTestBall')
L = ['life %s' % b.get_editor_property('initial_life_span')]
try: b.set_editor_property('initial_life_span', 0.0)
except Exception as e: L.append('life ERR %s' % e)
b.set_actor_enable_collision(False); b.set_actor_hidden_in_game(True)
for c in b.get_components_by_class(unreal.ActorComponent):
    L.append('%s %s' % (c.get_name(), c.get_class().get_name()))
    if isinstance(c, unreal.ProjectileMovementComponent):
        c.set_editor_property('auto_activate', False); c.set_editor_property('initial_speed', 0.0); c.set_editor_property('projectile_gravity_scale', 0.0)
L.append('life now %s' % b.get_editor_property('initial_life_span'))
open(os.path.join(D, 'rv_park_log.txt'), 'w').write('\n'.join(L))
