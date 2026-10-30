# #219 (checkking, 2026-10-30 night): the hero can climb onto the big boulder in the courtyard (near the barrels).
# Select that rock (or several rocks) in the level, then run:
#   py "<repo>/handoffs/courtyard-rock-219/fix_rock_219.py"
# For every StaticMeshComponent of the selected actors:
#   CanCharacterStepUpOn = No            (the capsule can't step onto it)
#   WalkableSlopeOverride = Unwalkable   (no surface of it counts as floor: the hero slides off instead of standing)
# Collision stays as it is (the rock still blocks). Nothing is selected -> it lists the 10 biggest rock-like meshes
# within 40 m of the PlayerStart so you can pick the right one. Save the map afterwards.
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sel = eas.get_selected_level_actors()
if not sel:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ps = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    origin = ps[0].get_actor_location() if ps else unreal.Vector(0, 0, 0)
    rows = []
    for a in eas.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor): continue
        sm = a.static_mesh_component.static_mesh
        n = (sm.get_name() if sm else '').lower()
        if not any(k in n for k in ('rock', 'boulder', 'stone', 'cliff')): continue
        d = (a.get_actor_location() - origin).length()
        if d > 4000: continue
        o, ext = a.get_actor_bounds(False)
        rows.append((ext.x * ext.y * ext.z, d, a.get_actor_label(), n))
    rows.sort(reverse=True)
    unreal.log('#219: nothing selected. Biggest rock-like meshes within 40 m of the PlayerStart (label, mesh, distance cm):')
    for v, d, lab, n in rows[:10]: unreal.log('   %s  %s  %.0f' % (lab, n, d))
else:
    done = []
    for a in sel:
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.modify()
            c.set_editor_property('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO)
            bi = c.get_editor_property('body_instance')
            ov = unreal.WalkableSlopeOverride()
            ov.set_editor_property('walkable_slope_behavior', unreal.WalkableSlopeBehavior.WALKABLE_SLOPE_UNWALKABLE)
            try:
                c.set_walkable_slope_override(ov)
            except Exception:
                bi.set_editor_property('walkable_slope_override', ov); c.set_editor_property('body_instance', bi)
        done.append(a.get_actor_label())
    unreal.log('#219: no step-up + unwalkable on %s. Save the map (Ctrl+S).' % ', '.join(done))
