# #451 seam fix (i5, 2026-11-03). Applies the moves proposed by seam_scan_ue.py (seam_findings.json, same folder):
#   GAP    slide the smaller piece into the bigger one (slit closed, 3 cm overlap = a joint inside the overlap)
#   ZFIGHT push the smaller piece 0.8 cm behind the shared face (the bigger face always wins, no flicker)
#   FLOAT  lower the piece onto the ground + 10 cm into it (real walls sit in the ground, RESEARCH_seams.md)
# Never touches decals / decal cards (the scan already skips them), gameplay actors (gate, cannons, stairs, BP_*), or any
# move longer than 30 cm. One move per actor (the first, worst finding). Does NOT save: the Master saves after a look.
#   py seam_fix_ue.py [--kinds GAP,ZFIGHT,FLOAT] [--max N] --dry-run     list what would move (default)
#   py seam_fix_ue.py [--kinds ...] [--max N] --apply                     move + write seam_fix_backup.json
#   py seam_fix_ue.py --revert                                            put every moved actor back
import json, os, sys, unreal
H = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() and 'gpt-review-polish' in __file__ else \
    'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish'
A = sys.argv[1:]
KINDS = (A[A.index('--kinds') + 1] if '--kinds' in A else 'GAP,ZFIGHT,FLOAT').split(',')
MAX = int(A[A.index('--max') + 1]) if '--max' in A else 9999
PROTECT = ('gate', 'cannon', 'stair', 'step', 'breach', 'door', 'portcullis', 'bridge', 'ladder', 'spawn', 'nav', 'trigger')
BK = os.path.join(H, 'seam_fix_backup.json')
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
by_path = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
log = []
if '--revert' in A:
    bk = json.load(open(BK))
    for path, loc in bk.items():
        a = by_path.get(path)
        if a: a.modify(); a.set_actor_location(unreal.Vector(*loc), False, False); log.append('reverted ' + a.get_actor_label())
        else: log.append('missing ' + path)
    print('\n'.join(log) + '\nreverted %d' % len(bk)); raise SystemExit
F = [f for f in json.load(open(os.path.join(H, 'seam_findings.json'))) if f['kind'] in KINDS and f.get('move_actor')]
done, backup = set(), (json.load(open(BK)) if os.path.exists(BK) and '--apply' in A else {})
n = 0
for f in F:
    if n >= MAX: break
    path = f['move_actor']
    if path in done: continue
    a = by_path.get(path)
    if not a: log.append('SKIP missing  %s' % path); continue
    lab = a.get_actor_label().lower()
    if any(k in lab for k in PROTECT) or a.get_class().get_name().startswith('BP_') or a.get_class().get_name() != 'StaticMeshActor':
        log.append('SKIP protect  %-6s %s (%s)' % (f['kind'], a.get_actor_label(), a.get_class().get_name())); continue
    mv = unreal.Vector(*f['move'])
    if mv.length() > 30: log.append('SKIP too far  %-6s %s %.1f cm' % (f['kind'], a.get_actor_label(), mv.length())); continue
    old = a.get_actor_location()
    log.append('%s %-6s %5.1f cm  %-40s move (%.1f, %.1f, %.1f)  vs %s' % ('MOVE' if '--apply' in A else 'WOULD', f['kind'], f['size'],
               a.get_actor_label()[:40], mv.x, mv.y, mv.z, f['b'] if f['a'] == a.get_actor_label() else f['a']))
    if '--apply' in A:
        backup.setdefault(path, [old.x, old.y, old.z])
        a.modify(); a.set_actor_location(old + mv, False, False)
    done.add(path); n += 1
if '--apply' in A: json.dump(backup, open(BK, 'w'), indent=0)
out = '\n'.join(log) + '\n%s %d actors (kinds %s)%s' % ('moved' if '--apply' in A else 'dry run:', n, ','.join(KINDS), '; backup ' + BK if '--apply' in A else '')
open(os.path.join(H, 'seam_fix_log.txt'), 'w', encoding='utf-8').write(out)
print(out)
