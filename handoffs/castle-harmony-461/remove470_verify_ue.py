# #470 (i5): verify a stripped material: no crack params / code left, compiles, its MIs still resolve.
import sys, unreal
MEL = unreal.MaterialEditingLibrary
p = sys.argv[1]; m = unreal.load_asset(p)
codes = [x.get_editor_property('code') for x in unreal.ObjectIterator(unreal.MaterialExpressionCustom) if x.get_path_name().startswith(m.get_path_name() + ':') or x.get_path_name().startswith(m.get_path_name() + '.')]
print('crack refs in code:', sum(c.count('Crack') for c in codes), '| custom nodes:', len(codes))
print('scalar params:', [str(x) for x in MEL.get_scalar_parameter_names(m) if 'rack' in str(x)], '| texture params:', [str(x) for x in MEL.get_texture_parameter_names(m) if 'rack' in str(x)])
print('stats', MEL.get_statistics(m).to_tuple() if hasattr(MEL, 'get_statistics') else 'n/a')
mi = unreal.load_asset('/Game/CastleDefender/Environment/Castle/StairsBaked/MI_StairBaked_Tread')
print('child MI parent:', mi.get_editor_property('parent').get_name(), '| its scalar params now:', len(MEL.get_scalar_parameter_names(mi)))
