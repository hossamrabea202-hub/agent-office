# Copies the finished weapons into the office repo: assets/laptop2/WeaponPack/<Item>/ (FBX, textures with 8-bit normals,
# renders, shop icon) + the shared import script, README and the build/bake sources.
#   blender -b --factory-startup -P pack_weapons.py -- <repo> [Item ...]
import bpy, os, sys, shutil, glob
args = sys.argv[sys.argv.index('--') + 1:]
REPO, pick = args[0], args[1:]
SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(REPO, 'assets', 'laptop2', 'WeaponPack')
ITEMS = {'HeaterShield': ('SM_HeaterShield', 'T_HeaterShield', 'heater', 'T_Item_HeaterShield'),
         'RoundShield': ('SM_RoundShield', 'T_RoundShield', 'round', 'T_Item_RoundShield'),
         'Emberoath': ('SM_Emberoath', 'T_Emberoath', 'sword', 'T_Item_Emberoath')}
sc = bpy.context.scene; st = sc.render.image_settings
for item in (pick or ITEMS):
    mesh, tn, rp, icon = ITEMS[item]
    d = os.path.join(OUT, item); os.makedirs(os.path.join(d, 'textures'), exist_ok=True); os.makedirs(os.path.join(d, 'renders'), exist_ok=True)
    shutil.copy2(os.path.join(SRC, mesh + '.fbx'), d)
    for suf in ('_BaseColor', '_ORM', '_Emissive'):
        p = os.path.join(SRC, 'tex', tn + suf + '.png')
        if os.path.exists(p): shutil.copy2(p, os.path.join(d, 'textures'))
    im = bpy.data.images.load(os.path.join(SRC, 'tex', tn + '_Normal_DirectX.png')); im.colorspace_settings.name = 'Non-Color'
    st.file_format = 'PNG'; st.color_depth = '8'; st.color_mode = 'RGB'; st.compression = 90
    im.save_render(os.path.join(d, 'textures', tn + '_Normal_DirectX.png'), scene=sc); bpy.data.images.remove(im)
    for r in glob.glob(os.path.join(SRC, 'renders', rp + '_*.png')) + glob.glob(os.path.join(SRC, 'renders', rp + 'B_*.png')):
        shutil.copy2(r, os.path.join(d, 'renders'))
    ic = os.path.join(SRC, 'icon', icon + '.png')
    if os.path.exists(ic): os.makedirs(os.path.join(d, 'icon'), exist_ok=True); shutil.copy2(ic, os.path.join(d, 'icon'))
    print('PACKED', item)
os.makedirs(os.path.join(OUT, 'source'), exist_ok=True)
for f in ('shieldkit.py', 'build_heater.py', 'build_round.py', 'build_sword.py', 'shieldmat.py', 'swordmat.py', 'matlib.py',
          'bake_shield.py', 'run_shield.ps1', 'render_heater.py', 'icon_heater.py', 'pack_weapons.py'):
    shutil.copy2(os.path.join(SRC, f), os.path.join(OUT, 'source'))
shutil.copy2(os.path.join(SRC, 'import_weapons_ue.py'), OUT)
if os.path.exists(os.path.join(SRC, 'WEAPONPACK_README.md')): shutil.copy2(os.path.join(SRC, 'WEAPONPACK_README.md'), os.path.join(OUT, 'README.md'))
print('PACK OK')
