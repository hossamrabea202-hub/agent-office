import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
c = [x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
m = [x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
open(os.path.join(D, 'dirty.txt'), 'w').write('content %s maps %s' % (c, m))
