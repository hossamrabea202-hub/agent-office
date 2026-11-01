# #242 ore shed + #246 shop signs: place the imported props in the open level (i5 core, 2026-11-01). UE 5.8 Python.
#   py "<repo>/handoffs/props-242-246/place_242_246_ue.py" --list                   read-only: anchor candidates + locations
#   py ".../place_242_246_ue.py" [--apply]                                          dry-run unless --apply
#   py ".../place_242_246_ue.py" --at OreShed X Y Z YAW [--at Sign_Smith X Y Z YAW ...] --apply   explicit spots
#   py ".../place_242_246_ue.py" --remove --apply                                   deletes only what this script placed
# Auto spots: the shed 7 m beside the centroid of the mine carts (#201), front facing them; each sign 2.6 m up on the
# anchor (forge/smith, tavern/inn, shop/Vesna/market), pushed 60 cm out along the anchor's forward axis. Tag Props242_246.
import sys, unreal
A = sys.argv[1:]
LIST, APPLY, REMOVE = '--list' in A, '--apply' in A, '--remove' in A
TAG = 'Props242_246'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
P = {'OreShed': '/Game/CastleDefender/Props/Mine/OreShed/SM_OreShed',
     'Sign_Smith': '/Game/CastleDefender/Props/Town/Signs/SM_Sign_Smith',
     'Sign_Tavern': '/Game/CastleDefender/Props/Town/Signs/SM_Sign_Tavern',
     'Sign_Shop': '/Game/CastleDefender/Props/Town/Signs/SM_Sign_Shop'}
WORDS = {'OreShed': ('cart',), 'Sign_Smith': ('smith', 'forge', 'anvil'), 'Sign_Tavern': ('tavern', 'inn'),
         'Sign_Shop': ('shop', 'vesna', 'market', 'merchant')}
log = ['#242/#246 placement' + ('' if APPLY else ' (DRY RUN: add --apply)')]
actors = EAS.get_all_level_actors()


def cands(key):
    return [a for a in actors if any(w in a.get_actor_label().lower() for w in WORDS[key])
            and not a.get_actor_label().startswith(('Lookdev', TAG)) and TAG not in [str(t) for t in a.tags]]


if REMOVE:
    for a in [a for a in actors if TAG in [str(t) for t in a.tags]]:
        log.append('remove ' + a.get_actor_label())
        if APPLY: EAS.destroy_actor(a)
elif LIST:
    for k in P:
        cs = cands(k)
        log.append('%s: %d candidates' % (k, len(cs)))
        for a in cs[:12]:
            l = a.get_actor_location(); log.append('   %-40s %8.0f %8.0f %7.0f yaw %4.0f' % (a.get_actor_label()[:40], l.x, l.y, l.z, a.get_actor_rotation().yaw))
else:
    spots = {}
    for i, k in enumerate(A):
        if k == '--at' and i + 5 < len(A) + 0 and A[i + 1] in P:
            x, y, z, yaw = (float(v) for v in A[i + 2:i + 6]); spots[A[i + 1]] = (unreal.Vector(x, y, z), yaw)
    for k, path in P.items():
        if k in spots: loc, yaw = spots[k]
        else:
            cs = cands(k)
            if not cs: log.append('%s: no anchor found (use --list, then --at %s X Y Z YAW)' % (k, k)); continue
            if k == 'OreShed':
                c = unreal.Vector(sum(a.get_actor_location().x for a in cs) / len(cs), sum(a.get_actor_location().y for a in cs) / len(cs),
                                  min(a.get_actor_location().z for a in cs))
                loc = c + unreal.Vector(700, 0, 0); yaw = 180.0                       # 7 m east of the carts, open front west
            else:
                a = cs[0]; f = a.get_actor_forward_vector()
                loc = a.get_actor_location() + f * 60.0 + unreal.Vector(0, 0, 260); yaw = a.get_actor_rotation().yaw
        if any(TAG in [str(t) for t in a.tags] and a.get_actor_label() == '%s_%s' % (TAG, k) for a in actors):
            log.append('%s already placed' % k); continue
        log.append('%s at (%.0f, %.0f, %.0f) yaw %.0f' % (k, loc.x, loc.y, loc.z, yaw))
        if APPLY:
            a = EAS.spawn_actor_from_object(unreal.load_asset(path), loc, unreal.Rotator(0, 0, yaw))
            a.set_actor_label('%s_%s' % (TAG, k)); a.tags = [unreal.Name(TAG)]
    if APPLY: log.append('placed. Check in the viewport, nudge by hand if needed, then save the level.')
out = '\n'.join(log); unreal.log(out); print(out)
