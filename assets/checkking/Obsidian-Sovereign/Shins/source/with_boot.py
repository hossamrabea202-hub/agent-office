# Append the boot build into the open greave file, then run the greave render: blender -b shin_build_r1.blend -P with_boot.py -- prefix samples res
import bpy, os
with bpy.data.libraries.load(r'C:\Users\hossam.rabea\checkking-work\boots\boot_build_r1.blend') as (src, dst):
    dst.objects = list(src.objects)
for o in dst.objects:
    if o is not None: bpy.context.scene.collection.objects.link(o)
exec(open(os.path.join(os.path.dirname(bpy.data.filepath), 'render_shin.py')).read())
