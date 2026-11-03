# #451 exact-duplicate fix (i5, 2026-11-03). Finds StaticMeshActors that are EXACT copies of another one (same mesh, same
# materials, same transform within 0.5 cm / 0.1 deg / 0.1 %). Two identical surfaces in one place z-fight: each quad's two
# triangles pick a different copy, so the floor shows a triangle sawtooth (wall walk, shots/v3_walkslab.png). Real masonry
# and AAA kits: one piece per surface. Keeps the copy with the lowest label number, HIDES the others (never deletes):
# hidden in game + in the editor, collision off. Decals / decal cards are never touched (not StaticMeshActors with a
# decal material; skipped by name too). Does NOT save.
#   py dup_fix_ue.py --dry-run      list groups (default)
#   py dup_fix_ue.py --apply        hide the extra copies, write dup_fix_backup.json
#   py dup_fix_ue.py --revert       show them again with their old collision
import json, os, re, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]
BK = H + 'dup_fix_backup.json'
SKIP = ('decal', 'soot', 'grime', 'stain', 'card', 'cd425', 'mud', 'moss', 'algae', 'puddle', 'leaf', 'blood', 'streak')
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
if '--revert' in A:
    bk = json.load(open(BK)); n = 0
    for path, old in bk.items():
        a = acts.get(path)
        if not a: print('missing', path); continue
        a.modify(); a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        a.static_mesh_component.set_visibility(True); a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.cast(old['coll']))
        n += 1
    print('revert: %d shown again' % n); raise SystemExit


def num(label):
    m = re.search(r'(\d+)$', label); return int(m.group(1)) if m else -1


groups = {}
for a in acts.values():
    if a.get_class().get_name() != 'StaticMeshActor': continue
    lab = a.get_actor_label()
    if any(k in lab.lower() for k in SKIP): continue
    c = a.static_mesh_component
    m = c.get_editor_property('static_mesh')
    if not m or not c.is_visible() or a.is_hidden_ed(): continue
    mats = tuple(x.get_path_name() if x else '' for x in c.get_materials())
    if any('decal' in x.lower() for x in mats): continue
    t = c.get_world_transform(); l, r, s = t.translation, t.rotation.rotator(), t.scale3d
    key = (m.get_path_name(), mats, round(l.x * 2), round(l.y * 2), round(l.z * 2), round(r.roll * 10) % 3600, round(r.pitch * 10) % 3600,
           round(r.yaw * 10) % 3600, round(s.x * 1000), round(s.y * 1000), round(s.z * 1000))
    groups.setdefault(key, []).append(a)
dups = [sorted(g, key=lambda a: (num(a.get_actor_label()), a.get_actor_label())) for g in groups.values() if len(g) > 1]
dups.sort(key=lambda g: g[0].get_actor_label())
backup = json.load(open(BK)) if os.path.exists(BK) and '--apply' in A else {}
lines, hidden = [], 0
for g in dups:
    keep, extra = g[0], g[1:]
    lines.append('keep %-28s hide %s  (%s)' % (keep.get_actor_label(), ', '.join(e.get_actor_label() for e in extra), keep.static_mesh_component.get_editor_property('static_mesh').get_name()))
    if '--apply' in A:
        for e in extra:
            c = e.static_mesh_component
            backup.setdefault(e.get_path_name(), {'label': e.get_actor_label(), 'coll': int(c.get_collision_enabled())})
            e.modify(); e.set_actor_hidden_in_game(True); c.set_visibility(False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            hidden += 1
    else:
        hidden += len(extra)
if '--apply' in A: json.dump(backup, open(BK, 'w'), indent=0)
out = '\n'.join(lines) + '\n%s: %d duplicate groups, %d extra copies %s' % ('APPLIED' if '--apply' in A else 'DRY RUN', len(dups), hidden, 'hidden (backup %s)' % BK if '--apply' in A else 'would be hidden')
open(H + 'dup_fix_log.txt', 'w', encoding='utf-8').write(out)
print(out)
