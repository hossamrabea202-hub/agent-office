import unreal, subprocess, os, glob
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())
eng = unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir())
uat = os.path.join(eng, 'Build', 'BatchFiles', 'RunUAT.bat')
out = r'C:\Unreal Backups\CastleDefender_Build\Release_2026-10-31_v2'
os.makedirs(out, exist_ok=True)
log = open(r'C:\Users\hossa\Documents\agent-office\_package2.log', 'w')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
gm = unreal.get_default_object(unreal.GameMapsSettings)
MAPS = []
for p in ('game_default_map', 'editor_startup_map'):
    try:
        v = str(gm.get_editor_property(p).get_editor_property('asset_path_name') if hasattr(gm.get_editor_property(p), 'get_editor_property') else gm.get_editor_property(p))
    except Exception: v = ''
    v = v.split('.')[0]
    if v.startswith('/Game') and v not in MAPS: MAPS.append(v)
if '/Game/ThirdPerson/Maps/ThirdPersonMap' not in MAPS: MAPS.append('/Game/ThirdPerson/Maps/ThirdPersonMap')
args = [uat, 'BuildCookRun', '-project=' + proj, '-noP4', '-utf8output', '-nocompileeditor', '-skipbuildeditor', '-nocompile', '-nocompileuat',
        '-installed', '-unrealexe=' + os.path.join(eng, 'Binaries', 'Win64', 'UnrealEditor-Cmd.exe'), '-platform=Win64', '-clientconfig=Shipping',
        '-cook', '-build', '-stage', '-package', '-pak', '-iostore', '-compressed', '-prereqs', '-archive', '-archivedirectory=' + out, '-map=' + '+'.join(MAPS)]
P = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=0x08000000, cwd=os.path.dirname(uat))
open(r'C:\Users\hossa\Documents\agent-office\_package2_info.txt', 'w').write('PID %d\n%s\n%s' % (P.pid, proj, ' '.join(args)))
print('PACKAGE STARTED', P.pid, proj)
