# #491 stone kit layout (i5, 2026-11-04). Plain Python 3, no Blender, no editor.
# Turns the box specs (*_specs.json, the same boxes gen_boxmason.py builds) into kit placements: per wall a list of
# kit blocks with centre, yaw, flip and scale, for i9's HISM spawner.
#   python layout_kit491.py [specs.json ...]          default: curtain_specs.json keep_specs.json mason2_specs.json
#   --xforms wall_xforms.json --deck 680              cut curtain walls at the deck (world z, cm): above it is the #488 merlon kit's.
#                                                     wall_xforms.json comes from dump_wall_xforms_ue.py (read-only, i9's map)
#   --cut 'Curtain|Wall'                              regex on the box name: which boxes get the deck cut (the keep never does)
#   writes layout/<specs>_layout.json + layout/report.json, prints a summary per file
# Corner stones (role 'quoin') are ordinary kit blocks: every kit stone is closed, so its end face is finished.
# Same logic as gen_boxmason.masonry(): courses of 0.42-0.56 m, two 0.38 m skins on the long faces, end faces between them,
# full and inset courses alternating (so corner stones bond like quoins), a cap inside the faces on top, a soffit under
# lintels. Difference: every course is filled from the KIT sizes and scaled by at most 8 % to close the span exactly, instead
# of random lengths snapped to the kit afterwards. The randomness is our own (seeded by the spec seed), so the stones won't
# match the ones in today's merged meshes one for one.
# Frame: wall-local = the box pivot (its centre), metres, UE axes (gen_boxmason mirrors Y for the FBX, UE's import mirrors it
# back): x along the box size[0], y along size[1], z up. Yaw 0 = the block's length along +x.
import json, math, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
JOINT = 0.012
KIT_H = (0.42, 0.46, 0.50, 0.55)            # stone heights (m), joint not included
KIT_L = tuple(float(x) for x in os.environ.get('KIT_L', '0.45,0.60,0.75,0.85,0.95').split(','))   # stone lengths (m). 0.85 is added to i9's 4: without it the 0.84 m wall ends need 9 % scale. KIT_L=... to test another set
KIT_D = 0.38                                # stone depth (m)
MAXS = 0.08                                 # scale fit limit, either way


def kit_name(h, l, v): return 'SM_Kit_H%d_L%d_V%d' % (round(h * 100), round(l * 100), v)


def fill(span, r, avoid=(), lengths=KIT_L, tries=300):
    """kit lengths whose pitches (length + joint) fill `span` within +-8 % after one common scale. Joints keep 0.1 m off
    the joints in `avoid` (the course below) where possible. Returns (lengths, scale, ok)."""
    best = None
    for t in range(tries):
        seq, tot = [], 0.0
        while True:
            rest = span - tot
            if rest <= 0: break
            fit = [l for l in lengths if abs(rest / (l + JOINT) - 1) <= MAXS]
            if fit and (rest < max(lengths) + JOINT or r.random() < 0.25):
                seq.append(r.choice(fit)); tot += seq[-1] + JOINT; break
            seq.append(r.choice(lengths)); tot += seq[-1] + JOINT
        s = span / tot; err = abs(s - 1)
        cuts, x = [], 0.0
        for l in seq[:-1]: x += (l + JOINT) * s; cuts.append(x)
        clash = sum(1 for c in cuts for a in avoid if abs(c - a) < 0.1)
        score = (err > MAXS, clash, err)
        if best is None or score < best[0]: best = (score, seq, s)
        if err <= MAXS and clash == 0: break
    (bad, clash, err), seq, s = best
    return seq, s, not bad


def courses(z0, z1, r):
    """kit heights for the courses between z0 and z1, one common vertical scale within +-8 %."""
    n_best = None
    for _ in range(200):
        n = max(1, round((z1 - z0) / (sum(KIT_H) / len(KIT_H) + JOINT)) + r.choice((-1, 0, 0, 1)))
        hs = [r.choice(KIT_H) for _ in range(n)]
        s = (z1 - z0) / sum(h + JOINT for h in hs)
        if abs(s - 1) <= MAXS: return hs, s, True
        if n_best is None or abs(s - 1) < abs(n_best[1] - 1): n_best = (hs, s)
    return n_best[0], n_best[1], False


