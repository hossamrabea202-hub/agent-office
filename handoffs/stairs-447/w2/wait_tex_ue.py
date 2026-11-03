import unreal
for n in ('C', 'N', 'M'):
    t = unreal.load_asset('/Game/CastleDefender/Environment/Castle/StairsBaked451/T_StairBaked451_N13_' + n)
    print('TEX', t.get_name(), t.blueprint_get_size_x(), t.get_editor_property('compression_settings'), t.get_editor_property('srgb'))
unreal.SystemLibrary.execute_console_command(None, 'r.Streaming.FullyLoadUsedTextures')
mi = unreal.load_asset('/Game/CastleDefender/Environment/Castle/StairsBaked451/MI_StairBaked451_N13_W2')
p = mi.get_editor_property('parent'); print('parent', p.get_name())
