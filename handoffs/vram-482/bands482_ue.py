# Card #487 (i5, 2026-11-04). Owner: "we use decals to connect walls to floors, should be replaced with a band like AAA". The stone materials already carry that band
# (DirtBand, GrimeHeight, moss, by world height), so these separate pieces only double it: 875 flat grime strips = 46 % of the castle's visible components, plus wall-base decals.
# This HIDES them group by group (never deletes). Compare look + frame before saving.
#   py bands482_ue.py --dry-run                 counts per group, changes nothing
#   py bands482_ue.py --apply tower             Tower9's grime strips (387)
#   py bands482_ue.py --apply contact           floor-contact strips (510)
#   py bands482_ue.py --apply walldecals        DampTide + YW_Moss_WallBase decals (100)
#   py bands482_ue.py --apply all
#   py bands482_ue.py --revert                  everything back, from bands482_backup.json
# Not saved: look, check `stat unit` + `stat rhi`, then save the map. Kept: torch soot, arch weathering, prop blobs outside these groups. Aborts in PIE.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
H = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/vram-482/', 'C:/Users/hossa/Documents/agent-office/handoffs/vram-482/') if os.path.isdir(h))
BK = H + 'bands482_backup.json'
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
def base_name(m):
    while isinstance(m, unreal.MaterialInstance): m = m.get_editor_property('parent')
    return m.get_name() if m else ''
def is_hidden(a): return a.is_hidden_ed() or a.get_editor_property('hidden')
def set_hidden(a, v):
    a.modify(); a.set_editor_property('hidden', v); a.set_is_temporarily_hidden_in_editor(v)
if '--revert' in A:
    if not os.path.exists(BK): print('NO BACKUP', BK); raise SystemExit
    d = json.load(open(BK)); by = {a.get_path_name(): a for a in actors}; n = 0
    for p in d:
        if p in by: set_hidden(by[p], False); n += 1
        else: print('MISSING', p)
    os.remove(BK); print('reverted', n, 'of', len(d), '- not saved'); raise SystemExit
groups = {'tower': [], 'contact': [], 'walldecals': []}
for a in actors:
    if is_hidden(a): continue
    fold = str(a.get_folder_path())
    if isinstance(a, unreal.DecalActor):
        m = a.get_decal_material() if hasattr(a, 'get_decal_material') else a.decal.get_decal_material()
        n = m.get_name() if m else ''
        if 'DampTide' in n or 'Moss_WallBase' in n: groups['walldecals'].append(a)
        continue
    cs = a.get_components_by_class(unreal.StaticMeshComponent)
    if len(cs) != 1: continue                                        # only plain single-card actors
    mats = [cs[0].get_material(i) for i in range(cs[0].get_num_materials())]
    b = {base_name(m) for m in mats if m}
    if b & {'M_EdgeGrimeCard', 'M_WallBaseGrime'} and fold.startswith('Castle/Tower9'): groups['tower'].append(a)
    elif b & {'M_EdgeGrimeCard', 'M_ContactBlobCard'} and fold.startswith('CastleDefender/FloorDressing'): groups['contact'].append(a)
print('visible actors', len(actors), {k: len(v) for k, v in groups.items()})
if '--apply' not in A: print('dry run: nothing changed'); raise SystemExit
which = A[A.index('--apply') + 1] if len(A) > A.index('--apply') + 1 else ''
sel = list(groups) if which == 'all' else [which] if which in groups else None
if not sel: print('say which group:', list(groups), 'or all'); raise SystemExit
d = json.load(open(BK)) if os.path.exists(BK) else []
n = 0
for k in sel:
    for a in groups[k]: set_hidden(a, True); d.append(a.get_path_name()); n += 1
json.dump(d, open(BK, 'w'), indent=0)
print('hidden', n, 'in', sel, '- NOT saved. Compare look + stat unit / stat rhi, then save the map, or --revert')
