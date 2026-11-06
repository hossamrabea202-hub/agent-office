# fb2_layer.py - Flesh Brute "creature performance layer" (#449 anim polish), adjustedfilm (Claude), 2026-11-06.
# Pure Python (no numpy, no unreal): the UE script reads poses, this module returns new local poses.
# A pose = list (per bone) of [px,py,pz, qx,qy,qz,qw, sx,sy,sz] in the bone's LOCAL space (UE conventions).
#
# Layers (film/VFX creature rules, see RESEARCH.md):
#   1 jaw performance   - the maw is alive: breathing gape, anticipation gape -> snap at the strike, slack on hit/death, roar on burst
#   2 tongue overlap    - tongue lags the head and curls with the jaw (follow-through)
#   3 flesh jiggle      - belly/side/breast/butt spring-damper on the parent's motion, low frequency = big mass
#   4 heft              - footfall shock travels up the spine to the head (Pacific Rim: Uprising "Heft" layer); head/neck lag
#   5 retime            - attacks: slow wind-up, fast strike, slow settle; strike frame and clip length unchanged
import math

# ---------------- quaternion / vector helpers (x, y, z, w) ----------------
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by,
            aw*by - ax*bz + ay*bw + az*bx,
            aw*bz + ax*by - ay*bx + az*bw,
            aw*bw - ax*bx - ay*by - az*bz)
def qinv(q): return (-q[0], -q[1], -q[2], q[3])
def qnorm(q):
    n = math.sqrt(sum(c*c for c in q)) or 1.0
    return tuple(c/n for c in q)
def qrot(q, v):
    p = qmul(qmul(q, (v[0], v[1], v[2], 0.0)), qinv(q)); return (p[0], p[1], p[2])
def qaxis(axis, deg):
    a = math.radians(deg)*0.5; s = math.sin(a); n = vlen(axis) or 1.0
    return (axis[0]/n*s, axis[1]/n*s, axis[2]/n*s, math.cos(a))
