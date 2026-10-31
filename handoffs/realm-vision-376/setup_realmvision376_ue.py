# #376 Realm vision, editor setup (adjustedfilm, 2026-10-31 late). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/realm-vision-376/setup_realmvision376_ue.py" --check            READ-ONLY: the bubble, its mesh, collision,
#                                                                                       a two-sided trace test, its material scalars
#   py ".../setup_realmvision376_ue.py" [--dry-run]                                     makes BP_RealmVision (+ PostProcess "Vision")
#   py ".../setup_realmvision376_ue.py" --place [--dry-run]                             AFTER the BPVar + graph paste and Compile:
#                                                                                       places Realm_Vision, links it to the bubble
# The bubble (Realm_Bubble_Owner, its mesh, material, transform) is only READ. No decal is touched.
# Writes realmvision376_<mode>.txt next to itself.
import os, sys, unreal

A = sys.argv[1:]
DRY, CHECK, PLACE = '--dry-run' in A, '--check' in A, '--place' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\realm-vision-376'
DEST = '/Game/CastleDefender/Gameplay/Realm'
BP = DEST + '/BP_RealmVision'
BUBBLE_LABEL, LABEL, TAG = 'Realm_Bubble_Owner', 'Realm_Vision', 'laptop2_realm'
EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#376 realm vision %s%s' % ('--check' if CHECK else '--place' if PLACE else 'setup', ' (DRY RUN)' if DRY else '')]

# inside look: the Master's start values (owner tunes them on Realm_Vision -> Vision -> Post Process Settings, live in PIE too)
LOOK = [('color_saturation', unreal.Vector4(0.78, 0.86, 0.80, 1.0)), ('color_contrast', unreal.Vector4(1.12, 1.12, 1.12, 1.0)),
        ('color_gain', unreal.Vector4(0.92, 1.04, 0.94, 1.0)), ('color_gamma', unreal.Vector4(0.97, 1.0, 1.02, 1.0)),
        ('scene_color_tint', unreal.LinearColor(0.86, 1.0, 0.88, 1.0)), ('scene_fringe_intensity', 1.6), ('vignette_intensity', 0.75),
        ('bloom_intensity', 1.6), ('film_grain_intensity', 0.25), ('auto_exposure_bias', -0.35)]


def bubble():
    a = [x for x in EAS.get_all_level_actors() if x.get_actor_label() == BUBBLE_LABEL]
    if not a: log.append('NO actor labelled %s in the open level' % BUBBLE_LABEL); return None, None
    ms = list(a[0].get_components_by_class(unreal.StaticMeshComponent))
    log.append('bubble %s (%s), %d static mesh component(s): %s' % (BUBBLE_LABEL, a[0].get_class().get_name(), len(ms),
               [(m.get_name(), m.get_editor_property('static_mesh').get_name() if m.get_editor_property('static_mesh') else None) for m in ms]))
    return a[0], (ms[0] if ms else None)


def trace(c, s, e):
    """ComponentLineTrace, complex. 5.3 Python returns None on a miss (bool return + outs), else the outs."""
    r = c.line_trace_component(s, e, True, False, False)
    if r is None or r is False: return None
    if isinstance(r, tuple):
        if r and isinstance(r[0], bool):
            if not r[0]: return None
            r = r[1:]
        return next((v for v in r if isinstance(v, unreal.Vector)), s)
    return s


def two_sided_test(c):
    """hit the top of the membrane from above, then trace back out from just inside: a hit = the trace sees back faces."""
    org, box, _r = unreal.SystemLibrary.get_component_bounds(c)
    top = unreal.Vector(org.x, org.y, org.z + box.z + 500.0)
    p = trace(c, top, org)
    if p is None:
        p = trace(c, top, unreal.Vector(org.x, org.y, org.z - box.z - 500.0))
    if p is None: log.append('two-sided test: no hit from above (complex collision missing?)'); return None
    back = trace(c, p - unreal.Vector(0, 0, 5.0), p + unreal.Vector(0, 0, 200.0))
    log.append('two-sided test: front hit at z %.0f; trace back out from inside %s -> TwoSided = %s' % (p.z, 'HIT' if back else 'missed', bool(back)))
    return bool(back)


