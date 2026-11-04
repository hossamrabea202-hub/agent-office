# Castle Defender - arcaded wall-walk (i9 11-04, Alien: "is that how real architects build castles" -> stone arcade).
# The inner-ward walks overhang the courtyard by 2.8 m on timber cantilevers: no stone corbel carries that. Real
# answer (arcaded rampart, e.g. Carcassonne / Avila inner arcades): a stone arcade at the deck edge - square piers,
# semicircular arches of wedge voussoirs, coursed spandrels and a top course under the deck; the deck beams then rest
# on wall + arcade like any timber floor. World coordinates (cm in, m inside), one mesh per walk, pivot at its origin.
# Run: blender -b -P gen_arcade.py   -> castlestones/arcade_fbx/SM_Arcade_North.fbx, SM_Arcade_South.fbx
import sys, random, math, os, json
sys.path.insert(0, 'C:/Users/hossa/sync58/tunnel')
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix
from gen_boxmason import Buf, rbox, JOINT
J2 = JOINT / 2
OUT = 'C:/Users/hossa/sync58/castlestones/arcade_fbx'; os.makedirs(OUT, exist_ok=True)
NB = 8                                             # bays; equal so every arch springs from the same impost height
X0, X1 = 4.80, 26.80                               # end pier centres (m): clear of the Tower9 drum ... east curtain
PIERS = [X0 + (X1 - X0) * k / NB for k in range(NB + 1)]   # 2.75 m centres; pier 1 at 7.55 clears the chest (5.25-7.0)
PW = 0.70                      # pier width (x) = arcade thickness (y): real square piers
Z_TOP = 6.45                   # deck underside
VS = 0.32                      # voussoir depth (2*VS < PW: both arches' springers fit on one pier)
TOPC = 0.26                    # top course under the deck
CROWN = 0.24                   # one full course between the crowns and the top course (no slivers)
THS = math.radians(25)         # springer (tas-de-charge) height: voussoirs start 25 deg above the springing
SIDES = {'North': dict(y0=30.45, y1=31.15, seed=1151), 'South': dict(y0=3.85, y1=4.55, seed=1152)}   # arcade y range (m)

from gen_boxmason import pick_rect

def prism(B, poly, y0, y1, mat=0, tone=None, damp=0.0):
    """Cut stone: a 2D outline in the arch plane (x, z, metres, counter-clockwise) extruded from y0 to y1. Faces
    get their own vertices (hard arrises); caps get one clean stone patch like rbox. Used where a stone must follow
    the arch: wedge voussoirs and spandrel stones cut to the extrados, so only the mortar joint shows."""
    tone = random.random() if tone is None else tone
    xs, zs_ = [p[0] for p in poly], [p[1] for p in poly]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs_), max(zs_); w, h = max(x1 - x0, 0.05), max(z1 - z0, 0.05)
    def patch():
        r = pick_rect(w, h); ix, iy = (r[2] - r[0]) * 0.08, (r[3] - r[1]) * 0.10
        return r[0] + ix, r[1] + iy, r[2] - ix, r[3] - iy
    for y, rev in ((y1, False), (y0, True)):                    # caps (+Y face, -Y face)
        u0, v0, u1, v1 = patch(); st = len(B.v)
        pts = poly[::-1] if rev else poly
        for x, z in pts:
            B.v.append(Vector((x, y, z))); B.col.append((tone, damp, 1.0, 1.0))
            B.uv.append((u0 + (x - x0) / w * (u1 - u0), 1 - (v0 + (z - z0) / h * (v1 - v0))))
        B.f.append(tuple(range(st, st + len(pts)))); B.mat.append(mat)
    n = len(poly)
    for i in range(n):                                          # sides
        (xa, za), (xb, zb) = poly[i], poly[(i + 1) % n]
        u0, v0, u1, v1 = patch(); L = math.hypot(xb - xa, zb - za); st = len(B.v)
        for (x, z, y, s, t) in ((xa, za, y0, 0, 0), (xb, zb, y0, 1, 0), (xb, zb, y1, 1, 1), (xa, za, y1, 0, 1)):
            B.v.append(Vector((x, y, z))); B.col.append((tone, damp, 0.6, 1.0))
            B.uv.append((u0 + s * min(1.0, L / 3.2 / max(u1 - u0, 1e-3)) * (u1 - u0), 1 - (v0 + t * (v1 - v0) * 0.3)))
        B.f.append((st, st + 1, st + 2, st + 3)); B.mat.append(mat)

def arc_pts(xc, zc, r, t0, t1, n):
    return [(xc + r * math.cos(t0 + (t1 - t0) * k / n), zc + r * math.sin(t0 + (t1 - t0) * k / n)) for k in range(n + 1)]

