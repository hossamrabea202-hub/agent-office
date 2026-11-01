# Close the asset editors of the given assets (i5 helper):  py ".../close_bp_ue.py" /Game/Path/BP_A [/Game/Path/BP_B ...]
import sys, unreal
AES = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
for p in [a for a in sys.argv[1:] if a.startswith('/Game/')]: AES.close_all_editors_for_asset(unreal.load_asset(p))
unreal.log('i5 close_bp: %s' % sys.argv[1:])
