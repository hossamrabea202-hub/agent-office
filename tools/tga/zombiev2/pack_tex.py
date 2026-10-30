# Re-save textures losslessly as 8-bit RGB PNG at max compression for the repo.
# blender -b --factory-startup -P pack_tex.py -- <src_dir> <dst_dir> <prefix>      (skips *_N_GL: lookdev only)
import bpy, sys, os
src, dst, pre = sys.argv[sys.argv.index('--') + 1:]
os.makedirs(dst, exist_ok=True)
sc = bpy.context.scene; s = sc.render.image_settings
s.file_format = 'PNG'; s.color_mode = 'RGB'; s.color_depth = '8'; s.compression = 100
for f in sorted(os.listdir(src)):
    if not f.startswith(pre) or not f.endswith('.png') or f.endswith('_N_GL.png'): continue
    im = bpy.data.images.load(os.path.join(src, f)); im.colorspace_settings.name = 'Non-Color'
    im.save_render(os.path.join(dst, f), scene=sc); bpy.data.images.remove(im)
    print('PACKED', f, os.path.getsize(os.path.join(dst, f)) // 1024, 'KB', flush=True)
