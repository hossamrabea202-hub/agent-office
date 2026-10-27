# Obsidian Sovereign chest, AAA pilot (checkking). Parametric torso + layered plates, built with numpy + bpy.
# Units: meters, Z up, front = -Y (same as the Codex set). Height 0.476.
import math
import numpy as np
import bpy
import bmesh

H = 0.476
import os
LOW = os.environ.get('CHEST_RES', '1') == '1'
DU, DV, DT, DS = (0.62, 0.42, 0.5, 0.8) if LOW else (1, 1, 1, 1)
PATCH_CENTER = False   # set True by shoulderlib (see patch())

# ---------- smooth profile tables (Catmull-Rom) ----------
def catmull(zs, vs, z):
    zs = np.asarray(zs, float); vs = np.asarray(vs, float)
    z = np.clip(np.asarray(z, float), zs[0], zs[-1])
    i = np.clip(np.searchsorted(zs, z) - 1, 0, len(zs) - 2)
    t = (z - zs[i]) / (zs[i + 1] - zs[i])
    p0 = vs[np.maximum(i - 1, 0)]; p1 = vs[i]; p2 = vs[i + 1]; p3 = vs[np.minimum(i + 2, len(vs) - 1)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)

ZS = [0.000, 0.050, 0.090, 0.170, 0.260, 0.340, 0.400, 0.450, 0.476]
A  = [0.170, 0.148, 0.136, 0.144, 0.162, 0.180, 0.184, 0.175, 0.163]   # half width
BF = [0.122, 0.114, 0.110, 0.124, 0.152, 0.166, 0.160, 0.140, 0.118]   # front depth (breast)
BB = [0.114, 0.107, 0.104, 0.108, 0.118, 0.127, 0.131, 0.128, 0.120]   # back depth
NSE = 2.6  # superellipse exponent

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def surf(phi, z):
    """phi: 0 = front centre (-Y), +pi/2 = +X side, pi = back. Returns (...,3)."""
    phi = np.asarray(phi, float); z = np.asarray(z, float)
    a = catmull(ZS, A, z); bf = catmull(ZS, BF, z); bb = catmull(ZS, BB, z)
    c = np.cos(phi); s = np.sin(phi)
    b = bb + (bf - bb) * smoothstep(-0.25, 0.25, c)
    e = 2.0 / NSE
    x = a * np.sign(s) * np.abs(s) ** e
    y = -b * np.sign(c) * np.abs(c) ** e
    # medial keel on the breast
    keel = 0.0065 * np.exp(-(np.angle(np.exp(1j * phi)) / 0.16) ** 2) * smoothstep(0.13, 0.22, z) * (1 - smoothstep(0.40, 0.47, z))
    y = y - keel
    return np.stack([x, y, z * np.ones_like(x)], -1)

def surf_n(phi, z, d=1e-4):
    p = surf(phi, z)
    dp = surf(phi + d, z) - surf(phi - d, z)
    dz = surf(phi, z + d) - surf(phi, z - d)
    n = np.cross(dz, dp)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    rad = p.copy(); rad[..., 2] = 0
    flip = np.sign(np.sum(n * rad, -1, keepdims=True))
    return n * np.where(flip == 0, 1, flip)

def place(phi, z, off):
    return surf(phi, z) + surf_n(phi, z) * np.asarray(off)[..., None] if np.ndim(off) else surf(phi, z) + surf_n(phi, z) * off

