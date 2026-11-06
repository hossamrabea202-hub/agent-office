# #509 step 6b (i5 checkking, 2026-11-05): mud, weeds and moss where the castle walls meet the ground.
import os
#   py place_foot509_ue.py                DRY RUN: finds the wall feet, writes foot_report509.txt
#   py place_foot509_ue.py --apply        spawns (tag FW509, outliner folder CastleFoot509): foot cards + weed clumps, ISM per asset
#   py place_foot509_ue.py --remove       deletes every FW509 actor (the undo)
#   --near <x> <y> <z> <radius>  only near a point (preview);  --temp  card MIs from /Game/_i5tmpWS509 (i5 lookdev)
# Physical causes (KB rule 3): rain splash-back throws soil up the lowest 30-50 cm; that strip stays damp longest, so moss
# grows on the lowest course (more on faces the sun doesn't dry); the strip right against the wall is never trodden or
# grazed, so weeds grow there in clumps (grass tufts, dead stalks, and the two plants of old walls: poppy in the sun, foxglove
# in the shade). Not at doors, gate passages or paved ground.
# No doubling (#461, PERFECT_CASTLE #7): stone that already weathers its foot in the material (family C, M_KeepEntrance_Baked)
# or wears base-grime cards (Tower9) gets weeds only, no card.
import math, random, sys, unreal
args = sys.argv[1:]
SRC = 'C:/Users/hossa/Documents/agent-office/handoffs/castle-weather-504/place_weather504_ue.py'
code = open(SRC, encoding='utf-8').read()
g = {'__name__': 'foot509'}; sys_argv = sys.argv; sys.argv = ['x']
exec(compile(code[:code.index("if '--remove' in args:")], SRC, 'exec'), g); sys.argv = sys_argv     # #504's stone filter, traces, card frames
V, trace, EAS = g['V'], g['trace'], g['EAS']
TAG = 'FW509'
HERE = 'C:/Users/hossa/Documents/agent-office/handoffs/castle-props-509'   # Master: this PC's repo (scripts exec each other without __file__)
MID = '/Game/_i5tmpWS509/' if '--temp' in args else '/Game/CastleDefender/Environment/CastleWeather504/'
MS = '/Game/CastleDefender/AssetPacks/Fab/Megascans/Plants/'
WEEDS = ([('grass', MS + 'Wild_Grass_vczndjqja/Raw/SM_vczndjqja_Var' + c, 0.55, 1.0) for c in 'ABCDEFGH'] +
         [('grass', MS + 'Wild_Grass_vlkhcbxia/Raw/SM_vlkhcbxia_Var' + c, 0.55, 1.0) for c in 'ABCDEFGH'] +
         [('stalks', MS + 'Dead_Shrubs_vdknafgha/Raw/SM_vdknafgha_Var' + c, 0.5, 0.85) for c in 'ABCDEFGH'])
POPPY = ('poppy', '/Game/CastleDefender/Environment/Flora/Poppy/SM_Flora_Poppy', 0.8, 1.1)
FOXGLOVE = ('foxglove', '/Game/CastleDefender/Environment/Flora/Foxglove/SM_Flora_Foxglove', 0.75, 1.05)
COL = 100.0
FEET = []          # (face point, normal, ground z, shade, 'foot' | 'door'): read by place_fittings509_ue.py
random.seed(5096)
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): print('PIE RUNNING: abort'); raise SystemExit


def ground_ok(h):
    if not h or h['n'].z < 0.8: return False
    a = h['comp'].get_owner() if h.get('comp') else None
    lab = (a.get_actor_label() + ' ' + a.get_class().get_name()).lower() if a else ''
    if any(w in lab for w in ('road', 'pave', 'slab', 'stair', 'bridge', 'water', 'walk', 'keepshell', 'threshold', 'kerb', 'landing', 'foundation')): return False
    return any(w in lab for w in ('landscape', 'ground', 'terrain', 'courtyardfloor', 'baileyfloor', 'mud'))     # earth and cobble yards


