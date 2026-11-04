# Card #487 (i5, 2026-11-04): video memory. i9's editor reports VIDEO MEMORY EXHAUSTED (92 MB over). Audit (vram_tags.csv, read from i5's copy): 132 textures are NeverStream, always fully
# in memory, about 1.1 GB if all loaded; 114 are uncompressed, 647 MB, mostly HUD art. Reads the live values, so what you already capped shows as nothing to do.
#   py textures482_ue.py --dry-run     lists what would change + the estimated saving, changes nothing
#   py textures482_ue.py --apply ui    HUD art from uncompressed to BC7 (same sharpness class, 1/4 of the size): Vesna, Muster, Reveal, Controls
#   py textures482_ue.py --apply world 3D textures: streaming on + 2K cap on the 8K ones (gate oak, meadow grass scan, others)
#   py textures482_ue.py --revert      old values back, from textures482_backup.json
# Look at Vesna's shop + the Barracks after `ui` (text edges). Saves each texture it changes. Aborts in PIE.
import json, os, re, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]; EAL = unreal.EditorAssetLibrary
H = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/vram-482/', 'C:/Users/hossa/Documents/agent-office/handoffs/vram-482/') if os.path.isdir(h))
BK = H + 'textures482_backup.json'
if '--revert' in A:
    d = json.load(open(BK))
    for p, v in d.items():
        t = unreal.load_asset(p); t.set_editor_property('compression_settings', getattr(unreal.TextureCompressionSettings, v['comp'])); t.set_editor_property('never_stream', v['ns']); t.set_editor_property('max_texture_size', v['max']); EAL.save_loaded_asset(t)
    os.remove(BK); print('reverted', len(d)); raise SystemExit
ar = unreal.AssetRegistryHelpers.get_asset_registry()
UI = ('/UI/Trade/', '/UI/Barracks/', '/UI/Reveal/', '/UI/Controls/')
ui, world = [], []
def dims(ad):
    m = re.match(r'(\d+)x(\d+)', str(ad.get_tag_value('Dimensions') or '')); return (int(m[1]), int(m[2])) if m else (0, 0)
for ad in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D')):
    p = str(ad.package_name)
    if not p.startswith('/Game/') or re.search(r'_bak|BACKUP|Backup', p): continue
    w, h = dims(ad); fmt = str(ad.get_tag_value('Format') or ''); ns = str(ad.get_tag_value('NeverStream') or '').lower() == 'true'; mx = int(float(str(ad.get_tag_value('MaxTextureSize') or 0) or 0))
    if any(u in p for u in UI) and fmt == 'B8G8R8A8' and max(w, h) >= 256: ui.append((p, w * h * 4 * 1.33 / 1e6, w * h * 1.33 / 1e6))
    elif '/UI/' not in p and '/Characters/Greystone/' not in p:
        s = w * h * (0.5 if fmt == 'DXT1' else 1) * 1.33 / 1e6
        if max(w, h) >= 8192 and (not mx or mx > 2048): world.append((p, s, s / 16, True))
        elif ns: world.append((p, s, s, False))
print('ui %d: %.0f -> %.0f MB (if all loaded)' % (len(ui), sum(x[1] for x in ui), sum(x[2] for x in ui)))
print('world %d: %.0f -> %.0f MB, 8K capped %d, others just streamable' % (len(world), sum(x[1] for x in world), sum(x[2] for x in world), sum(1 for x in world if x[3])))
for x in sorted(world, key=lambda t: -t[1])[:10]: print('  world %4.0f -> %4.0f %s' % (x[1], x[2], x[0].split('/')[-1]))
if '--apply' not in A: print('dry run: nothing changed'); raise SystemExit
which = A[A.index('--apply') + 1] if len(A) > A.index('--apply') + 1 else ''
if which not in ('ui', 'world'): print('say ui or world'); raise SystemExit
d = json.load(open(BK)) if os.path.exists(BK) else {}
def snap(t, p):
    d.setdefault(p, {'comp': str(t.get_editor_property('compression_settings')).split('.')[-1].split(':')[0], 'ns': t.get_editor_property('never_stream'), 'max': t.get_editor_property('max_texture_size')})
n = 0
for x in (ui if which == 'ui' else world):
    t = unreal.load_asset(x[0])
    if not t: continue
    snap(t, x[0]); json.dump(d, open(BK, 'w'), indent=0)
    if which == 'ui': t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_BC7)
    else:
        t.set_editor_property('never_stream', False)
        if x[3]: t.set_editor_property('max_texture_size', 2048)
    EAL.save_loaded_asset(t); n += 1
print('changed + saved', n, which, '| look + stat streaming, undo --revert')
