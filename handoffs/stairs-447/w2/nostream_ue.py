# temp A/B helper: never_stream on/off for the N13 bakes (NOT saved)
import sys, unreal
on = sys.argv[1] == 'on'
for n in ('C', 'N', 'M'):
    t = unreal.load_asset('/Game/CastleDefender/Environment/Castle/StairsBaked451/T_StairBaked451_N13_' + n)
    t.set_editor_property('never_stream', on); print('never_stream', t.get_name(), on)
