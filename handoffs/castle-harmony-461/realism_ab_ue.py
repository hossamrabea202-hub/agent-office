# Card #486 "castle reads cartoonish" (i5, 2026-11-04): same camera, one change at a time, real viewport shots. Nothing is saved; settings + materials go back at the end.
#   py realism_ab_ue.py            all variants at all spots, into Saved/Screenshots/ (takes a few minutes; Lumen settles between shots). Then push or post the images
#   py realism_ab_ue.py --dump     only prints the post process, sun, sky and fog values
#   py realism_ab_ue.py --test     one 960x540 shot, for i5
# Variants: A today | B real-time soft shadows (VSM) instead of 1024 cascades | C Lumen sees each mesh + full probes | D no limewash coat | E full render resolution | F B+C+D+E together.
# Editor idle, not in Play, viewport set to Lit. Aborts in PIE.
import sys, unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if ues.get_game_world(): print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]; w = ues.get_editor_world(); MEL = unreal.MaterialEditingLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
def dump():
    PP = ('auto_exposure_method', 'auto_exposure_bias', 'auto_exposure_min_brightness', 'auto_exposure_max_brightness', 'bloom_intensity', 'vignette_intensity', 'film_grain_intensity', 'film_slope', 'film_toe', 'film_shoulder', 'color_saturation', 'color_contrast', 'color_gamma', 'white_temp', 'ambient_occlusion_intensity', 'local_exposure_contrast_scale', 'lumen_scene_lighting_quality', 'lumen_final_gather_quality', 'lumen_reflection_quality', 'motion_blur_amount', 'depth_of_field_focal_distance', 'sharpen')
    for a in actors:
        if isinstance(a, unreal.PostProcessVolume):
            s = a.get_editor_property('settings'); out = {}
            for k in PP:
                try:
                    if s.get_editor_property('override_' + k): out[k] = str(s.get_editor_property(k))
                except Exception: pass
            print('PPV', a.get_actor_label(), 'unbound', a.get_editor_property('unbound'), out)
        for cls, keys in ((unreal.DirectionalLightComponent, ('intensity', 'temperature', 'light_source_angle', 'contact_shadow_length', 'cast_shadows', 'use_temperature')), (unreal.SkyLightComponent, ('intensity', 'real_time_capture', 'lower_hemisphere_color')),
                          (unreal.ExponentialHeightFogComponent, ('fog_density', 'fog_height_falloff', 'volumetric_fog', 'start_distance', 'fog_inscattering_luminance'))):
            for c in a.get_components_by_class(cls):
                o = {}
                for k in keys:
                    try: o[k] = str(c.get_editor_property(k))
                    except Exception: pass
                print(cls.__name__, a.get_actor_label(), o)
dump()
if '--dump' in A: raise SystemExit
LIME = []
C = '/Game/CastleDefender/Shared/Materials/Castle/'
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')):
    if str(ad.asset_name) in ('MI_Castle_Stone_Harmony461', 'MI_CastleAshlar', 'MI_CastleAshlar_Trim'):
        m = unreal.load_asset(str(ad.package_name)); LIME.append((m, MEL.get_material_instance_scalar_parameter_value(m, 'LimewashAmount')))
print('limewash materials:', [(m.get_name(), v) for m, v in LIME])
BASE = {'r.Shadow.Virtual.Enable': '0', 'r.Lumen.TraceMeshSDFs': '0', 'r.Lumen.ScreenProbeGather.DownsampleFactor': '32', 'r.ScreenPercentage': '67'}
VSM = {'r.Shadow.Virtual.Enable': '1'}; SDF = {'r.Lumen.TraceMeshSDFs': '1', 'r.Lumen.ScreenProbeGather.DownsampleFactor': '16'}; RES = {'r.ScreenPercentage': '100'}
VARIANTS = [('A_today', {}, False), ('B_vsm', VSM, False), ('C_lumen', SDF, False), ('D_nolime', {}, True), ('E_res100', RES, False), ('F_all', dict(VSM, **dict(SDF, **RES)), True)]
SPOTS = [('gate', (-1000, 1750, 260), (40, 1750, 450)), ('wall', (-700, 300, 200), (160, 900, 450)), ('keep', (1100, 1750, 170), (2600, 1750, 420))]
if '--test' in A: VARIANTS = VARIANTS[:1]; SPOTS = SPOTS[:1]
W, H = (960, 540) if '--test' in A else (1600, 900)
def cvars(d):
    for k, v in dict(BASE, **d).items(): unreal.SystemLibrary.execute_console_command(w, '%s %s' % (k, v))
def lime(off):
    if '--test' in A: return                        # i5 runs inside the Multi-User sandbox: no MI edits there
    for m, v in LIME: MEL.set_material_instance_scalar_parameter_value(m, 'LimewashAmount', 0.0 if off else v); MEL.update_material_instance(m)
jobs = [(v, s) for v in VARIANTS for s in SPOTS]; state = {'i': 0, 'wait': 0, 'h': None}
def restore():
    cvars({}); lime(False); unreal.unregister_slate_post_tick_callback(state['h']); print('REALISM done, %d shots in Saved/Screenshots, settings + materials back' % len(jobs))
def tick(dt):
    if state.get('busy'): return                    # an MI edit can pump Slate (Multi-User autosave) and re-enter this tick: froze i5 with a RecursionError
    if state['wait'] > 0: state['wait'] -= 1; return
    if state['i'] >= len(jobs): state['busy'] = True; restore(); return
    (name, cv, nolime), (spot, cam, tgt) = jobs[state['i']]
    if state.get('armed') != state['i']:
        state['busy'] = True; state['armed'] = state['i']
        try:
            cvars(cv); lime(nolime); c, t = unreal.Vector(*cam), unreal.Vector(*tgt)
            ues.set_level_viewport_camera_info(c, unreal.MathLibrary.find_look_at_rotation(c, t)); state['wait'] = 150
        finally: state['busy'] = False
        return
    state['i'] += 1; state['wait'] = 90; state['busy'] = True          # count first: the screenshot call can pump Slate and re-enter this tick
    try:
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot %dx%d filename=realism486_%s_%s' % (W, H, spot, name)); print('shot', spot, name)
    finally: state['busy'] = False
state['h'] = unreal.register_slate_post_tick_callback(tick)