def plan():
    sun = g['sun_dir'](); gate = None
    for a in EAS.get_all_level_actors():
        if 'gate' in a.get_actor_label().lower() and 'realm' not in a.get_actor_label().lower(): gate = gate or a.get_actor_location()
    cards, weeds, feet = [], [], 0
    comps = g['stone_components'](); stone = {cc[1].get_path_name(): cc for cc in comps}
    seen = set()
    for a, c, o, e, mat in comps:
        for nrm, tan in ((V(1, 0, 0), V(0, 1, 0)), (V(-1, 0, 0), V(0, 1, 0)), (V(0, 1, 0), V(1, 0, 0)), (V(0, -1, 0), V(1, 0, 0))):
            half = abs(tan.x) * e.x + abs(tan.y) * e.y; depth = abs(nrm.x) * e.x + abs(nrm.y) * e.y
            shade = nrm.dot(sun) < -0.15
            for ci in range(max(1, int(2 * half / COL))):
                s = -half + (ci + 0.5) * COL + random.uniform(-15, 15)
                Q = V(o.x, o.y, o.z + e.z + 50) + tan * s + nrm * (depth + 60.0)
                gr = trace(Q, Q - V(0, 0, 4000))
                if not ground_ok(gr) or gr['loc'].z > o.z + e.z - 80.0: continue              # the ground must meet this face (pieces run below it)
                G = gr['loc']
                # the stone face standing on this ground: the first stone hit going in at 25 cm (a plinth / skirt in front counts)
                hw = trace(G + nrm * 20.0 + V(0, 0, 25), G + V(0, 0, 25) - nrm * (depth + 150.0))
                if not hw or not hw.get('comp') or hw['comp'].get_path_name() not in stone or hw['n'].dot(nrm) < 0.6 or hw['dist'] > 150.0: continue
                key = (int(hw['loc'].x // 80), int(hw['loc'].y // 80), int(hw['loc'].z // 80))
                if key in seen: continue                                                       # two pieces' faces on one foot
                seen.add(key)
                op = trace(G + nrm * 20.0 + V(0, 0, 150), G + V(0, 0, 150) - nrm * (depth + 150.0))
                if not op or op['dist'] > hw['dist'] + 30.0:                                   # an opening above: a door / gate passage
                    FEET.append((hw['loc'], hw['n'], G.z, shade, 'door')); continue
                if gate is not None and (V(G.x, G.y, 0) - V(gate.x, gate.y, 0)).length() < 500.0: continue
                ha, hc, ho, he, hmat = stone[hw['comp'].get_path_name()]
                nocard = 'keepentrance_baked' in hmat or ha.get_actor_label().lower().startswith('tower9')
                feet += 1; F = hw['loc']; FEET.append((F, hw['n'], G.z, shade, 'foot'))
                if not nocard and random.random() < 0.8:
                    hgt = random.uniform(65, 95)
                    cards.append(('MI_Foot509_Shade' if shade else 'MI_Foot509_Sun', V(F.x, F.y, G.z + hgt / 2 - 4.0), hw['n'], random.uniform(110, 150), hgt))
                if random.random() < 0.6:
                    for _ in range(random.randint(2, 5)):
                        if random.random() < 0.08: w = FOXGLOVE if shade else POPPY
                        else: w = random.choice(WEEDS)
                        P = F + nrm * random.uniform(4, 40) + tan * random.uniform(-45, 45)
                        gz = trace(P + V(0, 0, 80), P - V(0, 0, 120))
                        if not ground_ok(gz): continue
                        sc = random.uniform(w[2], w[3]) * (1.15 if shade else 1.0)                 # lusher where it stays damp
                        weeds.append((w[1], unreal.Transform(V(P.x, P.y, gz['loc'].z - 2.0), unreal.Rotator(random.uniform(-6, 6), random.uniform(-6, 6), random.uniform(0, 360)), V(sc, sc, sc))))
    return feet, cards, weeds


def spawn(cards, weeds):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); BFL = unreal.SubobjectDataBlueprintFunctionLibrary
    plane = unreal.load_asset('/Engine/BasicShapes/Plane'); made = []

    def ism_actor(label, mesh):
        act = EAS.spawn_actor_from_class(unreal.Actor, V(0, 0, 0))
        act.set_actor_label('FW509_' + label); act.tags = [unreal.Name(TAG)]; act.set_folder_path('CastleFoot509')
        root = sub.k2_gather_subobject_data_for_instance(act)[0]
        hnd, why = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.InstancedStaticMeshComponent))
        ism = BFL.get_object(BFL.get_data(hnd)); ism.set_static_mesh(mesh); ism.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        ism.set_editor_property('can_ever_affect_navigation', False)
        return ism
    by = {}
    for cd in cards: by.setdefault(cd[0], []).append(cd)
    for mi, lst in by.items():
        ism = ism_actor(mi[3:], plane); ism.set_material(0, unreal.load_asset(MID + mi)); ism.set_cast_shadow(False)
        ism.set_editor_property('receives_decals', False); ism.set_editor_property('num_custom_data_floats', 1)
        for mi_, loc, n, w, h in lst:
            i = ism.add_instance(g['card_xform'](mi_, loc, n, w, h, 0.0, False), True); ism.set_custom_data_value(i, 0, random.uniform(0, 97.0), True)
        made.append((mi, len(lst)))
    wb = {}
    for path, t in weeds: wb.setdefault(path, []).append(t)
    for path, ts in wb.items():
        sm = unreal.load_asset(path)
        if not sm: print('MISSING', path); continue
        ism = ism_actor(path.split('/')[-1], sm)
        ism.set_editor_property('world_position_offset_disable_distance', 2500)      # step 2's rule: no sway past 25 m
        for t in ts: ism.add_instance(t, True)
        made.append((path.split('/')[-1], len(ts)))
    return made


if '--remove' in args:
    gone = [x for x in EAS.get_all_level_actors() if TAG in [str(t) for t in x.tags]]
    for x in gone: EAS.destroy_actor(x)
    print('removed', len(gone), 'FW509 actors'); raise SystemExit
if any(TAG in [str(t) for t in x.tags] for x in EAS.get_all_level_actors()): print('FW509 already in the level: --remove first'); raise SystemExit
feet, cards, weeds = plan()
if '--near' in args:
    i = args.index('--near'); c0 = V(*[float(a) for a in args[i + 1:i + 4]]); rad = float(args[i + 4])
    cards = [k for k in cards if (k[1] - c0).length() < rad]; weeds = [w for w in weeds if (w[1].translation - c0).length() < rad]
kinds = {}
for p, t in weeds:
    k = 'poppy' if 'Poppy' in p else 'foxglove' if 'Foxglove' in p else 'stalks' if 'vdknafgha' in p else 'grass'; kinds[k] = kinds.get(k, 0) + 1
head = 'wall-foot columns %d | cards %d (sun %d, shade %d) | weeds %d %s' % (feet, len(cards), sum(1 for k in cards if k[0].endswith('Sun')), sum(1 for k in cards if k[0].endswith('Shade')), len(weeds), kinds)
open(HERE + '/foot_report509.txt', 'w').write(head + '\n' + '\n'.join('%s %.0f %.0f %.0f %dx%d' % (k[0], k[1].x, k[1].y, k[1].z, k[3], k[4]) for k in cards) + '\n')
print(head)
if '--apply' in args or ('--near' in args and '--dry-run' not in args): print('spawned', spawn(cards, weeds))
else: print('dry run: nothing placed')
