import unreal, subprocess, os
ROOT = r'C:\Users\hossa\Documents\agent-office'
BPD = os.path.join(ROOT, '_bp')
os.makedirs(BPD, exist_ok=True)
NOWIN = 0x08000000
def find(name):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')):
        if str(a.asset_name) == name: return str(a.package_name)
def open(name):
    p = find(name); bp = unreal.load_asset(p)
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp]); print('OPENED', p)
def save_clip(name):
    f = os.path.join(BPD, 'live_%s.t3d' % name)
    r = subprocess.run(['powershell', '-NoProfile', '-Command', 'Get-Clipboard -Raw | Out-File -Encoding utf8 -LiteralPath "%s"' % f], capture_output=True, text=True, creationflags=NOWIN)
    print('SAVED_CLIP', f, os.path.getsize(f) if os.path.exists(f) else -1, r.stderr[-200:])
def load_clip(fname):
    f = os.path.join(BPD, fname)
    r = subprocess.run(['powershell', '-NoProfile', '-Command', 'Get-Content -Raw -LiteralPath "%s" | Set-Clipboard' % f], capture_output=True, text=True, creationflags=NOWIN)
    print('CLIP_LOADED', f, os.path.getsize(f), r.stderr[-200:])
def compile_save(name):
    p = find(name); bp = unreal.load_asset(p)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    print('COMPILED_SAVED', name, unreal.EditorAssetLibrary.save_asset(p, only_if_is_dirty=False))
def run(rel):
    import runpy; runpy.run_path(os.path.join(ROOT, '_latest', *rel.split('/')), run_name='__main__'); print('RAN', rel)
