# Quick look at the procedural material on the high poly, before a full bake:
#   blender -b bake_ready.blend -P preview_mat.py -- out_prefix [samples] [res] [close]
import sys, os
import bpy
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import materials
materials.build_all()
for m in bpy.data.materials:
    if 'OUT' in m.node_tree.nodes if m.node_tree else False:
        try: materials.set_output(m, 'BSDF')
        except KeyError: pass
for o in bpy.data.objects:
    if o.type == 'MESH':
        hide = o.name != 'HP'
        o.hide_render = hide; o.hide_viewport = hide
exec(open(os.path.join(D, 'render_clay.py')).read())
