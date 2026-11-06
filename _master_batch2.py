import unreal, runpy, traceback, os, shutil
ROOT = r'C:\Users\hossa\Documents\agent-office'; L3 = os.path.join(ROOT, '_latest')
OUT = os.path.join(ROOT, '_master_results2.txt'); RES = []
def w(): open(OUT, 'w').write('\n'.join(RES))
shutil.copy(os.path.join(ROOT, '_set_texture_budget_apply_nodecals.py'), os.path.join(L3, 'handoffs', 'texture-budget', 'set_texture_budget_apply_nodecals.py'))
JOBS = [('248', 'assets/tga/MedicGear/import_medicgear_ue_fixed.py'), ('251', 'assets/tga/SiegeEngines/import_siege_ue_fixed.py'),
        ('253', 'assets/tga/Feast/import_feast_ue_fixed.py'), ('173', 'assets/laptop2/DecalKit/import_decals_ue.py'),
        ('260', 'handoffs/texture-budget/set_texture_budget_apply_nodecals.py')]
for n, p in JOBS:
    try: runpy.run_path(os.path.join(L3, *p.split('/')), run_name='__main__'); RES.append(n + ' OK')
    except BaseException: RES.append(n + ' FAIL ' + traceback.format_exc()[-500:])
    w()
try:
    tb = open(os.path.join(L3, 'handoffs', 'texture-budget', 'texture_budget.txt')).read()[:1500]; RES.append('BUDGET:\n' + tb)
except BaseException: pass
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True); RES.append('SAVED'); w(); print('BATCH2 DONE')
