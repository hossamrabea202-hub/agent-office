# Blender: import the brute rig + a UE anim FBX, re-export the anim the way the new clips will be exported.
# blender -b -P bl_roundtrip.py -- <SK.fbx> <anim.fbx> <out.fbx>
import bpy, sys, os
a = sys.argv[sys.argv.index('--')+1:]; SK, ANIM, OUT = a
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_rig as R
arm = R.load_rig(SK)
R.apply_anim_fbx(arm, ANIM)
R.export_anim(arm, OUT)
print('ROUNDTRIP OK', OUT)
