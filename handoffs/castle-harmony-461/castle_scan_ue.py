# #461 castle harmony scan (i5, 2026-11-03). READ-ONLY: saves nothing, changes nothing. Aborts in PIE.
#   py castle_scan_ue.py     -> castle_scan.json next to this file (or in the repo path below), ~1-3 MB
# Every static-mesh element inside the castle box (+15 m): actor, class, hidden state, each mesh component with mesh, tris,
# Nanite, bounds, scale, its materials (+ parent chain + the look parameters that decide harmony: tints, limewash, moss,
# grime, tiling / scale params) and the base-colour texture of each material with its size.
import json, os, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
OUT = None
for h in ('C:/Users/hossam.rabea/agent-office/handoffs/castle-harmony-461/', 'C:/Users/hossa/Documents/agent-office/handoffs/castle-harmony-461/'):
    if os.path.isdir(h): OUT = h; break
BOX = (-400.0 - 1500, -400.0 - 1500, 5000.0 + 1500, 3850.0 + 1500)          # castle box (#41) + 15 m
MEL = unreal.MaterialEditingLibrary
LOOK = ('tint', 'limewash', 'moss', 'grime', 'dirt', 'crack', 'scale', 'tile', 'tiling', 'size', 'macro', 'bright', 'satur', 'rough', 'antitile', 'color', 'colour')
mats = {}

def mat_info(m):
    p = m.get_path_name()
    if p in mats: return p
    d = {'chain': [], 'scalars': {}, 'vectors': {}, 'textures': {}}
    q = m
    while isinstance(q, unreal.MaterialInstance):
        d['chain'].append(q.get_path_name()); q = q.get_editor_property('parent')
    d['base'] = q.get_path_name() if q else None
    if isinstance(m, unreal.MaterialInstanceDynamic):            # runtime MID: read its constant parent's look instead
        d['mid'] = True; m = m.get_editor_property('parent')
    if isinstance(m, unreal.MaterialInstanceConstant):
        for n in MEL.get_scalar_parameter_names(m):
            if any(w in str(n).lower() for w in LOOK): d['scalars'][str(n)] = round(MEL.get_material_instance_scalar_parameter_value(m, n), 4)
        for n in MEL.get_vector_parameter_names(m):
            if any(w in str(n).lower() for w in LOOK):
                v = MEL.get_material_instance_vector_parameter_value(m, n); d['vectors'][str(n)] = [round(v.r, 4), round(v.g, 4), round(v.b, 4), round(v.a, 4)]
        for n in MEL.get_texture_parameter_names(m):
            t = MEL.get_material_instance_texture_parameter_value(m, n)
            if t: d['textures'][str(n)] = [t.get_path_name().split('.')[0], t.blueprint_get_size_x() if hasattr(t, 'blueprint_get_size_x') else 0]
    mats[p] = d
    return p

els = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if not (BOX[0] <= o.x <= BOX[2] and BOX[1] <= o.y <= BOX[3]): continue
    comps = []
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if not m: continue
        isminst = isinstance(c, unreal.InstancedStaticMeshComponent)
        co, ce, _ = unreal.SystemLibrary.get_component_bounds(c)
        try: nan = m.get_editor_property('nanite_settings').enabled
        except Exception: nan = None
        comps.append({'comp': c.get_name(), 'mesh': m.get_path_name().split('.')[0], 'tris': m.get_num_triangles(0), 'nanite': nan,
                      'instances': c.get_instance_count() if isminst else 1, 'visible': c.is_visible() and not c.get_editor_property('hidden_in_game'),
                      'origin': [round(co.x), round(co.y), round(co.z)], 'extent': [round(ce.x), round(ce.y), round(ce.z)],
                      'scale': [round(v, 3) for v in c.get_world_scale().to_tuple()],
                      'mats': [mat_info(c.get_material(i)) if c.get_material(i) else None for i in range(c.get_num_materials())]})
    if comps:
        els.append({'label': a.get_actor_label(), 'name': a.get_name(), 'class': a.get_class().get_name(), 'hidden': a.is_hidden_ed() or a.get_editor_property('hidden'),
                    'folder': str(a.get_folder_path()), 'comps': comps})
json.dump({'box': BOX, 'elements': els, 'materials': mats}, open(OUT + 'castle_scan.json', 'w'))
print('SCAN', len(els), 'actors,', sum(len(x['comps']) for x in els), 'mesh components,', len(mats), 'materials ->', OUT + 'castle_scan.json')
