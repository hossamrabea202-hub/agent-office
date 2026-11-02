# Read-only: walk a material graph upstream from BaseColor / Metallic / Roughness and print the tree (depth-limited).
#   py graph_walk_ue.py <material asset path> [depth=7]
import sys, unreal
MEL = unreal.MaterialEditingLibrary
mat = unreal.load_asset(sys.argv[1]); depth = int(sys.argv[2]) if len(sys.argv) > 2 else 7
seen = {}


def desc(n):
    d = n.get_class().get_name().replace('MaterialExpression', '')
    for p in ('parameter_name', 'r', 'constant', 'default_value', 'texture', 'code', 'description', 'input_name'):
        try:
            v = n.get_editor_property(p)
        except Exception:
            continue
        if v is None:
            continue
        if hasattr(v, 'get_name'):
            v = v.get_name()
        s = str(v).replace('\n', ' ')
        d += ' %s=%s' % (p, s[:90])
    return d


def walk(n, lvl, pre):
    if n is None:
        return
    key = n.get_name()
    if key in seen:
        print(pre + '(see %s) %s' % (seen[key], desc(n)[:60])); return
    seen[key] = len(seen)
    print(pre + '#%d %s' % (seen[key], desc(n)))
    if lvl >= depth:
        return
    for ch in MEL.get_inputs_for_material_expression(mat, n):
        walk(ch, lvl + 1, pre + '  ')


for prop in ('MP_BASE_COLOR', 'MP_METALLIC', 'MP_ROUGHNESS'):
    print('=====', prop)
    walk(MEL.get_material_property_input_node(mat, getattr(unreal.MaterialProperty, prop)), 0, '')
