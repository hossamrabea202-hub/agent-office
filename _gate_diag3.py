import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); L = []
for a in eas.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn in ('BP_GateBreachLeaf_C', 'BP_CastleMainGate_C') or a.get_actor_label().startswith('Nav_GateLink'):
        L.append('%s [%s] hidden=%s' % (a.get_actor_label(), cn, a.is_hidden_ed()))
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            try:
                o, e = c.bounds.origin, c.bounds.box_extent
            except Exception:
                o = e = unreal.Vector(0, 0, 0)
            s = '   %s [%s] vis=%s coll=%s pawn=%s origin=(%.0f,%.0f,%.0f) ext=(%.0f,%.0f,%.0f)' % (c.get_name(), c.get_class().get_name(), c.is_visible(), c.get_collision_enabled(), c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN), o.x, o.y, o.z, e.x, e.y, e.z)
            if isinstance(c, unreal.BoxComponent): s += ' boxext=%s' % c.get_unscaled_box_extent()
            L.append(s)
ns = unreal.get_default_object(unreal.NavigationSystemV1) if hasattr(unreal, 'NavigationSystemV1') else None
try: L.append('NAV runtime: %s' % unreal.get_default_object(unreal.RecastNavMesh).get_editor_property('runtime_generation'))
except Exception as e: L.append('NAV runtime ? %s' % e)
for a in eas.get_all_level_actors():
    if a.get_class().get_name() == 'RecastNavMesh':
        try: L.append('NAV actor %s runtime=%s agentR=%s step=%s' % (a.get_actor_label(), a.get_editor_property('runtime_generation'), a.get_editor_property('agent_radius'), a.get_editor_property('agent_max_step_height')))
        except Exception as e: L.append('NAV actor %s %s' % (a.get_actor_label(), e))
open(r'C:\Users\hossa\Documents\agent-office\_gate_diag3.txt', 'w').write('\n'.join(L)); print('GATEDIAG2')
