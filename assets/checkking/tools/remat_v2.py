# Swap the v2 procedural materials into an existing bake_ready.blend (geometry + UVs untouched), then save it.
#   blender -b <dir>/bake_ready.blend -P remat_v2.py -- [leather_tone]
import sys, bpy
sys.path.insert(0, r'C:\Users\hossam.rabea\checkking-work\chest')
import materials
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if args: materials.LEATHER_TONE = float(args[0])
materials.build_all()
bpy.ops.wm.save_mainfile()
print('REMAT OK', bpy.data.filepath, 'leather', materials.LEATHER_TONE)
