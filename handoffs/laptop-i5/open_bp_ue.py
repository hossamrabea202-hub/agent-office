# Open one Blueprint editor (i5 helper):  py ".../open_bp_ue.py" /Game/Path/BP_Name   [--close-all first]
import sys, unreal
AES = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
if '--close-all' in sys.argv: [AES.close_all_editors_for_asset(a) for a in AES.get_all_edited_assets()]
paths = [a for a in sys.argv[1:] if a.startswith('/Game/')]
for p in paths: AES.open_editor_for_assets([unreal.load_asset(p)])
unreal.log('i5 open_bp: %s' % paths)
