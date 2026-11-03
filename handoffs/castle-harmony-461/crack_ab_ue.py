# #470 lookdev (i5, temporary): CrackAmount on one MI, as a toggle for lit_ab_ue.py.  args: <0|1>
import sys, unreal
MEL = unreal.MaterialEditingLibrary
mi = unreal.load_asset('/Game/CastleDefender/Environment/Castle/StairsBaked469/MI_StairBaked469_N13_W2')
MEL.set_material_instance_scalar_parameter_value(mi, 'CrackAmount', float(sys.argv[1])); MEL.update_material_instance(mi)
for n in ('C', 'N', 'M'):
    unreal.load_asset('/Game/CastleDefender/Environment/Castle/StairsBaked469/T_StairBaked469_N13_' + n).set_editor_property('never_stream', True)
print('CrackAmount', sys.argv[1])
