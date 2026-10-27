import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
p = open(os.path.join(D, 'open_target.txt')).read().strip()
bp = unreal.load_asset(p)
ok = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
open(os.path.join(D, 'open_bp.txt'), 'w').write('opened %s %s' % (p, ok))