def layout(spec, cut=None):
    """cut: wall-local z (m) of the deck, or None. Courses stop there; the cap sits just under it."""
    r = random.Random(spec.get('seed', 1103))
    S = [v / 100.0 for v in spec['size']]; H = [v / 2 for v in S]
    out = dict(name=spec['name'], size_cm=spec['size'], blocks=[], special=[], unfit=[])
    if cut is not None:
        out['deck_cut_m'] = round(cut, 4)
        if cut <= -H[2] + 0.05:
            out['special'].append(dict(role='parapet', note='wholly above the deck: #488 merlon kit', size_cm=spec['size'])); return out
    if spec.get('single'):
        out['special'].append(dict(role='single', note='one carved stone: keep its own mesh', size_cm=spec['size'])); return out
    t = spec.get('depth', KIT_D)
    z0, z1 = -H[2], H[2] if cut is None or cut >= H[2] else cut
    top_cap = spec.get('top', True) and not spec.get('coping'); bot = spec.get('bottom', False)
    if top_cap: z1 -= 0.2                                                 # gen_boxmason's cap is 0.2 m thick inside the faces
    if bot: z0 += 0.2
    if z1 - z0 < min(KIT_H) * (1 - MAXS):
        out['special'].append(dict(role='slab', note='thinner than one course: no kit block fits', size_cm=spec['size'])); return out
    hs, sv, okv = courses(z0, z1, r)
    if not okv:                                                           # trim, corbel, string course...: not coursed wall
        out['special'].append(dict(role='trim', note='no whole number of kit courses fits the height (vertical scale %.2f): keep its own mesh' % sv, size_cm=spec['size'])); return out
    # thinner than two skins: one through-stone per course, if the kit depth fits the thickness
    thin = [i for i in (0, 1) if S[i] < 2 * t + 0.12]
    if len(thin) == 2:
        out['special'].append(dict(role='pier', note='thinner than two skins both ways: keep its own mesh', size_cm=spec['size'])); return out
    dscale = 1.0
    if thin:
        dscale = S[thin[0]] / KIT_D
        if abs(dscale - 1) > MAXS:
            out['special'].append(dict(role='thin', note='%.2f m thick: one kit stone is %.2f deep, two are %.2f' % (S[thin[0]], KIT_D, 2 * KIT_D), size_cm=spec['size'])); return out
        faces = (('-y', 0, -H[0], H[0], 0.0, 0),) if thin[0] == 1 else (('-x', 1, -H[1], H[1], 0.0, 270),)
    else:
        faces = (('-y', 0, -H[0], H[0], -H[1] + t / 2, 0), ('+y', 0, -H[0], H[0], H[1] - t / 2, 180),
                 ('-x', 1, -H[1], H[1], -H[0] + t / 2, 270), ('+x', 1, -H[1], H[1], H[0] - t / 2, 90))
    if abs(t - KIT_D) > 1e-6: out['unfit'].append('skin depth %.2f in the spec, kit stones are %.2f' % (t, KIT_D))
    under = {}
    z = z0
    for k, h in enumerate(hs):
        ch = (h + JOINT) * sv; zc = z + ch / 2; xfull = k % 2 == 0
        for face, along, a0, a1, fixed, yaw in faces:
            full = (xfull if along == 0 else not xfull) or bool(thin)      # the long faces and the ends take turns to run through the corner
            lo, hi = (a0, a1) if full else (a0 + t, a1 - t)
            if hi - lo < 0.12: continue
            if hi - lo < min(KIT_L) * (1 - MAXS) + JOINT:                 # shorter than any kit stone: one cut closer
                ctr = ((lo + hi) / 2, fixed, zc) if along == 0 else (fixed, (lo + hi) / 2, zc)
                out['special'].append(dict(role='closer', note='cut stone, shorter than the kit', face=face, centre=[round(q, 4) for q in ctr], len_m=round(hi - lo - JOINT, 4), h_m=round(h * sv, 4)))
                continue
            seq, s, ok = fill(hi - lo, r, [c - lo for c in under.get(face, [])])
            if not ok: out['unfit'].append('%s course %d: span %.3f m, scale %.3f' % (face, k, hi - lo, s))
            x, cuts = lo, []
            for j, l in enumerate(seq):
                p = (l + JOINT) * s; c = x + p / 2
                corner = full and (j == 0 or j == len(seq) - 1)
                v = r.choice((1, 2)); flip = r.random() < 0.5
                ctr = (c, fixed, zc) if along == 0 else (fixed, c, zc)
                b = dict(kit=kit_name(h, l, v), role='quoin' if corner else 'face', face=face,
                         c=[round(q, 4) for q in ctr], yaw=(yaw + (180 if flip else 0)) % 360, flip=flip,
                         scale=[round(s, 4), round(dscale, 4), round(sv, 4)], len_m=round(l * s, 4), h_m=round(h * sv, 4), d_m=round(KIT_D * dscale, 4))
                out['blocks'].append(b); x += p; cuts.append(x)
            under[face] = cuts[:-1]
        z += ch
    inner = [S[0] - 2 * t, S[1] - 2 * t]
    if top_cap and min(inner) > 0.05:
        top = H[2] if cut is None or cut >= H[2] else cut
        out['special'].append(dict(role='cap', note='walk / top surface inside the faces, 0.2 m thick (coping slab or floor kit)', centre=[0, 0, round(top - 0.1, 4)], size_m=[round(inner[0], 3), round(inner[1], 3), 0.2]))
    if bot and min(inner) > 0.05:
        out['special'].append(dict(role='soffit', note='under a lintel, 0.2 m thick', centre=[0, 0, round(-H[2] + 0.1, 4)], size_m=[round(inner[0], 3), round(inner[1], 3), 0.2]))
    return out


