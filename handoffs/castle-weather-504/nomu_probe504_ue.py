import unreal
MEL = unreal.MaterialEditingLibrary
print([n for n in dir(MEL) if 'rror' in n or 'compile' in n.lower() or 'stat' in n.lower()])
m = unreal._cw504['M_RainStreakCard504']
for n in ('compile_errors', 'material_compile_errors'):
    try: print(n, m.get_editor_property(n))
    except Exception as e: print(n, 'x', e)
t = unreal.new_object(unreal.Material, name='M_T504min')
c = MEL.create_material_expression(t, unreal.MaterialExpressionConstant3Vector, -300, 0)
MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
t.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MODULATE); t.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
MEL.recompile_material(t); print('min compiled')
