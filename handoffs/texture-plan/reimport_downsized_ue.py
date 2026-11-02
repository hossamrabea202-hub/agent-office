# #262/#267 texture cut, step 6 (i5 / adjustedfilm, 2026-11-02): re-import ONLY the 307 downsized textures. UE 5.8 Python.
#   py reimport_downsized_ue.py                         DRY RUN (default): match every downsized source PNG to its UE texture
#                                                       (by the texture's import source path) -> reimport_list.txt. Read-only.
#   py reimport_downsized_ue.py --apply --kit laptop2/CampKit [--limit 20]
#                                                       re-imports that kit's matched textures (same asset, same settings:
#                                                       Reimport keeps compression / sRGB / LOD group), saves each one
# Small batches on purpose (i5 rule): one kit per run, --limit caps it. Order by memory saved: see REIMPORT_PLAN.md.
# Textures whose UE size already equals the downsized size are skipped ("already done").
import json, os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
A = sys.argv[1:]
APPLY, KIT = '--apply' in A, (A[A.index('--kit') + 1] if '--kit' in A else None)
LIMIT = int(A[A.index('--limit') + 1]) if '--limit' in A else 10 ** 6
rows = [r for r in json.load(open(os.path.join(HERE, 'audit.json')))['rows'] if r.get('over')]
def key(p):   # import paths were recorded on other machines (C:\Users\hossa\..., D:\...): match on the part from assets/ on
    p = p.replace('\\', '/').lower(); i = p.find('/assets/')
    return p[i + 1:] if i >= 0 else (p if p.startswith('assets/') else '')
want = {key(r['file']): r for r in rows if not KIT or r['kit'] == KIT}
reg = unreal.AssetRegistryHelpers.get_asset_registry()
found, log = {}, []
for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D')):
    if not str(ad.package_path).startswith('/Game/CastleDefender'): continue
    t = ad.get_asset()
    try: src = t.get_editor_property('asset_import_data').get_first_filename()
    except Exception: continue
    k = key(src) if src else ''
    if k and k in want: found.setdefault(k, []).append(t)
done = todo = 0; batch = []
for k, r in sorted(want.items(), key=lambda kv: -(kv[1]['gpu_mb'] - kv[1]['gpu_mb_after'])):
    ts = found.get(k, [])
    if not ts: log.append('NO UE TEXTURE  %-28s %s' % (r['kit'], r['file'])); continue
    for t in ts:
        cur = (t.blueprint_get_size_x(), t.blueprint_get_size_y())
        state = 'done' if cur[0] <= r['target_w'] and cur[1] <= r['target_h'] else 'TODO'
        done += state == 'done'; todo += state == 'TODO'
        log.append('%-4s %-28s %-60s %dx%d -> %dx%d  -%.1f MB' % (state, r['kit'], t.get_path_name().split('.')[0], cur[0], cur[1], r['target_w'], r['target_h'], r['gpu_mb'] - r['gpu_mb_after']))
        if state == 'TODO' and len(batch) < LIMIT: batch.append((t, k))
head = '#267 re-import %s: %d downsized sources%s, %d matched textures already done, %d TODO' % (
    'APPLY' if APPLY else 'DRY RUN', len(want), (' in ' + KIT) if KIT else '', done, todo)
if APPLY:
    if not KIT: raise SystemExit('--apply needs --kit (one kit per run, i5 small-steps rule)')
    tasks = []
    for t, k in batch:
        src = os.path.join(REPO, k)                      # the shrunk file in THIS repo, not the recorded path
        path = t.get_path_name().split('.')[0]
        task = unreal.AssetImportTask()
        for p, v in (('filename', src), ('destination_path', path.rsplit('/', 1)[0]), ('destination_name', path.rsplit('/', 1)[1]),
                     ('replace_existing', True), ('replace_existing_settings', False), ('automated', True), ('save', True)):
            task.set_editor_property(p, v)
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    head += '\nre-imported %d: %s' % (len(tasks), ', '.join(t.get_name() for t, _ in batch))
open(os.path.join(HERE, 'reimport_list.txt'), 'w', encoding='utf-8').write(head + '\n' + '\n'.join(log))
print(head)
