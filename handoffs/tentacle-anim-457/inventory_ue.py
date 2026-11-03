# #457 (i5): read-only inventory of the tentacle creature's animation setup. Aborts if a Play session is running.
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(package_paths=['/Game'], recursive_paths=True)
rows = []
for a in ar.get_assets(f):
    p = str(a.package_name)
    if 'entacle' not in p and 'Scorpion' not in p: continue
    rows.append((str(a.asset_class_path.asset_name), p))
for c, p in sorted(rows): print('%-24s %s' % (c, p))
print('total', len(rows))
