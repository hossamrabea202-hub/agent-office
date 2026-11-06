import runpy, traceback, os, unreal
B = r'C:\Users\hossa\Documents\agent-office\_latest\assets\tga\Obsidian-Sovereign'; R = []
for d, f in (('Forearms', 'import_forearms_ue.py'), ('Thighs', 'import_thighs_ue.py'), ('Waist', 'import_waist_ue.py'), ('UpperArms', 'import_upperarms_ue.py')):
    try: runpy.run_path(os.path.join(B, d, f), run_name='__main__'); R.append(d + ' OK')
    except BaseException: R.append(d + ' FAIL ' + traceback.format_exc()[-400:])
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(r'C:\Users\hossa\Documents\agent-office\_run_obs.txt', 'w').write('\n'.join(R)); print('OBS', R)