def vadd(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def vsub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vmul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def vdot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def vcross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def vlen(a): return math.sqrt(vdot(a, a))
def vnorm(a):
    n = vlen(a) or 1.0; return (a[0]/n, a[1]/n, a[2]/n)
def qlog(q):  # rotation vector (radians)
    q = qnorm(q)
    if q[3] < 0: q = tuple(-c for c in q)
    s = math.sqrt(q[0]**2+q[1]**2+q[2]**2)
    if s < 1e-9: return (0.0, 0.0, 0.0)
    ang = 2*math.atan2(s, q[3]); return (q[0]/s*ang, q[1]/s*ang, q[2]/s*ang)
def qexp(v):
    ang = vlen(v)
    if ang < 1e-9: return (0.0, 0.0, 0.0, 1.0)
    return qaxis(v, math.degrees(ang))
def smooth(x): x = max(0.0, min(1.0, x)); return x*x*(3-2*x)

# ---------------- forward kinematics ----------------
def fk(pose, parents):
    """component-space (pos, rot) per bone; parents[i] = parent index or -1 (bones are in parent-first order)."""
    out = [None]*len(pose)
    for i, t in enumerate(pose):
        lp = (t[0]*1.0, t[1]*1.0, t[2]*1.0); lq = (t[3], t[4], t[5], t[6])
        p = parents[i]
        if p < 0: out[i] = (lp, lq); continue
        pp, pq = out[p]; ps = pose[p][7:10]
        out[i] = (vadd(pp, qrot(pq, (lp[0]*ps[0], lp[1]*ps[1], lp[2]*ps[2]))), qmul(pq, lq))
    return out

def apply_world_delta(pose, wl, parents, i, dq):
    """rotate bone i by component-space delta dq about its own pivot (children follow through FK)."""
    p = parents[i]
    pq = wl[p][1] if p >= 0 else (0.0, 0.0, 0.0, 1.0)
    nw = qmul(dq, wl[i][1])
    nl = qnorm(qmul(qinv(pq), nw))
    t = list(pose[i]); t[3:7] = list(nl); pose[i] = t

def add_local_offset_world(pose, wl, parents, i, dv):
    """translate bone i by a component-space vector dv."""
    p = parents[i]; pq = wl[p][1] if p >= 0 else (0.0, 0.0, 0.0, 1.0)
    ps = pose[p][7:10] if p >= 0 else (1, 1, 1)
    lv = qrot(qinv(pq), dv); t = list(pose[i])
    t[0] += lv[0]/ps[0]; t[1] += lv[1]/ps[1]; t[2] += lv[2]/ps[2]; pose[i] = t

# ---------------- springs ----------------
class Spring:
    """critically-tunable damped spring on a vector; driven by the target's motion (lag = offset)."""
    def __init__(self, hz, zeta):
        self.w = 2*math.pi*hz; self.z = zeta; self.x = None; self.v = (0.0, 0.0, 0.0)
    def step(self, target, tvel, dt, sub=4):
        # damping acts on the velocity RELATIVE to the target: steady motion gives no lag, only acceleration
        # (footfalls, swings, stops) throws the flesh - flesh is attached, it does not trail behind.
        if self.x is None: self.x = target; self.v = tvel
        h = dt/sub
        for _ in range(sub):
            a = vsub(vmul(vsub(target, self.x), self.w*self.w), vmul(vsub(self.v, tvel), 2*self.z*self.w))
            self.v = vadd(self.v, vmul(a, h)); self.x = vadd(self.x, vmul(self.v, h))
        return vsub(self.x, target)

def run_spring(targets, hz, zeta, dt, loop):
    """offset (lag) per frame; for loops the sim runs 3 times round so the cycle is seamless."""
    s = Spring(hz, zeta); n = len(targets); out = [None]*n
    vel = [vmul(vsub(targets[(f+1) % n if loop else min(n-1, f+1)], targets[(f-1) % n if loop else max(0, f-1)]), 0.5/dt) for f in range(n)]
    passes = 3 if loop else 1
    for p in range(passes):
        for f in range(n):
            o = s.step(targets[f], vel[f], dt)
            if p == passes-1: out[f] = o
    return out

# ---------------- clip classification ----------------
def classify(name):
    n = name.lower()
    for k, c in [('attack', 'attack'), ('taking_damage', 'hit'), ('_hit', 'hit'), ('death', 'death'), ('burst', 'burst'),
                 ('laying', 'laying'), ('impaled', 'laying'), ('crawl', 'crawl'), ('run', 'loco'), ('walk', 'loco'), ('idle', 'idle')]:
        if k in n: return c
    return 'idle'
LOOPING = ('loco', 'idle', 'crawl', 'laying')

# ---------------- the rig facts this layer needs ----------------
FLESH = {  # bone: (hz, damping ratio, gain, max cm)   - bigger mass = lower frequency, more lag
    # tuned on the real clips (the pelvis swings hard, up to 170 cm/s even in the walk): walk p90 ~2-3 cm, hits/attacks up to ~6 cm
    'belly_C': (3.0, 0.35, 1.0, 6.0), 'belly_L': (3.3, 0.38, 0.9, 5.0), 'belly_R': (3.3, 0.38, 0.9, 5.0),
    'side_L': (3.8, 0.42, 0.8, 3.5), 'side_R': (3.8, 0.42, 0.8, 3.5),
    'breast_L': (3.4, 0.36, 0.9, 4.5), 'breast_R': (3.4, 0.36, 0.9, 4.5),
    'butt_L': (4.0, 0.45, 0.7, 3.5), 'butt_R': (4.0, 0.45, 0.7, 3.5)}
TONGUE = ['tongue_03', 'tongue_02', 'tongue_01']
# The artist's rest pose is the showcase gape (maw wide open). JAW_CLOSED is the rotation (deg, opening sign) that
# brings the lower jaw up to closed; the jaw curve below is "degrees open from closed", so 0 = shut, ~-JAW_CLOSED = rest gape.
JAW_CLOSED = -50.0   # measured on the real mesh (Blender profile renders, 2026-11-06): teeth meet at 50 deg
JAW_SIGN = None       # None = auto; +1/-1 forces the opening direction

class Rig:
    def __init__(self, bones, parents):
        self.bones = bones; self.parents = parents; self.ix = {b: i for i, b in enumerate(bones)}
    def i(self, b): return self.ix[b]

def strike_frame(world, rig, n, dt):
    """frame of the fastest hand (the hit lands about there)."""
    best, bf = -1.0, int(n*0.5)
    for f in range(1, n):
        for h in ('hand_L', 'hand_R'):
            v = vlen(vsub(world[f][rig.i(h)][0], world[f-1][rig.i(h)][0]))/dt
            if v > best and 0.15*n < f < 0.9*n: best, bf = v, f
    return bf

def footfalls(world, rig, n, dt):
    """foot plants: a foot's height reaches a local minimum after moving down fast."""
    up = updir(world[0], rig); out = []
    for foot in ('foot_L', 'foot_R'):
        h = [vdot(world[f][rig.i(foot)][0], up) for f in range(n)]
        lo = min(h); hi = max(h)
        if hi-lo < 1.5: continue
        for f in range(2, n-1):
            vin = (h[f]-h[f-2])/(2*dt)
            if h[f] <= h[f-1] and h[f] <= h[f+1] and h[f] < lo+0.4*(hi-lo) and vin < -0.6*(hi-lo):
                if not out or min(abs(f-o) for o in out) > 4: out.append(f)
        if not any(abs(h[o]-lo) < 0.4*(hi-lo) for o in out if 0 <= o < n) and hi-lo > 4.0:
            out.append(min(range(n), key=lambda f: h[f]))   # slow gait: at least the lowest point of each foot
    return sorted(set(out))

def updir(w0, rig):
    a = vmul(vadd(w0[rig.i('foot_L')][0], w0[rig.i('foot_R')][0]), 0.5)
    return vnorm(vsub(w0[rig.i('head')][0], a))

def lateral(w, rig):
    return vnorm(vsub(w[rig.i('upper_arm_01_L')][0], w[rig.i('upper_arm_01_R')][0]))

def head_lateral(w, rig):
    """the skull's own left-right axis (fixed in the head bone, measured once on the rest/first pose)."""
    if getattr(rig, 'lat_head', None) is None:
        rig.lat_head = qrot(qinv(w[rig.i('head')][1]), lateral(w, rig))
    return vnorm(qrot(w[rig.i('head')][1], rig.lat_head))

# ---------------- jaw performance curve (degrees of opening) ----------------
def jaw_curve(cat, n, dt, strike, plants, seed):
    T = n*dt; out = []
    rnd = (math.sin(seed*12.9898)*43758.5453) % 1.0
    cyc = max(1, round(T/3.4)); per = T/cyc   # breathing period divides the clip -> seamless loops
    for f in range(n):
        t = f*dt
        breath = 0.5-0.5*math.cos(2*math.pi*t/per)          # 0..1, slow inhale/exhale
        quiver = 0.6*math.sin(2*math.pi*8.3*t+rnd*6)+0.4*math.sin(2*math.pi*11.7*t+rnd*3)  # living tremble
        if cat in ('idle', 'loco', 'crawl'):
            a = 5.0+9.0*breath+0.5*quiver*breath                                   # lips parted, teeth showing, slow breath
        elif cat == 'laying':
            a = 6.0+6.0*breath
        elif cat == 'attack':
            ts = strike*dt; t0 = ts*0.30
            if t < t0: a = 5.0+3.0*breath
            elif t < ts-0.10: a = 5.0+57.0*smooth((t-t0)/max(0.05, ts-0.10-t0))+1.5*quiver   # anticipation gape past the showcase pose (telegraph)
            elif t < ts+0.03: a = 62.0*(1-smooth((t-(ts-0.10))/0.13))+1.0                   # SNAP shut on the strike
            else:
                k = t-(ts+0.03); a = 2.0+12.0*(1-math.exp(-k/0.25))*math.exp(-k/1.4)+6.0*smooth(k/0.8)   # slack, panting
        elif cat == 'hit':
            a = 8.0+28.0*math.exp(-t/0.35)*abs(math.cos(2*math.pi*t*2.2))+6.0*smooth(t/0.4)
        elif cat == 'death':
            a = 6.0+34.0*smooth(t/(T*0.6))+3.0*math.exp(-t/0.3)*math.sin(2*math.pi*t*3)
        elif cat == 'burst':
            a = 4.0+62.0*smooth((t-T*0.25)/(T*0.25))*(1-0.6*smooth((t-T*0.75)/(T*0.2)))+2.0*quiver   # roar
        else:
            a = 6.0
        out.append(a)
    for p in plants:   # flesh inertia: the heavy jaw drops a little on every footfall
        for f in range(p, min(n, p+12)):
            k = (f-p)*dt; out[f] += 3.2*math.exp(-k/0.12)*math.sin(math.pi*min(1.0, k/0.10)+0.3)
    return out

# ---------------- retime (attacks): slow wind-up, fast strike, slow settle; anchors 0, strike, end ----------------
def retime_times(n, dt, strike, amount=0.45):
    """returns the source time to sample for each output frame."""
    T = (n-1)*dt; ts = strike*dt; out = []
    for f in range(n):
        t = f*dt
        if t <= ts:
            u = t/ts if ts > 0 else 1.0
            w = u**(1.0+amount)                       # ease-in: lingers in the wind-up, then whips into the strike
        else:
            u = (t-ts)/(T-ts) if T > ts else 1.0
            w = 1.0-(1.0-u)**(1.0+amount*0.6)         # ease-out: fast follow-through, long heavy settle
        out.append(w*ts if t <= ts else ts+w*(T-ts))
    return out

# ---------------- de-pop: the retargeted zombie clips snap up to 99 deg in ONE frame at their start ----------------
def qdeg(a, b):
    d = abs(a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3]); return math.degrees(2*math.acos(min(1.0, d)))