def arcade(sd):
    random.seed(sd['seed']); B = Buf()
    yc, hy = (sd['y0'] + sd['y1']) / 2, (sd['y1'] - sd['y0']) / 2
    ya, yb = yc - hy + J2, yc + hy - J2
    S = PIERS[1] - PIERS[0]; r = (S - PW) / 2; ri, ro = r, r + VS; roj = ro + JOINT
    zs = Z_TOP - TOPC - CROWN - ro                     # springing (top of the impost)
    xcs = [(PIERS[i] + PIERS[i + 1]) / 2 for i in range(NB)]     # bay centres
    zt = zs + ro * math.sin(THS)                       # springer top = first spandrel bed
    # --- piers: bonded courses (one whole block / two half blocks across the thickness, alternating), impost on top
    for px in PIERS:
        z, k = 0.0, 0
        while z < zs - 0.22 - 0.30:
            ch = random.uniform(0.38, 0.50)
            if z + ch > zs - 0.22 - 0.25: ch = zs - 0.22 - z
            dmp = max(0.0, 1.0 - z / 1.2) * 0.6
            if k % 2 == 0:
                rbox(B, Vector((px, yc, z + ch / 2)), Vector((PW / 2 - J2, hy - J2, ch / 2 - J2)), rb=random.uniform(0.012, 0.022), damp=dmp)
            else:
                for sg in (-1, 1):
                    rbox(B, Vector((px, yc + sg * hy / 2, z + ch / 2)), Vector((PW / 2 - J2, hy / 2 - J2, ch / 2 - J2)), rb=random.uniform(0.012, 0.022), damp=dmp)
            z += ch; k += 1
        rbox(B, Vector((px, yc, (z + zs) / 2)), Vector((PW / 2 + 0.05, hy + 0.04, (zs - z) / 2 - J2)), rb=0.02, rock=1.2)     # impost
        # mortar core: fills every bed / head joint of the pier 1.5 cm behind the faces (no light through the joints)
        prism(B, [(px - PW / 2 + 0.015, 0.0), (px + PW / 2 - 0.015, 0.0), (px + PW / 2 - 0.015, zs), (px - PW / 2 + 0.015, zs)],
              yc - hy + 0.015, yc + hy - 0.015, mat=1, tone=0.5)
    # --- springers (tas-de-charge): one stone per pier, cut to both arches, horizontal bed on the impost, radial top joints
    def intr(xc, t, rad=ri): return (xc + rad * math.cos(t), zs + rad * math.sin(t))
    for k, px in enumerate(PIERS):
        poly = []
        if k > 0:      # left arch (bay k-1): its right half, angles 0 .. THS
            xc = xcs[k - 1]
            poly += [intr(xc, 0.0 + J2 / ri)] if False else []
            left = [(xc + ri * math.cos(t), zs + ri * math.sin(t)) for t in (THS * q / 4 for q in range(5))][::-1]
            # walk: top-left (extrados at THS) -> radial down to intrados at THS -> down the intrados to the springing
            poly_l = [(xc + roj * math.cos(THS), zs + roj * math.sin(THS))] + left
        else:
            poly_l = [(px - PW / 2 + J2, zt + 0.0), (px - PW / 2 + J2, zs)]
        if k < NB:     # right arch (bay k): its left half, angles pi .. pi - THS
            xc = xcs[k]
            right = [(xc + ri * math.cos(math.pi - THS * q / 4), zs + ri * math.sin(math.pi - THS * q / 4)) for q in range(5)]
            poly_r = right + [(xc + roj * math.cos(math.pi - THS), zs + roj * math.sin(math.pi - THS))]
        else:
            poly_r = [(px + PW / 2 - J2, zs), (px + PW / 2 - J2, zt)]
        # outline: left part goes top->bottom, then bottom->top on the right; close along the top bed
        poly = poly_l + poly_r
        prism(B, [(x, max(z, zs + J2)) for x, z in poly], ya, yb)
    # --- voussoirs: true wedges from THS to pi-THS, odd count -> keystone
    n = max(7, int(round((math.pi - 2 * THS) * (ri + VS / 2) / 0.26)) | 1)
    for xc in xcs:
        for i in range(n):
            t0 = THS + (math.pi - 2 * THS) * i / n; t1 = THS + (math.pi - 2 * THS) * (i + 1) / n
            di, do = J2 / ri, J2 / ro
            prism(B, arc_pts(xc, zs, ri, t0 + di, t1 - di, 3) + arc_pts(xc, zs, ro, t1 - do, t0 + do, 3), ya, yb)
    # --- spandrel courses per pier column, from the springer bed to the top course, cut to the extrados on both sides
    def ext_r(xc, z):  # right half extrados of a bay (x of the curve), or the bay centre above the crown
        d = z - zs
        return xc + math.sqrt(roj * roj - d * d) if d < roj else xc
    def ext_l(xc, z):
        d = z - zs
        return xc - math.sqrt(roj * roj - d * d) if d < roj else xc
    z = zt
    zc = Z_TOP - TOPC
    while z < zc - 0.05:
        ch = min(random.uniform(0.20, 0.27), zc - z)
        if zc - (z + ch) < 0.12: ch = zc - z
        za, zb = z + J2, z + ch - J2
        zz = [za + (zb - za) * q / 6 for q in range(7)]
        for k, px in enumerate(PIERS):
            L = [((ext_r(xcs[k - 1], q) + J2) if k > 0 else px - PW / 2 + J2, q) for q in zz]
            R = [((ext_l(xcs[k], q) - J2) if k < NB else px + PW / 2 - J2, q) for q in zz]
            lmax, rmin = max(p[0] for p in L), min(p[0] for p in R)
            if rmin - lmax < 0.03: continue
            cuts, x = [], lmax + random.uniform(0.25, 0.45)
            while rmin - x > 0.30:
                cuts.append(x); x += random.uniform(0.35, 0.70)
            edges = [L] + [[(c, za), (c, zb)] for c in cuts] + [R]
            for e0, e1 in zip(edges[:-1], edges[1:]):
                left = [(p[0] + (J2 if e0 is not L else 0.0), p[1]) for p in e0]
                right = [(p[0] - (J2 if e1 is not R else 0.0), p[1]) for p in e1]
                poly = left[::-1] + right            # top-left -> bottom-left -> bottom-right -> top-right
                prism(B, poly, ya, yb)
        z += ch
    # --- mortar core behind every joint (1.5 cm in from both faces = pointed nearly flush): arcade outline minus the openings
    for xc in xcs:
        a, b = xc - S / 2, xc + S / 2
        left = [(a, zs)] + arc_pts(xc, zs, ri + 0.015, math.pi, math.pi / 2, 12) + [(xc, Z_TOP - 0.01), (a, Z_TOP - 0.01)]
        right = [(xc, Z_TOP - 0.01)] + arc_pts(xc, zs, ri + 0.015, math.pi / 2, 0.0, 12) + [(b, zs), (b, Z_TOP - 0.01)]
        for poly in (left, right): prism(B, poly, yc - hy + 0.015, yc + hy - 0.015, mat=1, tone=0.5)
    # --- top course: long stones under the deck the full arcade length (the deck beams sit on it)
    x = PIERS[0] - PW / 2
    while PIERS[-1] + PW / 2 - x > 0.1:
        Lr = min(random.uniform(0.7, 1.2), PIERS[-1] + PW / 2 - x)
        rbox(B, Vector((x + Lr / 2, yc, Z_TOP - TOPC / 2)), Vector((Lr / 2 - J2, hy + 0.02, TOPC / 2 - J2)), rb=0.02, rock=1.2)
        x += Lr
    return B, zs

