# Shared mesh helpers for the shield builders (extracted from build_heater.py, laptop2 2026-10-29).
import os, math
import bpy, numpy as np
RES = os.environ.get('RES', 'low'); HIGH = RES == 'high'
PI = math.pi
MATS = {}

def mat(name):
    if name not in MATS: MATS[name] = bpy.data.materials.new(name)
    return MATS[name]
def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def vnoise(u, v, s=0):
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b, c, d = _hash(iu, iv, s), _hash(iu + 1, iv, s), _hash(iu, iv + 1, s), _hash(iu + 1, iv + 1, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def fbm(u, v, s, oct=5):
    t, amp, f, tot = 0, 1.0, 1.0, 0
    for o in range(oct):
        t = t + amp * vnoise(u * f, v * f, s + o * 17); tot += amp; amp *= 0.5; f *= 2.03
    return t / tot
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def mesh(name, V, blocks, mname, uv=None, attrs=None, group=None):
    V = np.asarray(V, np.float32).reshape(-1, 3)
    blocks = [np.asarray(b, np.int64) for b in blocks if len(b)]
    idx = np.concatenate([b.ravel() for b in blocks]).astype(np.int32)
    sizes = np.concatenate([np.full(len(b), b.shape[1]) for b in blocks])
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(len(idx)); me.loops.foreach_set('vertex_index', idx)
    me.polygons.add(len(sizes)); me.polygons.foreach_set('loop_start', starts)
    me.update(calc_edges=True)
    me.materials.append(mat(mname))
    if uv is not None:
        lay = me.uv_layers.new(name='UV'); lay.data.foreach_set('uv', np.asarray(uv, np.float32)[idx].ravel())
    for k, a in (attrs or {}).items():
        me.attributes.new(k, 'FLOAT', 'POINT').data.foreach_set('value', np.asarray(a, np.float32))
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if group: ob.vertex_groups.new(name=group).add(list(range(len(V))), 1.0, 'REPLACE')
    return ob
def grid_quads(nr, nc, wrap=False):
    i = np.arange(nr - 1)[:, None]; j = np.arange(nc if wrap else nc - 1)[None, :]
    a = i * nc + j; b = i * nc + (j + 1) % nc
    return np.stack([a, b, b + nc, a + nc], -1).reshape(-1, 4)
def orient(V, Q, want):
    """flip the winding of Q so the summed face normal points along `want`."""
    V = np.asarray(V); q = Q[:: max(1, len(Q) // 400)]
    n = np.cross(V[q[:, 1]] - V[q[:, 0]], V[q[:, 2]] - V[q[:, 0]]).sum(0)
    return Q if np.dot(n, want) > 0 else Q[:, ::-1]
def unit(v): return v / np.linalg.norm(v, axis=-1, keepdims=True)
def sweep(path, up, prof, closed=False, caps=True):
    """prof: (M,2) closed profile in (side, up). Returns V, quads, tris, uv.
    The profile's first column is repeated at the end (and a closed path's first row), so every UV island has a real
    seam instead of a face that wraps back across the whole island (that overlap baked black)."""
    path = np.asarray(path, float)
    t = unit(np.roll(path, -1, 0) - np.roll(path, 1, 0)) if closed else unit(np.gradient(path, axis=0))
    up = unit(up - (up * t).sum(-1, keepdims=True) * t); side = unit(np.cross(t, up))
    if closed:
        path, up, side = np.vstack([path, path[:1]]), np.vstack([up, up[:1]]), np.vstack([side, side[:1]])
    N = len(path); prof = np.vstack([prof, prof[:1]]); M = len(prof)
    V = (path[:, None, :] + prof[None, :, 0, None] * side[:, None, :] + prof[None, :, 1, None] * up[:, None, :]).reshape(-1, 3)
    Q = grid_quads(N, M, False)
    # wind the faces so they point away from the path (the profile's direction decides it otherwise; inward tubes
    # render black through the normal map)
    f = Q[(N // 2) * (M - 1) + (M - 1) // 3] if N > 2 else Q[0]
    nrm = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
    inward = np.dot(nrm, V[f].mean(0) - path[min(N // 2, N - 1)]) < 0
    if inward: Q = Q[:, ::-1]
    pl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))]
    sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    uv = np.stack(np.broadcast_arrays(pl[None, :], sl[:, None]), -1).reshape(-1, 2)
    Tr = np.zeros((0, 3), int)
    if caps and not closed:
        # each end cap gets its own vertices and its own little UV island (the profile shape), so its fan never
        # paints across the side strip's island
        K = M - 1; r0 = V[:K]; r1 = V[(N - 1) * M:(N - 1) * M + K]; pu = prof[:K] - prof[:K].min(0)
        c0 = len(V); V = np.vstack([V, r0, r1, path[0], path[-1]])
        uv = np.vstack([uv, pu, pu, pu.mean(0, keepdims=True), pu.mean(0, keepdims=True)])
        j = np.arange(K); jn = (j + 1) % K; a0, a1, ce0, ce1 = c0, c0 + K, c0 + 2 * K, c0 + 2 * K + 1
        Tr = np.vstack([np.stack([np.full(K, ce0), a0 + jn, a0 + j], -1), np.stack([np.full(K, ce1), a1 + j, a1 + jn], -1)])
        if inward: Tr = Tr[:, ::-1]
    return V, Q, Tr, uv
def rrect(w, h, n, p=6.0):
    a = np.linspace(0, 2 * PI, n, endpoint=False); c, s = np.cos(a), np.sin(a)
    return np.stack([w / 2 * np.sign(c) * np.abs(c) ** (2 / p), h / 2 * np.sign(s) * np.abs(s) ** (2 / p)], -1)
def circ(r, n):
    a = np.linspace(0, 2 * PI, n, endpoint=False); return np.stack([r * np.cos(a), r * np.sin(a)], -1)
def add(parts, V, Q, Tr, uv):
    parts.append((V, Q, Tr, uv))
def emit(name, parts, mname, group=None):
    Vs, Qs, Ts, Us, off = [], [], [], [], 0
    for V, Q, Tr, uv in parts:
        Vs.append(V); Us.append(uv); Qs.append(np.asarray(Q).reshape(-1, 4) + off); Ts.append(np.asarray(Tr).reshape(-1, 3) + off); off += len(V)
    return mesh(name, np.vstack(Vs), [np.vstack(Qs), np.vstack(Ts)], mname, uv=np.vstack(Us), group=group)
def frame_of(n):
    n = unit(np.asarray(n, float)); a = unit(np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0])); return n, a, np.cross(n, a)
def dome(c, n, r, h, nu=14, nv=5):
    """rivet head: a low dome on the surface point c with normal n."""
    n, a, b = frame_of(n)
    th = np.linspace(0, 2 * PI, nu, endpoint=False); ph = np.linspace(0, PI / 2, nv + 1)[:-1]
    R = r * np.cos(ph)[:, None]; Hh = h * np.sin(ph)[:, None] - 0.0004
    V = c + R[..., None] * (np.cos(th)[None, :, None] * a + np.sin(th)[None, :, None] * b) + Hh[..., None] * n
    V = np.vstack([V.reshape(-1, 3), c + n * (h - 0.0004)])
    Q = grid_quads(nv, nu, True); top = len(V) - 1; j = np.arange(nu)
    Tr = np.stack([(nv - 1) * nu + j, (nv - 1) * nu + (j + 1) % nu, np.full(nu, top)], -1)
    return V, Q, Tr, np.zeros((len(V), 2))
def superellipsoid(nlon, nlat, e=0.18):
    th = np.linspace(-PI / 2, PI / 2, nlat + 2)[1:-1]; ph = np.linspace(-PI, PI, nlon, endpoint=False)
    sg = lambda v, m: np.sign(v) * np.abs(v) ** m
    T_, P_ = np.meshgrid(th, ph, indexing='ij')
    V = np.stack([sg(np.cos(T_), e) * sg(np.cos(P_), e), sg(np.cos(T_), e) * sg(np.sin(P_), e), sg(np.sin(T_), e)], -1).reshape(-1, 3)
    V = np.vstack([V, [0, 0, -1], [0, 0, 1]])
    Q = grid_quads(nlat, nlon, True); j = np.arange(nlon); bot, top = len(V) - 2, len(V) - 1
    Tr = np.vstack([np.stack([np.full(nlon, bot), (j + 1) % nlon, j], -1), np.stack([(nlat - 1) * nlon + j, (nlat - 1) * nlon + (j + 1) % nlon, np.full(nlon, top)], -1)])
    return V, Q, Tr
def sqrove(c, n, s, h):
    """square iron washer (rove) with a peened rivet end."""
    n, a, b = frame_of(n)
    V, Q, Tr = superellipsoid(16 if HIGH else 4, 6 if HIGH else 1, 0.25)
    P = c + V[:, 0, None] * a * s / 2 + V[:, 1, None] * b * s / 2 + (V[:, 2, None] * 0.5 + 0.5) * n * h
    return P, Q, Tr, np.stack([P[:, 0], P[:, 2]], -1)

def smart_uv(names):
    """superellipsoid parts got planar UVs whose front and back overlap: give them a real unwrap on the low poly."""
    import bpy, math
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o is None: continue
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
