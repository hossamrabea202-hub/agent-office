import unreal, subprocess
subprocess.run(['gh', 'issue', 'comment', '266', '--repo', 'hossamrabea202-hub/agent-office', '--body-file', r'C:\Users\hossa\Documents\agent-office\_c266.md'], capture_output=True, text=True, creationflags=0x08000000)
EAL = unreal.EditorAssetLibrary
src = '/Game/ThirdPerson/Maps/ThirdPersonMap'; bk = '/Game/ThirdPerson/Maps/ThirdPersonMap_BACKUP_stones'
ok = EAL.does_asset_exist(bk) or bool(EAL.duplicate_asset(src, bk))
print('BACKUP', ok, EAL.does_asset_exist(bk))
MERGE_DRY = True
exec(compile(open(r'C:\Users\hossa\Documents\agent-office\_merge_stones.py', encoding='utf-8').read(), 'merge', 'exec'))
