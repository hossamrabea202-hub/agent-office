import unreal, subprocess, os, glob
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())
eng = unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir())
uat = os.path.join(eng, 'Build', 'BatchFiles', 'RunUAT.bat')
out = r'C:\Unreal Backups\CastleDefender_Build\Release_2026-10-31'
os.makedirs(out, exist_ok=True)
log = open(r'C:\Users\hossa\Documents\agent-office\_package.log', 'w')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
args = [uat, 'BuildCookRun', '-project=' + proj, '-noP4', '-utf8output', '-nocompileeditor', '-skipbuildeditor', '-nocompile', '-nocompileuat',
        '-installed', '-unrealexe=' + os.path.join(eng, 'Binaries', 'Win64', 'UnrealEditor-Cmd.exe'), '-platform=Win64', '-clientconfig=Shipping',
        '-cook', '-build', '-stage', '-package', '-pak', '-iostore', '-compressed', '-prereqs', '-archive', '-archivedirectory=' + out]
P = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=0x08000000, cwd=os.path.dirname(uat))
open(r'C:\Users\hossa\Documents\agent-office\_package_info.txt', 'w').write('PID %d\n%s\n%s' % (P.pid, proj, ' '.join(args)))
print('PACKAGE STARTED', P.pid, proj)
