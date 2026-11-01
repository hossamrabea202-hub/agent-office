# #401 stables lookdev at locked exposure (knowledge base). checkking (Claude), 2026-11-01.
#   blender -b stable.blend -P lookdev_stable.py -- <texdir> <out.png> <view: 34|front|inside|close> [exposure]
# The material here is the same recipe as M_StableTile in UE (import_stable_ue.py): tiling BC/ORM/N + vertex 'Wear':
#   G (muck): colour -> lerp(base, lerp(base^2, muck, 0.5), G), roughness -> lerp(r, 0.35, 0.8 G)  (wet dung is dark + glossy)
#   B (sun):  colour -> lerp(c, grey(c) * 1.12, 0.45 B), roughness + 0.05 B                     (UV-bleached, dry)
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cavlib import lookdev
a = sys.argv[sys.argv.index('--') + 1:]
TEX, OUTP, VIEW = a[0], a[1], a[2]
EXP = float(a[3]) if len(a) > 3 else None
MUCK = (0.050, 0.034, 0.021)

def build(m, name):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled'); L(p.outputs[0], out.inputs[0])
    def img(suffix, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(TEX, f'T_Stable{name}_{suffix}.png'))
        n.image.colorspace_settings.name = cs; return n
    bc = img('BC', 'sRGB'); orm = img('ORM', 'Non-Color'); nm = img('N_GL', 'Non-Color')
    sep = nt.nodes.new('ShaderNodeSeparateColor'); L(orm.outputs[0], sep.inputs[0])
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Wear'; vs = nt.nodes.new('ShaderNodeSeparateColor'); L(vc.outputs[0], vs.inputs[0])
    sq = nt.nodes.new('ShaderNodeMix'); sq.data_type = 'RGBA'; sq.blend_type = 'MULTIPLY'; sq.inputs[0].default_value = 1.0
    L(bc.outputs[0], sq.inputs[6]); L(bc.outputs[0], sq.inputs[7])
    mk = nt.nodes.new('ShaderNodeMix'); mk.data_type = 'RGBA'; mk.inputs[0].default_value = 0.5; L(sq.outputs[2], mk.inputs[6]); mk.inputs[7].default_value = (*MUCK, 1)
    c1 = nt.nodes.new('ShaderNodeMix'); c1.data_type = 'RGBA'; L(vs.outputs[1], c1.inputs[0]); L(bc.outputs[0], c1.inputs[6]); L(mk.outputs[2], c1.inputs[7])
    gr = nt.nodes.new('ShaderNodeRGBToBW'); L(c1.outputs[2], gr.inputs[0])
    gm = nt.nodes.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'; gm.inputs[1].default_value = 1.12; L(gr.outputs[0], gm.inputs[0])
    bm = nt.nodes.new('ShaderNodeMath'); bm.operation = 'MULTIPLY'; bm.inputs[1].default_value = 0.45; L(vs.outputs[2], bm.inputs[0])
    c2 = nt.nodes.new('ShaderNodeMix'); c2.data_type = 'RGBA'; L(bm.outputs[0], c2.inputs[0]); L(c1.outputs[2], c2.inputs[6]); L(gm.outputs[0], c2.inputs[7])
    L(c2.outputs[2], p.inputs['Base Color'])
    g8 = nt.nodes.new('ShaderNodeMath'); g8.operation = 'MULTIPLY'; g8.inputs[1].default_value = 0.8; L(vs.outputs[1], g8.inputs[0])
    r1 = nt.nodes.new('ShaderNodeMix'); r1.data_type = 'FLOAT'; L(g8.outputs[0], r1.inputs[0]); L(sep.outputs[1], r1.inputs[2]); r1.inputs[3].default_value = 0.35
    b5 = nt.nodes.new('ShaderNodeMath'); b5.operation = 'MULTIPLY_ADD'; L(vs.outputs[2], b5.inputs[0]); b5.inputs[1].default_value = 0.05; L(r1.outputs[0], b5.inputs[2])
    L(b5.outputs[0], p.inputs['Roughness']); L(sep.outputs[2], p.inputs['Metallic'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); L(nm.outputs[0], nmap.inputs['Color']); L(nmap.outputs[0], p.inputs['Normal'])

ob = bpy.data.objects['SM_Stable']
for m in ob.data.materials:
    build(m, m.name.replace('M_Stable', ''))
for o in list(bpy.data.objects):
    if o.name.startswith('UCX_'): bpy.data.objects.remove(o)
views = {'34': ((-7.5, -10.5, 4.2), (8.0, 3.5, 1.8), 24, (2.2, -2.2, 0)),
         'front': ((8.0, -12.0, 2.4), (8.0, 3.0, 2.2), 26, (3.0, -2.5, 0)),
         'inside': ((6.4, 0.9, 1.7), (2.6, 6.2, 1.0), 18, (4.6, 2.4, 0)),
         'close': ((3.9, 2.2, 1.45), (2.2, 5.6, 0.9), 26, (2.6, 3.0, 0))}
cl, tg, lens, ball = views[VIEW]
lookdev(OUTP, cl, tg, lens=lens, sun_rot=float(os.environ.get('SUNROT', '200')), res=(1600, 1000),
        samples=int(os.environ.get('LD_SAMPLES', '48')), ball_at=ball, exposure=EXP)
