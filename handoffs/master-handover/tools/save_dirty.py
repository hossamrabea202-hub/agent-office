import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
left = [x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
open(os.path.join(D, 'save_dirty.txt'), 'w').write('saved %s left %s' % (ok, left))
