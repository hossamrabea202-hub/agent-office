# Day / night: the material parameter collection BP_DayNight writes every tick. Run in the UE 5.3 editor:
#   py "<repo>/handoffs/day-night/make_daynight_ue.py"
# Makes /Game/CastleDefender/Environment/DayNight/MPC_DayNight with one scalar: Night (0 by day, 1 at night).
# Any material can read it (Collection Parameter node): torch/lantern/window emissive = Night, the realm glow, etc.
import unreal
ROOT = '/Game/CastleDefender/Environment/DayNight'
EAL, tools = unreal.EditorAssetLibrary, unreal.AssetToolsHelpers.get_asset_tools()
if not EAL.does_directory_exist(ROOT): EAL.make_directory(ROOT)
path = ROOT + '/MPC_DayNight'
if not EAL.does_asset_exist(path):
    mpc = tools.create_asset('MPC_DayNight', ROOT, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
else:
    mpc = unreal.load_asset(path)
p = unreal.CollectionScalarParameter(); p.set_editor_property('parameter_name', 'Night'); p.set_editor_property('default_value', 0.0)
mpc.set_editor_property('scalar_parameters', [p])
EAL.save_asset(mpc.get_path_name())
unreal.log('DAY NIGHT OK: %s (scalar Night)' % path)
