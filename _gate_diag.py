import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); A = eas.get_all_level_actors(); L = []
gates = [a for a in A if 'gate' in (a.get_actor_label() + a.get_class().get_name()).lower()]
for g in gates:
    o, e = g.get_actor_bounds(False)
    L.append('GATE %s [%s] folder=%s loc=%s ext=%s' % (g.get_actor_label(), g.get_class().get_name(), g.get_folder_path(), o, e))
    for c in g.get_components_by_class(unreal.PrimitiveComponent):
        try: prof = c.get_collision_profile_name()
        except Exception: prof = '?'
        L.append('   %s [%s] coll=%s prof=%s pawn=%s nav=%s' % (c.get_name(), c.get_class().get_name(), c.get_collision_enabled(), prof, c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN), c.get_editor_property('can_ever_affect_navigation')))
main = [g for g in gates if 'control' in g.get_class().get_name().lower() or 'lever' not in g.get_actor_label().lower()]
if gates:
    c0 = gates[0].get_actor_location()
    L.append('--- volumes / nav near gate (15 m)')
    for a in A:
        cn = a.get_class().get_name()
        if any(k in cn for k in ('Volume', 'NavLink', 'NavModifier', 'BlockingVolume', 'TriggerBox')) and (a.get_actor_location() - c0).length() < 1500:
            o, e = a.get_actor_bounds(False); L.append('   %s [%s] loc=%s ext=%s' % (a.get_actor_label(), cn, o, e))
open(r'C:\Users\hossa\Documents\agent-office\_gate_diag.txt', 'w').write('\n'.join(L)); print('GATEDIAG')