def check(w):
    """no two blocks of one wall overlap (boxes shrunk by 2 mm), and how much of each long face the blocks cover."""
    bx = []
    for b in w['blocks']:
        L, Hh = b['len_m'], b['h_m']; along_x = b['face'] in ('-y', '+y')
        D = b.get('d_m', KIT_D); dx, dy = (L / 2, D / 2) if along_x else (D / 2, L / 2)
        bx.append([b['c'][0] - dx + 0.002, b['c'][0] + dx - 0.002, b['c'][1] - dy + 0.002, b['c'][1] + dy - 0.002, b['c'][2] - Hh / 2 + 0.002, b['c'][2] + Hh / 2 - 0.002])
    hits = 0
    order = sorted(range(len(bx)), key=lambda i: bx[i][0])
    for ii, i in enumerate(order):
        for j in order[ii + 1:]:
            if bx[j][0] >= bx[i][1]: break
            if bx[i][2] < bx[j][3] and bx[j][2] < bx[i][3] and bx[i][4] < bx[j][5] and bx[j][4] < bx[i][5]: hits += 1
    return hits


if __name__ == '__main__':
    A = sys.argv[1:]; opt = lambda k, d=None: A[A.index(k) + 1] if k in A else d
    XF = json.load(open(opt('--xforms'))) if opt('--xforms') else {}; DECK = float(opt('--deck', 680)); CUT = re.compile(opt('--cut', 'Curtain|Wall'))
    files = [a for i, a in enumerate(A) if not a.startswith('--') and (i == 0 or A[i - 1] not in ('--xforms', '--deck', '--cut'))] or ['curtain_specs.json', 'keep_specs.json', 'mason2_specs.json']
    def deck_local(s):
        if s['name'] not in XF or not CUT.search(s['name']): return None
        ps = XF[s['name']]; zs = {round(p['loc'][2], 1) for p in ps}
        if len(zs) > 1: print('  note: %s placed at %d heights %s, cut by the first' % (s['name'], len(zs), sorted(zs)))
        p = ps[0]
        if abs(p['rot'][0]) > 0.5 or abs(p['rot'][1]) > 0.5: print('  note: %s is tilted %s, no cut' % (s['name'], p['rot'])); return None
        return (DECK - p['loc'][2]) / p['scale'][2] / 100.0
    os.makedirs(os.path.join(HERE, 'layout'), exist_ok=True)
    rep = {}
    for f in files:
        specs = json.load(open(os.path.join(HERE, f) if not os.path.isabs(f) else f))['boxes']
        walls = [layout(s, deck_local(s)) for s in specs]
        use, worst, unfit, overlaps = {}, 0.0, 0, 0
        for w in walls:
            w['overlaps'] = check(w); overlaps += w['overlaps']; unfit += len(w['unfit'])
            for b in w['blocks']:
                use[b['kit']] = use.get(b['kit'], 0) + 1
                worst = max(worst, *(abs(x - 1) for x in b['scale']))
        name = os.path.splitext(os.path.basename(f))[0]
        json.dump(dict(source=f, joint_m=JOINT, kit=dict(heights=KIT_H, lengths=KIT_L, depth=KIT_D, max_scale=MAXS), walls=walls),
                  open(os.path.join(HERE, 'layout', name + '_layout.json'), 'w'), indent=0)
        rep[name] = dict(deck_cut=sum(1 for w in walls if 'deck_cut_m' in w), walls=len(walls), blocks=sum(len(w['blocks']) for w in walls), specials=sum(len(w['special']) for w in walls),
                         worst_scale=round(worst, 4), unfit=unfit, overlaps=overlaps, kit_use=dict(sorted(use.items(), key=lambda kv: -kv[1])))
        print('%-18s walls %3d  blocks %6d  special %3d  worst scale %.1f %%  unfit %d  overlaps %d' % (name, rep[name]['walls'], rep[name]['blocks'], rep[name]['specials'], worst * 100, unfit, overlaps))
    json.dump(rep, open(os.path.join(HERE, 'layout', 'report.json'), 'w'), indent=1)
