# Read-only (i5, wood polish): every material used by a mesh in the level, with parent chain, parameters, textures
# (+ their size / sRGB / compression) and where it is used. Writes materials_level.json next to this script.
import json, os, unreal
OUT = os.path.join(os.path.dirname(__file__), 'materials_level.json')
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
info = {}


def tex_info(t):
    try:
        return {'path': t.get_path_name(), 'w': t.blueprint_get_size_x(), 'h': t.blueprint_get_size_y(),
                'srgb': t.get_editor_property('srgb'), 'comp': str(t.get_editor_property('compression_settings')),
                'adjust': [round(t.get_editor_property(p), 3) for p in ('adjust_brightness', 'adjust_saturation', 'adjust_vibrance', 'adjust_rgb_curve')]}
    except Exception as e:
        return {'path': t.get_path_name(), 'err': str(e)}


def mat_info(m):
    if isinstance(m, unreal.MaterialInstanceDynamic):      # runtime MID: report its parent instead
        m = m.get_editor_property('parent') or m
        if isinstance(m, unreal.MaterialInstanceDynamic):
            return info.setdefault('MID:' + m.get_name(), {'class': 'MID', 'chain': [], 'scalar': {}, 'vector': {}, 'texture': {},
                                                          'used_tex': [], 'count': 0, 'meshes': {}, 'actors': []})
    p = m.get_path_name()
    if p in info:
        return info[p]
    d = {'class': m.get_class().get_name(), 'chain': [], 'scalar': {}, 'vector': {}, 'texture': {}, 'used_tex': [],
         'count': 0, 'meshes': {}, 'actors': []}
    cur = m
    while isinstance(cur, unreal.MaterialInstance):
        cur = cur.get_editor_property('parent')
        if cur:
            d['chain'].append(cur.get_path_name())
        else:
            break
    if isinstance(m, unreal.MaterialInstance):
        for n in MEL.get_scalar_parameter_names(m):
            d['scalar'][str(n)] = round(MEL.get_material_instance_scalar_parameter_value(m, n), 4)
        for n in MEL.get_vector_parameter_names(m):
            c = MEL.get_material_instance_vector_parameter_value(m, n); d['vector'][str(n)] = [round(c.r, 4), round(c.g, 4), round(c.b, 4), round(c.a, 4)]
        for n in MEL.get_texture_parameter_names(m):
            t = MEL.get_material_instance_texture_parameter_value(m, n)
            d['texture'][str(n)] = tex_info(t) if t else None
    try:
        base = m.get_base_material()
        for t in MEL.get_used_textures(base):
            d['used_tex'].append(tex_info(t))
    except Exception:
        pass
    info[p] = d
    return d


for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.get_editor_property('static_mesh')
        if not sm:
            continue
        n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if not m:
                continue
            d = mat_info(m)
            d['count'] += n
            d['meshes'][sm.get_path_name()] = d['meshes'].get(sm.get_path_name(), 0) + n
            if len(d['actors']) < 8:
                l = a.get_actor_location()
                d['actors'].append('%s @ %d,%d,%d%s' % (a.get_actor_label(), l.x, l.y, l.z, '' if c.is_visible() else ' (hidden)'))
json.dump(info, open(OUT, 'w'), indent=0)
print('materials:', len(info), '->', OUT)