def qslerp(a, b, t):
    d = a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3]
    if d < 0: b = tuple(-c for c in b); d = -d
    if d > 0.9995: return qnorm(tuple(a[i]+(b[i]-a[i])*t for i in range(4)))
    th = math.acos(d); s = math.sin(th)
    return tuple((math.sin((1-t)*th)*a[i]+math.sin(t*th)*b[i])/s for i in range(4))
def depop(poses, limit=25.0, passes=4):
    """where any bone turns more than `limit` deg in one frame, ease that frame toward its neighbours (local rotations).
    Fast but readable motion is kept; only single-frame snaps are softened. Returns (poses, frames touched)."""
    n = len(poses); touched = set()
    for _ in range(passes):
        bad = [f for f in range(1, n) if any(qdeg(tuple(poses[f][i][3:7]), tuple(poses[f-1][i][3:7])) > limit for i in range(len(poses[f])))]
        if not bad: break
        new = [[list(t) for t in p] for p in poses]
        for f in bad:
            for g in (f-1, f):
                if 0 < g < n-1:
                    touched.add(g)
                    for i in range(len(poses[g])):
                        a = tuple(poses[g-1][i][3:7]); b = tuple(poses[g+1][i][3:7]); c = tuple(poses[g][i][3:7])
                        mid = qslerp(a, b, 0.5); new[g][i][3:7] = list(qslerp(c, mid, 0.6))
        poses = new
    return poses, sorted(touched)

