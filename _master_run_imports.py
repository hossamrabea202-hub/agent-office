import unreal, runpy, traceback, time, os
ROOT = r'C:\Users\hossa\Documents\agent-office'
L3 = os.path.join(ROOT, '_latest')
OUT = os.path.join(ROOT, '_master_results.txt')
JOBS = [('172','assets/laptop2/GroundKit/import_ground_ue.py'),
 ('233','assets/checkking/Weapons/import_weapons_ue.py'),
 ('240','assets/tga/ZombieV2/import_zombiev2_ue.py'),
 ('242','assets/tga/OreShed/import_oreshed_ue.py'),
 ('243','assets/tga/Fence/import_fence_ue.py'),
 ('244','assets/tga/Rocks/import_rocks_ue.py'),
 ('245','assets/tga/Trough/import_trough_ue.py'),
 ('246','assets/tga/Signs/import_signs_ue.py'),
 ('247','assets/tga/MinerGear/import_minergear_ue.py'),
 ('248','assets/tga/MedicGear/import_medicgear_ue.py'),
 ('249','assets/tga/SiegeDebris/import_debris_ue.py'),
 ('250','assets/tga/RealmDressing/import_realmdressing_ue.py'),
 ('251','assets/tga/SiegeEngines/import_siege_ue.py'),
 ('252','assets/tga/FarmCrops/import_farm_ue.py'),
 ('253','assets/tga/Feast/import_feast_ue.py')]
RES = []
def w(): open(OUT, 'w').write('\n'.join(RES))
for n, p in JOBS:
    t = time.time()
    try:
        runpy.run_path(os.path.join(L3, *p.split('/')), run_name='__main__')
        RES.append('%s OK %.0fs' % (n, time.time() - t))
    except BaseException:
        RES.append('%s FAIL %s' % (n, traceback.format_exc()[-700:]))
    w()
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True); RES.append('SAVED')
except BaseException:
    RES.append('SAVE FAIL ' + traceback.format_exc()[-300:])
w(); print('BATCH DONE')
