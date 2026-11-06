import unreal
MERGE_DRY = False
exec(compile(open(r'C:\Users\hossa\Documents\agent-office\_merge_stones.py', encoding='utf-8').read(), 'merge', 'exec'))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(r'C:\Users\hossa\Documents\agent-office\_merge_castle_stones.txt', 'a').write('\nSAVED')
print('MERGE APPLIED + SAVED')
