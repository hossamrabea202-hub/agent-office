import unreal, runpy, traceback, os
ROOT = r'C:\Users\hossa\Documents\agent-office'; L3 = os.path.join(ROOT, '_latest')
OUT = os.path.join(ROOT, '_master_results4.txt'); RES = []
try: runpy.run_path(os.path.join(L3, 'assets', 'tga', 'Feast', 'import_feast_ue_fix2.py'), run_name='__main__'); RES.append('253 OK')
except BaseException: RES.append('253 FAIL ' + traceback.format_exc()[-500:])
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True); RES.append('SAVED')
open(OUT, 'w').write('\n'.join(RES)); print('BATCH3 DONE')
