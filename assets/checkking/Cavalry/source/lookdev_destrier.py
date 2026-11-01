# #402 Destrier lookdev at locked exposure. checkking (Claude), 2026-11-01.
#   blender -b <work>/destrier_anim.blend -P lookdev_destrier.py -- <work> <out.png> <view> <skin> <barded 0|1> [action frame]
# Cycles, Nishita sky, sun 35 deg, grey + chrome ball metered on the lit side to 118 sRGB, AgX at that exposure.
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cavlib import lookdev
a = sys.argv[sys.argv.index('--') + 1:]
D, OUTP, VIEW, SKIN, BARDED = a[0], a[1], a[2], a[3], a[4] == '1'
T = os.path.join(D, 'out', 'tex')
def img(nt, name, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, name + '.png')); n.image.colorspace_settings.name = cs; return n
def pbr(m, bc, orm, nrm, sheen=0.0):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled'); L(p.outputs[0], out.inputs[0])
    b = img(nt, bc, 'sRGB'); o = img(nt, orm, 'Non-Color'); n = img(nt, nrm, 'Non-Color')
    sp = nt.nodes.new('ShaderNodeSeparateColor'); L(o.outputs[0], sp.inputs[0])
    L(b.outputs[0], p.inputs['Base Color']); L(sp.outputs[1], p.inputs['Roughness']); L(sp.outputs[2], p.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); L(n.outputs[0], nm.inputs['Color']); L(nm.outputs[0], p.inputs['Normal'])
    if sheen: p.inputs['Sheen Weight'].default_value = sheen; p.inputs['Sheen Roughness'].default_value = 0.5
def hairmat(m, visible=True):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled'); L(p.outputs[0], out.inputs[0])
    t = img(nt, f'T_DestrierHair_{SKIN}_BCA', 'sRGB'); t.image.alpha_mode = 'STRAIGHT'
    L(t.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.45
    if visible: L(t.outputs['Alpha'], p.inputs['Alpha'])
    else: p.inputs['Alpha'].default_value = 0.0
    try: m.blend_method = 'HASHED'
    except Exception: pass
body = bpy.data.objects['SK_Destrier']; hair = bpy.data.objects['SK_Destrier_Hair']; tack = bpy.data.objects['SK_Destrier_Tack']
pbr(body.data.materials[0], f'T_Destrier_{SKIN}_BC', f'T_Destrier_{SKIN}_ORM', 'T_Destrier_N_GL')
hairmat(hair.data.materials[0]); hairmat(hair.data.materials[1], visible=not BARDED)
pbr(tack.data.materials[0], 'T_DestrierTack_BC', 'T_DestrierTack_ORM', 'T_DestrierTack_N_GL', sheen=0.3)
tack.hide_render = not BARDED
for nm, tx in (('SK_Destrier_Lance', 'T_Lance'), ('SK_Destrier_RiderLegs', 'T_RiderLegs')):      # #403 kit, when present
    ob = bpy.data.objects.get(nm)
    if ob:
        pbr(ob.data.materials[0], tx + '_BC', tx + '_ORM', tx + '_N_GL', sheen=0.2); ob.hide_render = os.environ.get('RIDER', '0') != '1'
arm = bpy.data.objects['SK_Destrier_Rig']
if len(a) > 6:
    arm.animation_data.action = bpy.data.actions[a[5]]
    if hasattr(arm.animation_data, 'action_slot') and arm.animation_data.action.slots: arm.animation_data.action_slot = arm.animation_data.action.slots[0]
    bpy.context.scene.frame_set(int(a[6]))
else:
    arm.animation_data.action = bpy.data.actions['A_Destrier_Idle']
    if hasattr(arm.animation_data, 'action_slot') and arm.animation_data.action.slots: arm.animation_data.action_slot = arm.animation_data.action.slots[0]
    bpy.context.scene.frame_set(0)
views = {'34': ((3.6, -4.2, 2.0), (0, -0.25, 1.05), 40, (1.6, -2.2, 0)),
         'side': ((5.2, -0.3, 1.3), (0, -0.25, 1.0), 40, (1.8, -1.9, 0)),
         'head': ((1.6, -2.7, 1.75), (0, -1.2, 1.55), 50, (0.9, -2.2, 0)),
         'front': ((1.2, -4.8, 1.6), (0, -0.6, 1.1), 40, (1.0, -2.6, 0))}
cl, tg, lens, ball = views[VIEW]
lookdev(OUTP, cl, tg, lens=lens, sun_rot=float(os.environ.get('SUNROT', '110')), res=(1600, 1100),
        samples=int(os.environ.get('LD_SAMPLES', '64')), ball_at=ball,
        exposure=float(os.environ['EXPOSURE']) if os.environ.get('EXPOSURE') else -5.34)   # locked: the exterior zone value (stable lookdev, same sun/sky)
