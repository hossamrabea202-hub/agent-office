# #440 step 1 (i5, 2026-11-03): READ-ONLY inventory of today's grass. Changes nothing.
# Lists: landscape materials and their LandscapeGrassOutput grass types (every variety: mesh, density, cull, shadows,
# scale, align), all LandscapeGrassType assets, PCG components in the level, instanced mesh components (counts per mesh,
# grass/foliage-like ones), WindDirectionalSource settings. -> grass-mountain-research/grass_inventory.txt
import collections, unreal
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/grass-mountain-research/grass_inventory.txt'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
L = []


def P(o, *names):
    out = []
    for n in names:
        try: out.append('%s=%s' % (n, o.get_editor_property(n)))
        except Exception: pass
    return ' '.join(out)


acts = EAS.get_all_level_actors()
lmats = collections.Counter()
for a in acts:
    if isinstance(a, unreal.LandscapeProxy):
        m = a.get_editor_property('landscape_material'); lmats[m.get_path_name() if m else 'None'] += 1
L.append('== landscape materials (proxies using it)'); L += ['  %3d %s' % (n, k) for k, n in lmats.most_common()]
L.append('== LandscapeGrassType assets')
f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Landscape', 'LandscapeGrassType')], package_paths=['/Game'], recursive_paths=True)
for ad in AR.get_assets(f):
    g = ad.get_asset(); L.append('  ' + g.get_path_name())
    try:
        for v in g.get_editor_property('grass_varieties'):
            m = v.get_editor_property('grass_mesh')
            L.append('     mesh=%s %s' % (m.get_name() if m else None, P(v, 'grass_density', 'start_cull_distance', 'end_cull_distance',
                     'min_lod', 'scaling', 'scale_x', 'random_rotation', 'align_to_surface', 'use_landscape_lightmap', 'receives_decals',
                     'cast_dynamic_shadow', 'cast_contact_shadow', 'use_grid')))
    except Exception as e: L.append('     (varieties unreadable: %s)' % e)
L.append('== grass outputs in the landscape materials')
for mp in lmats:
    if mp == 'None': continue
    mi = unreal.load_asset(mp)
    base = mi.get_base_material() if hasattr(mi, 'get_base_material') else mi
    L.append('  %s -> base %s' % (mp.split('/')[-1], base.get_path_name()))
    try:
        for e in unreal.MaterialEditingLibrary.get_material_expressions(base) if hasattr(unreal.MaterialEditingLibrary, 'get_material_expressions') else []:
            if isinstance(e, unreal.MaterialExpressionLandscapeGrassOutput):
                for gt in e.get_editor_property('grass_types'):
                    t = gt.get_editor_property('grass_type'); L.append('     grass output: %s -> %s' % (gt.get_editor_property('name'), t.get_path_name() if t else None))
    except Exception as ex: L.append('     (expressions unreadable: %s)' % ex)
L.append('== PCG components')
for a in acts:
    for c in a.get_components_by_class(unreal.PCGComponent) if hasattr(unreal, 'PCGComponent') else []:
        g = c.get_editor_property('graph_instance')
        L.append('  %s %s graph=%s' % (a.get_actor_label(), a.get_class().get_name(), g.get_editor_property('graph').get_path_name() if g and g.get_editor_property('graph') else None))
L.append('== instanced meshes (instances per mesh, top 40)')
inst = collections.Counter(); owner = {}
for a in acts:
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if not m: continue
        k = m.get_path_name().split('.')[0]; inst[k] += c.get_instance_count(); owner.setdefault(k, (a.get_actor_label(), a.get_class().get_name(),
            c.get_editor_property('instance_end_cull_distance') if hasattr(c, 'instance_end_cull_distance') else P(c, 'instance_end_cull_distance'), c.get_editor_property('cast_shadow')))
for k, n in inst.most_common(40): L.append('  %8d %-70s %s' % (n, k, owner[k]))
L.append('== wind')
for a in acts:
    if a.get_class().get_name() == 'WindDirectionalSource':
        c = a.get_component_by_class(unreal.WindDirectionalSourceComponent); L.append('  %s rot=%s %s' % (a.get_actor_label(), a.get_actor_rotation(), P(c, 'strength', 'speed', 'min_gust_amount', 'max_gust_amount', 'radius', 'point_wind')))
open(OUT, 'w', encoding='utf-8').write('\n'.join(L)); print('grass inventory', len(L), 'lines')
