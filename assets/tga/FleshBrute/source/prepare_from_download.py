# Flesh Brute (#229): rebuild TGA's game files from the ORIGINAL licensed download (TGA, 2026-10-31).
# Nothing licensed lives in this repo. The owner / Master downloads the model himself, extracts it, then runs:
#   blender -b -P prepare_from_download.py -- "<extracted download folder>" "C:\Unreal Backups\Castle Defender\Tools\PrivateExports\2026-10-29\flesh-brute"
# What TGA changed versus the download (this script re-applies all of it):
#   1. Mesh / rig: NOTHING. SK_FleshBrute.fbx is the artist's Monster_001.fbx byte for byte (verified by SHA-256),
#      only renamed. Scale, pivot, bones and materials slots are the artist's (cm, A-pose, root bone 'root', 2 slots).
#   2. Textures: 5 skins x 2 parts made by make_skins.py from the artist's skin_01 / skin_02 maps:
#      Clean + Bloody (the artist's two, with the realism pass: dark floor ~36 sRGB, roughness varied at 3 scales),
#      Rotten, Charred, Drowned (derived). Output names: T_FleshBrute_<Skin>_P01/_P02_BC/_ORM + T_FleshBrute_P01/_P02_N.
#   3. Unreal: material + instances are made by import_fleshbrute_ue.py (no files needed beyond the above).
# Needed from the download (folder names as the artist ships them):
#   Monster_001_FBX/Monster_001.fbx
#   Monster_001_TEXTURES/Monster_001_Textures/skin_01/Monster_001_Skin_01_part_0{1,2}_{BaseColor,AO,Roughness,Normal_DirectX}_4K.png
#   Monster_001_TEXTURES/Monster_001_Textures/skin_02/Monster_001_Skin_02_part_0{1,2}_{BaseColor,Roughness}_4K.png
#   (the UE 5.8 project, Blender file, Metallic and OpenGL normal maps are not needed)
import sys, os, shutil, hashlib, runpy
a = sys.argv[sys.argv.index('--') + 1:]
DL, OUT = os.path.abspath(a[0]), os.path.abspath(a[1])
FBX_SHA256 = 'afbcb899cf2820f7bdff9d15e33145c785431a4ab86671b4e1aedbccd7e7c372'    # the FBX TGA tested (artist's 2026-10 upload)

def find(name, want_dir=False):
    for root, dirs, files in os.walk(DL):
        if want_dir and name in dirs: return os.path.join(root, name)
        if not want_dir and name in files: return os.path.join(root, name)
    raise SystemExit('Flesh Brute: %s not found under %s - is this the extracted download?' % (name, DL))

fbx = find('Monster_001.fbx'); tex = find('Monster_001_Textures', want_dir=True)
os.makedirs(os.path.join(OUT, 'textures'), exist_ok=True)
shutil.copyfile(fbx, os.path.join(OUT, 'SK_FleshBrute.fbx'))
h = hashlib.sha256(open(fbx, 'rb').read()).hexdigest()
print('FBX copied as SK_FleshBrute.fbx, sha256', h, flush=True)
if h != FBX_SHA256: print('NOTE: this FBX differs from the one TGA tested (artist update?); check bones/scale after import.')
sys.argv = [sys.argv[0], '--', tex, os.path.join(OUT, 'textures')]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_skins.py'), run_name='__main__')
open(os.path.join(OUT, 'README_PRIVATE.txt'), 'w').write(
    'Flesh Brute - PRIVATE (licensed: "Flesh Mutant Monster" by andrey-ryzhko, Royalty Free licence, no AI).\n'
    'Do NOT commit to the public agent-office repo.\nMade by prepare_from_download.py. Next: py "<repo>/assets/tga/FleshBrute/import_fleshbrute_ue.py"\n')
print('PREPARE OK ->', OUT, flush=True)
