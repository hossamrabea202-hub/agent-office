import bpy, sys
f, n = sys.argv[sys.argv.index('--') + 1], int(sys.argv[sys.argv.index('--') + 2])
im = bpy.data.images.load(f); im.colorspace_settings.name = 'Non-Color'; im.scale(n, n); im.filepath_raw = f; im.file_format = 'PNG'; im.save(); print('resized', f, n)
