# #77 lookdev (i5, 2026-11-01): the showcase crossbow alone, XbowUp = (0,0) then (4,4) on the WORLD's MPC instance
# (editing the asset default doesn't reach the live instance), two captures at max for two crackle frames, then back to 0.
# Captures go to handoffs/xbow-upgrade-visuals/i5_lv0.png, i5_lv4.png, i5_lv4b.png (capture_shot_ue.py, no viewport needed).
import sys, time, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/'
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
m = unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree')
def setx(v): unreal.MaterialLibrary.set_vector_parameter_value(W, m, 'XbowUp', unreal.LinearColor(v, v, 0, 0))
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
sc = [a for a in acts if a.get_class().get_name().startswith('BP_TradeShowcase')][0]
which = sys.argv[1] if len(sys.argv) > 1 else 'ItemXbow'
c = [x for x in sc.get_components_by_class(unreal.MeshComponent) if which in x.get_name()][0]
others = [x for x in sc.get_components_by_class(unreal.MeshComponent) if x is not c and x.is_visible()]
for x in others: x.set_visibility(False)
c.set_visibility(True)
o = c.get_world_location(); r = 70.0
cam = o + unreal.Vector(-r * 2.0, -r * 1.0, r * 0.6)
def shot(name):
    sys.argv = ['x', H + 'xbow-upgrade-visuals/' + name, str(cam.x), str(cam.y), str(cam.z), str(o.x), str(o.y), str(o.z), '35']
    exec(compile(open(H + 'laptop-i5/capture_shot_ue.py').read(), 'cap', 'exec'), {'__name__': '__main__'})
try:
    setx(0.0); shot('i5_lv0.png'); setx(4.0); shot('i5_lv4.png'); shot('i5_lv4b.png')
finally:
    setx(0.0)
    for x in others: x.set_visibility(True)
print('done, XbowUp back to 0, %d other showcase meshes visible again' % len(others))