def report_bubble(a, c):
    if not c: log.append('no StaticMeshComponent on the bubble'); return None
    sm = c.get_editor_property('static_mesh')
    try:
        bs = sm.get_editor_property('body_setup')
        log.append('collision: complexity %s, double sided %s, profile %s' % (bs.get_editor_property('collision_trace_flag'),
                   bs.get_editor_property('double_sided_geometry'), c.get_collision_profile_name()))
    except Exception as e:
        log.append('collision: body setup unreadable (%s)' % e)
    org, box, _r = unreal.SystemLibrary.get_component_bounds(c)
    log.append('bounds origin %s, half size %s' % (org, box))
    mat = c.get_material(0)
    log.append('material 0: %s' % (mat.get_path_name() if mat else None))
    try:
        for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat):
            v = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mat, n) if isinstance(mat, unreal.MaterialInstance) \
                else unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(mat, n)
            log.append('  scalar %-24s %s' % (n, v))
    except Exception as e:
        log.append('  (scalars unreadable: %s)' % e)
    return two_sided_test(c)


if CHECK:
    a, c = bubble()
    if a: report_bubble(a, c)

elif PLACE:
    a, c = bubble()
    two = report_bubble(a, c) if a else None
    cls = unreal.load_class(None, BP + '.BP_RealmVision_C') if EAL.does_asset_exist(BP) else None
    if not cls: log.append('BP_RealmVision missing: run the setup without --place first')
    elif a:
        old = [x for x in EAS.get_all_level_actors() if x.get_actor_label() == LABEL]
        log.append(('reuse ' if old else 'place ') + LABEL)
        if not DRY:
            v = old[0] if old else EAS.spawn_actor_from_class(cls, a.get_actor_location(), unreal.Rotator(0, 0, 0))
            v.set_actor_label(LABEL); v.tags = [unreal.Name(TAG)]
            v.set_editor_property('Bubble', a)
            if two is not None: v.set_editor_property('TwoSided', two)
            log.append('  Bubble = %s, TwoSided = %s' % (a.get_actor_label(), v.get_editor_property('TwoSided')))
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

else:
    if EAL.does_asset_exist(BP):
        bp = unreal.load_asset(BP); log.append('reusing ' + BP)
    else:
        log.append('create ' + BP); bp = None
        if not DRY:
            f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
            bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_RealmVision', DEST, unreal.Blueprint, f)
    if bp:
        hs = sds.k2_gather_subobject_data_for_blueprint(bp)
        by = {str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))): h for h in hs}
        if 'Vision' in by: h = by['Vision']
        else:
            h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=unreal.PostProcessComponent, blueprint_context=bp))
            if not fail.is_empty(): raise RuntimeError('add Vision: %s' % fail)
            sds.rename_subobject(h, unreal.Text('Vision')); log.append('  + PostProcess Vision')
        pp = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
        pp.set_editor_property('unbound', True); pp.set_editor_property('priority', 5.0); pp.set_editor_property('blend_weight', 0.0)
        s = pp.get_editor_property('settings')
        for k, v in LOOK:
            try:
                s.set_editor_property('override_' + k, True); s.set_editor_property(k, v); log.append('  %s = %s' % (k, v))
            except Exception as e:
                log.append('  (%s skipped: %s)' % (k, e))
        pp.set_editor_property('settings', s)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_asset(BP)
    log.append('Next: VARIABLES_BPVar.txt (8 lines) + BP_RealmVision_graph.txt paste, Compile, then --place.')

out = '\n'.join(log)
open(os.path.join(HERE, 'realmvision376_%s.txt' % ('check' if CHECK else 'place' if PLACE else 'setup')), 'w').write(out)
unreal.log(out); print(out)
