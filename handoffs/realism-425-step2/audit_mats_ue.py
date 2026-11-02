# #425 step 2 (i5): READ-ONLY audit of the materials on level meshes, grouped by surface kind (wood / stone / grass...).
# Writes audit.txt: material, parent, kind, how many components use it, its texture + scalar params. Changes nothing.
import collections, unreal
KIND = (('wood', ('wood', 'plank', 'timber', 'beam', 'log', 'bark', 'crate', 'barrel')), ('stone', ('stone', 'rock', 'brick', 'cobble', 'castle', 'wall')),
        ('grass', ('grass', 'foliage', 'fern', 'bush', 'leaf', 'leaves', 'moss')), ('metal', ('iron', 'metal', 'steel')))
use = collections.Counter(); meshes = collections.defaultdict(set)
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for c in a.get_components_by_class(unreal.MeshComponent):
        try: mats = c.get_materials()
        except Exception: continue
        for m in mats:
            if m: use[m.get_path_name()] += 1; meshes[m.get_path_name()].add(a.get_actor_label()[:24])
out = []
for path, n in use.most_common():
    m = unreal.load_object(None, path); name = m.get_name().lower()
    kind = next((k for k, keys in KIND if any(x in name for x in keys)), '-')
    if kind == '-': continue
    par = m.get_editor_property('parent').get_name() if isinstance(m, unreal.MaterialInstance) and m.get_editor_property('parent') else '-'
    tex, sc = [], []
    if isinstance(m, unreal.MaterialInstance):
        for t in m.get_editor_property('texture_parameter_values'):
            if t.parameter_value: tex.append('%s=%s' % (t.parameter_info.name, t.parameter_value.get_path_name()))
        for s in m.get_editor_property('scalar_parameter_values'): sc.append('%s=%.3g' % (s.parameter_info.name, s.parameter_value))
        for v in m.get_editor_property('vector_parameter_values'): c = v.parameter_value; sc.append('%s=(%.2f,%.2f,%.2f)' % (v.parameter_info.name, c.r, c.g, c.b))
    out.append('%s | %4d | %s | parent %s | e.g. %s\n    tex: %s\n    par: %s' % (kind, n, path, par, ','.join(sorted(meshes[path])[:3]), '; '.join(tex), ', '.join(sc)))
open('C:/Users/hossam.rabea/agent-office/handoffs/realism-425-step2/audit.txt', 'w', encoding='utf-8').write('\n'.join(out))
print(len(out), 'materials;', collections.Counter(o.split(' |')[0] for o in out))