# ---------- mesh helpers ----------
def mesh_obj(name, verts, faces, mat=None, coll=None, uv=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uv is not None:
        lay = me.uv_layers.new(name='UVMap')
        idx = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', idx)
        lay.data.foreach_set('uv', np.asarray(uv, np.float32)[idx].ravel())
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    if mat: ob.data.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    return ob

def grid_faces(nu, nv, wrap_u=False):
    f = []
    for i in range(nu - (0 if wrap_u else 1)):
        i2 = (i + 1) % nu
        for j in range(nv - 1):
            f.append((i * nv + j, i2 * nv + j, i2 * nv + j + 1, i * nv + j + 1))
    return f

def patch(name, phi0, phi1, zb, zt, off, nu, nv, mat=None, coll=None, thick=0.0022):
    """Plate between phi0..phi1, z from zb(phi) to zt(phi), lifted 'off' along the normal. zb/zt: callables."""
    nu, nv = max(4, int(nu * DU)), max(3, int(nv * DV))
    ph = np.linspace(phi0, phi1, nu)
    V = []
    for p in ph:
        z0, z1 = float(zb(p)), float(zt(p))
        zz = np.linspace(z0, z1, nv)
        V.append(place(np.full(nv, p), zz, off))
    V = np.stack(V)  # (nu, nv, 3)
    # true-length unroll: u = arc length along each row, v = arc length up each column (from the plate's lowest point)
    du = np.linalg.norm(np.diff(V, axis=0), axis=-1); dv = np.linalg.norm(np.diff(V, axis=1), axis=-1)
    U = np.concatenate([np.zeros((1, nv)), np.cumsum(du, axis=0)], 0)
    if PATCH_CENTER:
        # dome-like plates: centre each row on the middle column and offset columns by the outline's parameter height
        # (left-aligned rows plus a world-Z offset shear and fold on a cap)
        U = U - U[nu // 2]
        zb0 = np.array([float(zb(p)) for p in ph])
        W = np.concatenate([np.zeros((nu, 1)), np.cumsum(dv, axis=1)], 1) + (zb0 - zb0.min())[:, None]
    else:
        W = np.concatenate([np.zeros((nu, 1)), np.cumsum(dv, axis=1)], 1) + (V[:, :1, 2] - V[:, 0, 2].min())
    uv = np.stack([U, W], -1).reshape(-1, 2)
    ob = mesh_obj(name, V.reshape(-1, 3), grid_faces(nu, nv), mat, coll, uv)
    if thick:
        m = ob.modifiers.new('Solidify', 'SOLIDIFY'); m.thickness = thick; m.offset = -1; m.use_even_offset = True
        m.use_rim = True
    return ob

def tube(name, pts, r, mat=None, coll=None, seg=12, closed=False, flat=1.0, up=None):
    """Sweep a circle (or flattened ellipse) of radius r along pts (N,3)."""
    pts = np.asarray(pts, float)
    if DT < 1 and len(pts) > 16:
        keep = np.unique(np.linspace(0, len(pts) - 1, max(8, int(len(pts) * DT))).astype(int))
        pts = pts[keep]
        if up is not None: up = np.asarray(up, float)[keep]
    seg = max(6, int(seg * DS))
    if up is None: up = np.tile([0, 0, 1.0], (len(pts), 1))
    up = np.asarray(up, float)
    loop = closed
    if loop:   # repeat the first ring at the end so the length UV runs 0..L without wrapping back; welded below
        pts = np.vstack([pts, pts[:1]]); up = np.vstack([up, up[:1]]); closed = False
    N = len(pts)
    T = np.gradient(pts, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    if loop: T[0] = T[-1] = (pts[1] - pts[-2]) / (np.linalg.norm(pts[1] - pts[-2]) + 1e-12)
    B = np.cross(T, up); B /= np.linalg.norm(B, axis=1, keepdims=True) + 1e-12
    Nn = np.cross(B, T)
    # each ring carries a duplicate of its first vertex so the strip unrolls flat (a real UV seam, no folded halves)
    R = seg + 1
    V = []
    for k in range(N):
        for s in range(R):
            a = 2 * math.pi * s / seg
            V.append(pts[k] + r * (math.cos(a) * B[k] + flat * math.sin(a) * Nn[k]))
    F = []
    for k in range(N - (0 if closed else 1)):
        k2 = (k + 1) % N
        for s in range(seg):
            F.append((k * R + s, k * R + s + 1, k2 * R + s + 1, k2 * R + s))
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    uv = np.array([(L[k], 2 * math.pi * r * s / seg) for k in range(N) for s in range(R)])
    if not loop:
        F.append(tuple(range(seg))[::-1]); F.append(tuple((N - 1) * R + s for s in range(seg)))
    ob = mesh_obj(name, V, F, mat, coll, uv)
    # weld the seam for shading (UVs stay split because the loops keep their own UVs)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bm.to_mesh(ob.data); bm.free()
    return ob

def ribbon(name, pts, nrm, w, mat=None, coll=None, thick=0.0004):
    pts = np.asarray(pts, float); nrm = np.asarray(nrm, float)
    T = np.gradient(pts, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    S = np.cross(nrm, T); S /= np.linalg.norm(S, axis=1, keepdims=True) + 1e-12
    V = np.concatenate([pts - S * w / 2, pts + S * w / 2])
    N = len(pts)
    F = [(k, k + 1, N + k + 1, N + k) for k in range(N - 1)]
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    uv = np.concatenate([np.stack([L, np.zeros(N)], 1), np.stack([L, np.full(N, w)], 1)])
    ob = mesh_obj(name, V, F, mat, coll, uv)
    if thick:
        m = ob.modifiers.new('Solidify', 'SOLIDIFY'); m.thickness = thick; m.offset = 1
    return ob

def rivet(name, pos, nrm, r, mat=None, coll=None, seg=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    for v in list(bm.verts):
        if v.co.z < -1e-6: bm.verts.remove(v)
    for v in bm.verts: v.co.z *= 0.55
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); (coll or bpy.context.scene.collection).objects.link(ob)
    if mat: ob.data.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    z = np.asarray(nrm, float); z /= np.linalg.norm(z)
    x = np.cross([0, 0, 1.0], z); x = x / np.linalg.norm(x) if np.linalg.norm(x) > 1e-6 else np.array([1.0, 0, 0])
    y = np.cross(z, x)
    import mathutils
    M = mathutils.Matrix(((x[0], y[0], z[0], pos[0]), (x[1], y[1], z[1], pos[1]), (x[2], y[2], z[2], pos[2]), (0, 0, 0, 1)))
    ob.matrix_world = M
    return ob