# ---------------- the bake ----------------
def bake(name, poses, rig, dt, seed=1.0, strength=1.0, jaw_axis_sign=None):
    """poses: list of frames (each a list of local transforms). Returns (new poses, report dict)."""
    cat = classify(name); n = len(poses); loop = cat in LOOPING
    P = rig.parents
    poses, popped = depop(poses)
    world = [fk(p, P) for p in poses]
    up = updir(world[0], rig)
    strike = strike_frame(world, rig, n, dt) if cat == 'attack' else -1
    plants = footfalls(world, rig, n, dt) if cat in ('loco', 'attack', 'crawl') else []
    jaw = jaw_curve(cat, n, dt, strike, plants, seed)
    ij = rig.i('jaw'); itip = rig.i('tongue_01')
    # jaw opening sign: opening must move the tongue tip AWAY from the skull (down/out of the mouth).
    if jaw_axis_sign is None: jaw_axis_sign = JAW_SIGN or getattr(rig, 'jaw_sign', None)
    if jaw_axis_sign is None:
        # decided ONCE per rig, on the calibration pose (rig.calib = an upright idle frame), in the skull's own frame
        cal = getattr(rig, 'calib', None) or poses[0]; wc = fk(cal, P)
        lat = head_lateral(wc, rig); upc = updir(wc, rig)
        def tip_after(sign):
            test = [list(t) for t in cal]; ww = fk(test, P)
            apply_world_delta(test, ww, P, ij, qaxis(lat, 25*sign)); return fk(test, P)[itip][0]
        # this rig's tongue sits ABOVE the jaw hinge (the hinge is low in the throat), so when the lower jaw drops
        # the tongue swings FORWARD, away from the back of the neck (checked on the real mesh in Blender, 2026-11-06).
        back = wc[rig.i('spine_04')][0]
        d_pos = vlen(vsub(tip_after(+1), back)); d_neg = vlen(vsub(tip_after(-1), back))
        jaw_axis_sign = +1 if d_pos > d_neg else -1
        rig.jaw_sign = jaw_axis_sign
    out = [[list(t) for t in p] for p in poses]
    # heft: footfall shock that travels up the body, plus head/neck follow-through on spine_04's motion
    shock = [0.0]*n
    for p in plants:
        for f in range(p, n):
            k = (f-p)*dt
            if k > 0.6: break
            shock[f] += math.exp(-k/0.16)*math.sin(2*math.pi*k*2.6+0.4)
    if loop and plants:  # wrap the tail of late plants onto the start
        for p in plants:
            for f in range(0, n):
                k = (f+n-p)*dt
                if k > 0.6: break
                shock[f] += math.exp(-k/0.16)*math.sin(2*math.pi*k*2.6+0.4)
    i4 = rig.i('spine_04'); ineck = rig.i('neck'); ihead = rig.i('head')
    # head lag spring on the chest's rotation vector (angles in degrees, via positions of a point ahead of the chest)
    chest_pts = []
    for f in range(n):
        cp, cq = world[f][i4]; chest_pts.append(vadd(cp, qrot(cq, (0.0, 30.0, 0.0))))
    lag = run_spring(chest_pts, 1.6, 0.45, dt, loop)
    # flesh springs
    flesh_off = {}
    for b, (hz, z, g, mx) in FLESH.items():
        if b not in rig.ix: continue
        tr = [world[f][rig.i(b)][0] for f in range(n)]
        offs = run_spring(tr, hz, z, dt, loop)
        flesh_off[b] = [vmul(o, g*strength) for o in offs]
        for f in range(n):   # soft limit (no flat spots like a hard clamp)
            o = flesh_off[b][f]; L = vlen(o)
            if L > 1e-6: flesh_off[b][f] = vmul(o, mx*math.tanh(L/mx)/L)
    # tongue spring: lag of the tongue base's motion, turned into a rotation
    tbase = [world[f][rig.i('tongue_03')][0] for f in range(n)]
    toff = run_spring(tbase, 2.2, 0.28, dt, loop)
    for f in range(n):
        pose = out[f]
        lat = lateral(world[f], rig)
        fwd = vnorm(vcross(up, lat))
        # 4 heft: shock nods spine_03 -> neck -> head with growing delay is approximated by growing amplitude
        s = shock[f]*strength
        ww = fk(pose, P)
        for b, amp in (('spine_02', 1.0), ('spine_03', 1.4), ('neck', 2.0), ('head', 2.6)):
            apply_world_delta(pose, ww, P, rig.i(b), qaxis(lat, amp*s)); ww = fk(pose, P)
        # head follow-through: the head lags the chest (opposite to the chest's motion), max ~7 deg
        lo = lag[f]
        lp = vsub(lo, vmul(up, vdot(lo, up)*0.5))
        ang = max(-7.0, min(7.0, vdot(lp, lat)*-0.45*strength)); ang2 = max(-7.0, min(7.0, vdot(lp, up)*0.45*strength))
        apply_world_delta(pose, ww, P, ineck, qmul(qaxis(up, ang*0.5), qaxis(lat, ang2*0.5))); ww = fk(pose, P)
        apply_world_delta(pose, ww, P, ihead, qmul(qaxis(up, ang*0.6), qaxis(lat, ang2*0.6))); ww = fk(pose, P)
        # 1 jaw (about the skull's own hinge axis)
        lat = head_lateral(ww, rig); fwd = vnorm(vcross(up, lat))
        apply_world_delta(pose, ww, P, ij, qaxis(lat, (JAW_CLOSED + jaw[f])*jaw_axis_sign*strength)); ww = fk(pose, P)
        # 2 tongue: curls down with the gape, flops with its own lag
        tl = toff[f]
        flop = max(-14.0, min(14.0, vdot(tl, up)*-1.6)); sway = max(-10.0, min(10.0, vdot(tl, lat)*1.6))
        for k, b in enumerate(TONGUE):
            if b not in rig.ix: continue
            w = (k+1)/3.0
            d = qmul(qaxis(lat, (jaw[f]*0.18*w + flop*w)*jaw_axis_sign*strength), qaxis(fwd, sway*w*strength))
            apply_world_delta(pose, ww, P, rig.i(b), d); ww = fk(pose, P)
        # 3 flesh
        for b, offs in flesh_off.items():
            add_local_offset_world(pose, ww, P, rig.i(b), offs[f])
        # breathing swell of the belly (scale), synced with the jaw's breath
        if 'belly_C' in rig.ix:
            T = n*dt; cyc = max(1, round(T/3.4)); per = T/cyc
            br = 0.5-0.5*math.cos(2*math.pi*f*dt/per)
            t = pose[rig.i('belly_C')]; sc = 1.0+0.035*br*strength
            pose[rig.i('belly_C')] = t[:7]+[t[7]*sc, t[8]*sc, t[9]*sc]
    rep = {'cat': cat, 'frames': n, 'depop_frames': popped, 'strike': strike, 'plants': plants, 'jaw_sign': jaw_axis_sign,
           'jaw_min': round(min(jaw), 1), 'jaw_max': round(max(jaw), 1),
           'flesh_max_cm': round(max((vlen(o) for v in flesh_off.values() for o in v), default=0), 2),
           'flesh_p90_cm': {b: round(sorted(vlen(o) for o in v)[int(0.9*(len(v)-1))], 2) for b, v in flesh_off.items() if b in ('belly_C', 'breast_L', 'butt_L')},
           'flesh_maxframe': {b: max(range(n), key=lambda f: vlen(v[f])) for b, v in flesh_off.items() if b == 'belly_C'}}
    return out, rep
