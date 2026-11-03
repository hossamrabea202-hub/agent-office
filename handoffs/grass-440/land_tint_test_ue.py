# #440 (i5): lookdev only. Runtime (unsaved) GrassTint / ForestTint on the 4 gate tiles, one base-colour capture, then back.
#   py land_tint_test_ue.py <tag> <gr,gg,gb> <fr,fg,fb>
import runpy, sys, unreal
tag, g, f = sys.argv[1], [float(v) for v in sys.argv[2].split(',')], [float(v) for v in sys.argv[3].split(',')]
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
P = [a for a in EAS.get_all_level_actors() if a.get_actor_label().replace('LandscapeStreamingProxy_', '') in ('3_3_0', '3_4_0', '4_3_0', '4_4_0')]
LC = lambda v: unreal.LinearColor(v[0], v[1], v[2], 1)
def setv(gv, fv):
    for p in P:
        p.set_landscape_material_vector_parameter_value('GrassTint', LC(gv)); p.set_landscape_material_vector_parameter_value('ForestTint', LC(fv))
setv(g, f)
try:
    sys.argv = ['shots_ue.py', tag + '@bc', 'wall;250,1750,1350;-4500,1500,0', 'low;-3000,500,180;-600,1900,40']
    runpy.run_path('C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/shots_ue.py', run_name='__main__')
except SystemExit: pass
finally:
    setv((0.27, 0.30, 0.17), (0.085, 0.09, 0.06)); print('tints back to the live values on', len(P), 'tiles')