if __name__ == '__main__':
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    mats = [bpy.data.materials.new('M_Tun_Ashlar'), bpy.data.materials.new('M_Tun_Mortar')]
    info = {}
    for key, sd in SIDES.items():
        B, zs = arcade(sd)
        me = bpy.data.meshes.new('SM_Arcade_' + key)
        me.from_pydata([(p.x, -p.y, p.z) for p in B.v], [], B.f)
        for m in mats: me.materials.append(m)
        me.polygons.foreach_set('material_index', B.mat)
        lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
        me.uv_layers.new(name='UV0').data.foreach_set('uv', np.asarray(B.uv, dtype=np.float32)[lv].ravel())
        me.attributes.new('Col', 'FLOAT_COLOR', 'CORNER').data.foreach_set('color', np.clip(np.asarray(B.col, dtype=np.float32), 0, 1)[lv].ravel())
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)          # every stone is a closed shell -> outward normals
        bm.to_mesh(me); bm.free()
        me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(35))   # rbox rounding stays soft, cut-stone arrises hard
        ob = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(ob)
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.fbx(filepath='%s/%s.fbx' % (OUT, me.name), use_selection=True, mesh_smooth_type='OFF', add_leaf_bones=False,
                                 bake_anim=False, axis_forward='-Z', axis_up='Y', apply_scale_options='FBX_SCALE_NONE', colors_type='LINEAR')
        info[key] = dict(verts=len(me.vertices), z_spring=round(zs, 3))
        print('ARCADE', key, info[key])
    json.dump(info, open(OUT + '/info.json', 'w'))
