# #440 (i5): is the dark ground the worn decal? Print its box, hide it for one base-colour capture, show it again.
import runpy, sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
d = next(a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'Env_WornGround_Decal')
c = d.get_component_by_class(unreal.DecalComponent); xf = c.get_world_transform()
print('DECAL size', c.get_editor_property('decal_size'), 'scale', xf.scale3d, 'rot', xf.rotation.rotator(), 'mat', c.get_editor_property('decal_material').get_path_name())
c.set_visibility(False)
try:
    sys.argv = ['shots_ue.py', 'g440nodecal@bc', 'wall;250,1750,1350;-4500,1500,0']
    runpy.run_path('C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/shots_ue.py', run_name='__main__')
except SystemExit: pass
finally:
    c.set_visibility(True); print('decal visible again', c.is_visible())
