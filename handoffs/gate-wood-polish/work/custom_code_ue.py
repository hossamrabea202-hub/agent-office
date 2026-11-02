# Read-only: print the HLSL of the Custom node(s) feeding BaseColor of a material. py custom_code_ue.py <material>
import sys, unreal
MEL = unreal.MaterialEditingLibrary
mat = unreal.load_asset(sys.argv[1])
seen, found = set(), []


def walk(n):
    if n is None or n.get_name() in seen:
        return
    seen.add(n.get_name())
    if isinstance(n, unreal.MaterialExpressionCustom):
        found.append(n)
    for ch in MEL.get_inputs_for_material_expression(mat, n):
        walk(ch)


for prop in ('MP_BASE_COLOR', 'MP_METALLIC', 'MP_ROUGHNESS', 'MP_NORMAL'):
    walk(MEL.get_material_property_input_node(mat, getattr(unreal.MaterialProperty, prop)))
for n in found:
    print('==== CUSTOM', n.get_editor_property('description'), 'out', n.get_editor_property('output_type'))
    print('inputs:', [str(i.get_editor_property('input_name')) for i in n.get_editor_property('inputs')])
    print(n.get_editor_property('code'))
