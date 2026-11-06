import json, os, sys, glob, numpy as np
D = sys.argv[1]
def qang(a, b):
    d = abs(np.sum(a*b, axis=-1)); d = np.clip(d, -1, 1); return np.degrees(2*np.arccos(d))
rows = []
for f in sorted(glob.glob(os.path.join(D, '*.json'))):
    j = json.load(open(f)); B = j['bones']; n = j['frames_n']
    L = np.array([fr['l'] for fr in j['frames']])  # n x bones x 10
    ref = np.array(j['ref']) if isinstance(j['ref'], list) else None
    def rng(b):  # max angle from first frame / from ref pose
        i = B.index(b); q = L[:, i, 3:7]
        r = qang(q, q[0:1]).max()
        rr = qang(q, ref[i:i+1, 3:7]).max() if ref is not None else -1
        return r, rr
    W = {k: np.array([fr['w'][k] for fr in j['frames']]) for k in j['frames'][0]['w']}
    pel = W['spine_01'][:, 2]; bob = pel.max()-pel.min()
    hz = (W['hand_L'][:, 2].mean()+W['hand_R'][:, 2].mean())/2
    headz = W['head'][:, 2].mean()
    # head angular speed (deg/frame) p95 = jerkiness
    hi = B.index('head'); hq = L[:, hi, 3:7]
    hs = np.percentile(qang(hq[1:], hq[:-1]), 95) if n > 2 else 0
    # root travel
    rt = W['root'][-1, :3]-W['root'][0, :3]
    ft = W['foot_L'][:, :3]
    rows.append((j['name'], n, rng('jaw'), rng('tongue_01'), rng('belly_C'), rng('breast_L'), round(bob, 1), round(hz/headz, 2), round(hs, 2), np.round(rt, 1), j['root_motion']))
print('clip frames | jaw(vsF0,vsRef) | tongue | belly | breast | pelvisBob cm | handZ/headZ | head p95 deg/frame | root travel | rm')
for r in rows:
    print(r[0].ljust(24), r[1], '| jaw %.1f %.1f' % r[2], '| tng %.1f %.1f' % r[3], '| bel %.1f %.1f' % r[4], '| br %.1f %.1f' % r[5], '| bob', r[6], '| hand/head', r[7], '| headspd', r[8], '| rt', r[9], r[10])
