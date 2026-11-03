# #470 lookdev (i5, temporary, NOT saved): CrackAmount on MI_Castle_StoneWall_World in memory, as a lit_ab toggle.  args: <value>
import sys, unreal
MEL = unreal.MaterialEditingLibrary
mi = unreal.load_asset('/Game/CastleDefender/Shared/Materials/Castle/MI_Castle_StoneWall_World')
MEL.set_material_instance_scalar_parameter_value(mi, 'CrackAmount', float(sys.argv[1])); MEL.update_material_instance(mi)
print('StoneWall CrackAmount', sys.argv[1])
