# #267 texture cut, step 7 (i9, 2026-11-02): the downsized sources that reimport_downsized_ue.py could not match by import
# path, matched by FILE NAME instead (T_Foo.png -> the one /Game/CastleDefender texture named T_Foo). UE 5.8 Python.
#   py reimport_byname_ue.py                       DRY RUN: list matches -> reimport_byname_list.txt
#   py reimport_byname_ue.py --apply [--kit K]     re-import every unique, still-oversized match (same asset, same settings)
# Only unique name matches are touched; names with 0 or 2+ textures are listed and skipped.
import json, os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
A = sys.argv[1:]
APPLY, KIT = '--apply' in A, (A[A.index('--kit') + 1] if '--kit' in A else None)
rows = [r for r in json.load(open(os.path.join(HERE, 'audit.json')))['rows'] if r.get('over') and (not KIT or r['kit'] == KIT)]
def key(p):
    p = p.replace('\\', '/'); i = p.lower().find('/assets/')
    return p[i + 1:] if i >= 0 else p
reg = unreal.AssetRegistryHelpers.get_asset_registry()
by_path, by_name = set(), {}
for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D')):
    if not str(ad.package_path).startswith('/Game/CastleDefender'): continue
    by_name.setdefault(str(ad.asset_name).lower(), []).append(ad)
    t = ad.get_asset()
    try: src = t.get_editor_property('asset_import_data').get_first_filename()
    except Exception: src = ''
    if src:
        s = src.replace('\\', '/').lower(); i = s.find('/assets/')
        if i >= 0: by_path.add(s[i + 1:])
log, batch, n = [], [], {'path': 0, 'none': 0, 'many': 0, 'done': 0, 'todo': 0}
for r in rows:
    k = key(r['file'])
    if k.lower() in by_path: n['path'] += 1; continue            # handled by reimport_downsized_ue.py
    stem = os.path.splitext(os.path.basename(k))[0].lower()
    hits = by_name.get(stem, [])
    if not hits: n['none'] += 1; log.append('NONE  %-26s %s' % (r['kit'], k)); continue
    if len(hits) > 1: n['many'] += 1; log.append('MANY  %-26s %s -> %s' % (r['kit'], k, [str(h.package_name) for h in hits])); continue
    t = hits[0].get_asset(); cur = (t.blueprint_get_size_x(), t.blueprint_get_size_y())
    if cur[0] <= r['target_w'] and cur[1] <= r['target_h']: n['done'] += 1; log.append('done  %-26s %s %dx%d' % (r['kit'], hits[0].package_name, *cur)); continue
    n['todo'] += 1; log.append('TODO  %-26s %s %dx%d -> %dx%d' % (r['kit'], hits[0].package_name, cur[0], cur[1], r['target_w'], r['target_h']))
    batch.append((t, k))
head = '#267 by-name %s: %s' % ('APPLY' if APPLY else 'DRY RUN', n)
if APPLY and batch:
    tasks = []
    for t, k in batch:
        path = t.get_path_name().split('.')[0]; task = unreal.AssetImportTask()
        for p, v in (('filename', os.path.join(REPO, k)), ('destination_path', path.rsplit('/', 1)[0]), ('destination_name', path.rsplit('/', 1)[1]),
                     ('replace_existing', True), ('replace_existing_settings', False), ('automated', True), ('save', True)):
            task.set_editor_property(p, v)
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    head += '\nre-imported %d' % len(tasks)
open(os.path.join(HERE, 'reimport_byname_list.txt'), 'w', encoding='utf-8').write(head + '\n' + '\n'.join(log))
print(head)
