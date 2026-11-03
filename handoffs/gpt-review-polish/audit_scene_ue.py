# #451 phase one (i5, 2026-11-03): READ-ONLY scene audit for the #347 master prompt. Changes nothing, saves nothing.
# Writes handoffs/gpt-review-polish/audit_raw.txt: world, lights, sky/atmosphere/clouds/fog, post-process volumes,
# renderer cvars (Lumen, Nanite, VSM, volumetrics), static-mesh usage by mesh + material (top 60), landscapes, foliage,
# decals, Niagara, tentacles, cannons.
import collections, unreal
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/audit_raw.txt'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
L = ['world %s' % world.get_path_name()]
acts = EAS.get_all_level_actors()
L.append('actors %d' % len(acts))
by_cls = collections.Counter(a.get_class().get_name() for a in acts)
L.append('== classes (top 40)'); L += ['  %5d %s' % (n, c) for c, n in by_cls.most_common(40)]


def P(o, *names):
    out = []
    for n in names:
        try: out.append('%s=%s' % (n, o.get_editor_property(n)))
        except Exception: pass
    return ' '.join(out)


L.append('== lights')
for a in acts:
    if isinstance(a, unreal.Light):
        c = a.light_component
        L.append('  %s %s int=%.2f T=%s useT=%s shadows=%s vol=%s mob=%s loc=%s rot=%s' % (
            a.get_class().get_name(), a.get_actor_label(), c.get_editor_property('intensity'),
            c.get_editor_property('temperature'), c.get_editor_property('use_temperature'), c.get_editor_property('cast_shadows'),
            P(c, 'volumetric_scattering_intensity'), c.get_editor_property('mobility'),
            [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)],
            a.get_actor_rotation() if isinstance(a, unreal.DirectionalLight) else ''))
n_point = sum(1 for a in acts if isinstance(a, (unreal.PointLight, unreal.SpotLight)))
n_shadow = sum(1 for a in acts if isinstance(a, (unreal.PointLight, unreal.SpotLight)) and a.light_component.get_editor_property('cast_shadows'))
L.append('  local lights %d, shadow-casting %d' % (n_point, n_shadow))
L.append('== sky / fog / clouds / ppv')
for a in acts:
    cn = a.get_class().get_name()
    if cn in ('SkyAtmosphere', 'VolumetricCloud', 'ExponentialHeightFog', 'SkyLight', 'LocalFogVolume', 'PostProcessVolume'):
        comp = a.get_components_by_class(unreal.ActorComponent)
        L.append('  %s %s' % (cn, a.get_actor_label()))
        for c in comp:
            if isinstance(c, unreal.ExponentialHeightFogComponent):
                L.append('    ' + P(c, 'fog_density', 'fog_height_falloff', 'fog_inscattering_luminance', 'volumetric_fog', 'volumetric_fog_scattering_distribution', 'volumetric_fog_albedo', 'volumetric_fog_extinction_scale', 'start_distance', 'fog_max_opacity'))
            if isinstance(c, unreal.SkyLightComponent):
                L.append('    ' + P(c, 'intensity', 'real_time_capture', 'source_type', 'lower_hemisphere_is_black'))
            if isinstance(c, unreal.VolumetricCloudComponent):
                L.append('    ' + P(c, 'layer_bottom_altitude', 'layer_height', 'material'))
            if isinstance(c, unreal.SkyAtmosphereComponent):
                L.append('    ' + P(c, 'rayleigh_scattering', 'mie_scattering_scale', 'mie_anisotropy', 'aerial_pespective_view_distance_scale', 'multi_scattering_factor'))
        if cn == 'PostProcessVolume':
            s = a.get_editor_property('settings')
            L.append('    unbound=%s priority=%s' % (a.get_editor_property('unbound'), a.get_editor_property('priority')))
            for k in ('auto_exposure_method', 'auto_exposure_bias', 'auto_exposure_min_brightness', 'auto_exposure_max_brightness',
                      'bloom_intensity', 'vignette_intensity', 'scene_fringe_intensity', 'film_grain_intensity', 'color_saturation',
                      'color_contrast', 'color_gain', 'white_temp', 'sharpen', 'dynamic_global_illumination_method',
                      'reflection_method', 'lumen_scene_lighting_quality', 'lumen_final_gather_quality', 'depth_of_field_fstop'):
                try:
                    if s.get_editor_property('override_' + k): L.append('    %s = %s' % (k, s.get_editor_property(k)))
                except Exception: pass
L.append('== renderer cvars')
for cv in ('r.DynamicGlobalIlluminationMethod', 'r.ReflectionMethod', 'r.Shadow.Virtual.Enable', 'r.Nanite', 'r.VolumetricFog',
           'r.VolumetricCloud', 'r.Lumen.SurfaceCache.CardCaptureRefreshFraction', 'r.Streaming.PoolSize', 'r.ScreenPercentage',
           'r.AntiAliasingMethod', 'r.Lumen.HardwareRayTracing'):
    try: L.append('  %s = %s' % (cv, unreal.SystemLibrary.get_console_variable_int_value(cv)))
    except Exception: pass
L.append('== static meshes by mesh (instances, materials) top 60')
mesh_n, mesh_mats = collections.Counter(), {}
for a in acts:
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if not m: continue
        k = m.get_path_name().split('.')[0]
        mesh_n[k] += 1
        if k not in mesh_mats:
            mesh_mats[k] = sorted({(mi.get_path_name().split('.')[0] if mi else 'None') for mi in c.get_materials()})
for k, n in mesh_n.most_common(60):
    L.append('  %4d %s  %s' % (n, k, ' | '.join(mesh_mats[k])))
L.append('  distinct meshes %d' % len(mesh_n))
L.append('== landscapes / foliage / decals / niagara')
for a in acts:
    if isinstance(a, (unreal.Landscape, unreal.LandscapeProxy)):
        L.append('  landscape %s mat=%s' % (a.get_actor_label(), a.get_editor_property('landscape_material').get_path_name() if a.get_editor_property('landscape_material') else None))
for a in acts:
    if a.get_class().get_name() == 'InstancedFoliageActor':
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            L.append('  foliage %6d %s' % (c.get_instance_count(), m.get_path_name().split('.')[0] if m else None))
dec = collections.Counter()
for a in acts:
    if isinstance(a, unreal.DecalActor):
        mi = a.decal.get_editor_property('decal_material'); dec[mi.get_path_name().split('.')[0] if mi else 'None'] += 1
L.append('  decals %d' % sum(dec.values())); L += ['    %4d %s' % (n, k) for k, n in dec.most_common(30)]
nia = collections.Counter()
for a in acts:
    for c in a.get_components_by_class(unreal.NiagaraComponent):
        s = c.get_asset(); nia[s.get_path_name().split('.')[0] if s else 'None'] += 1
L.append('  niagara comps %d' % sum(nia.values())); L += ['    %4d %s' % (n, k) for k, n in nia.most_common(25)]
L.append('== tentacles / cannons / mountains (by label)')
for a in acts:
    lab = a.get_actor_label()
    if any(t in lab.lower() for t in ('tentacle', 'cannon', 'mountain', 'cliff')):
        L.append('  %s %s at %s' % (a.get_class().get_name(), lab, [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)]))
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('audit written', OUT, len(L), 'lines')
