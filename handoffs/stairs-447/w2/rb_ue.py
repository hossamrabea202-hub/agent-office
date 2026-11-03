import unreal
MEL = unreal.MaterialEditingLibrary
mi = unreal.load_asset('/Game/CastleDefender/Environment/Castle/StairsBaked451/MI_StairBaked451_N13_W2')
for p in ('BakedColor', 'BakedNormal', 'BakedAO'):
    t = MEL.get_material_instance_texture_parameter_value(mi, p); print('RB', p, t.get_name() if t else None)
print('tex overrides', [(str(v.parameter_info.name), v.parameter_value.get_name() if v.parameter_value else None) for v in mi.get_editor_property('texture_parameter_values')])
