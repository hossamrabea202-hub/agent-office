# Shared helpers for the #400 cavalry kit (stables, destrier, tack, knight props). checkking (Claude), 2026-11-01.
# Original procedural work, no third-party assets. Runs inside Blender 4.5 (bpy + numpy).
#   - periodic (seamless) value noise / fbm for tiling textures
#   - sRGB <-> linear, PNG save, normal map from height (DirectX + GL)
#   - calibrated lookdev: Nishita sky, sun 35 deg, 0.18 grey ball + chrome ball, exposure metered on the grey ball to
#     118 sRGB (linear Standard), then rendered with AgX at that LOCKED exposure (knowledge base rule 2)
import bpy, numpy as np, math, os
from mathutils import Vector

# ---------------------------------------------------------------- colour
def lin(*srgb): return np.array([((c / 255 + 0.055) / 1.055) ** 2.4 for c in srgb], np.float32)
def to_srgb(l):
    l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def mix(a, b, t):
    t = np.asarray(t, np.float32)
    return a + (b - a) * (t[..., None] if t.ndim == a.ndim - 1 else t)

# ---------------------------------------------------------------- periodic 2D noise (tiles over the texture)
def _hash(ix, iy, seed):
    n = (ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791)
    n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16); return (n & 0xFFFF).astype(np.float32) / 65535.0
def pnoise(u, v, period_u, period_v=None, seed=0):
    """value noise on a lattice of period_u x period_v cells over u, v in [0, 1): seamless at the texture edge."""
    period_v = period_v or period_u
    x = u * period_u; y = v * period_v; ix = np.floor(x).astype(np.int64); iy = np.floor(y).astype(np.int64)
    fx = x - ix; fy = y - iy; fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    x0 = ix % period_u; x1 = (ix + 1) % period_u; y0 = iy % period_v; y1 = (iy + 1) % period_v
    a = _hash(x0, y0, seed); b = _hash(x1, y0, seed); c = _hash(x0, y1, seed); d = _hash(x1, y1, seed)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy
def pfbm(u, v, pu, pv=None, oct=4, seed=0, gain=0.5):
    pv = pv or pu; s = 0.0; a = 1.0; tot = 0.0
    for k in range(oct):
        s = s + a * pnoise(u, v, pu * 2 ** k, pv * 2 ** k, seed + 31 * k); tot += a; a *= gain
    return s / tot
def grid(res):
    v, u = np.meshgrid((np.arange(res) + 0.5) / res, (np.arange(res) + 0.5) / res, indexing='ij'); return u.astype(np.float32), v.astype(np.float32)
def cells(u, v, nu, nv, seed=0, jitter=0.8):
    """periodic Worley: distance to nearest and second-nearest feature point + id of the nearest cell."""
    x = u * nu; y = v * nv; ix = np.floor(x).astype(np.int64); iy = np.floor(y).astype(np.int64)
    d1 = np.full(u.shape, 9.0, np.float32); d2 = np.full(u.shape, 9.0, np.float32); cid = np.zeros(u.shape, np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx = ix + dx; cy = iy + dy; wx = cx % nu; wy = cy % nv
            px = cx + 0.5 + jitter * (_hash(wx, wy, seed) - 0.5); py = cy + 0.5 + jitter * (_hash(wx, wy, seed + 7) - 0.5)
            d = np.sqrt((x - px) ** 2 + (y - py) ** 2); idc = _hash(wx, wy, seed + 13)
            closer = d < d1; d2 = np.where(closer, d1, np.minimum(d2, d)); cid = np.where(closer, idc, cid); d1 = np.where(closer, d, d1)
    return d1, d2, cid

# ---------------------------------------------------------------- images
def save_png(path, rgb, srgb_encoded=True):
    """rgb: (H, W, 3) float 0..1, already in the target encoding. Rows go bottom-up in Blender, so flip."""
    H, W = rgb.shape[:2]; im = bpy.data.images.new(os.path.basename(path), W, H, alpha=False)
    im.colorspace_settings.name = 'Non-Color'
    a = np.ones((H, W, 4), np.float32); a[..., :3] = np.clip(rgb, 0, 1)[::-1]
    im.pixels.foreach_set(a.ravel()); im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    print('SAVED', path, flush=True)
def normal_from_height(h, px_per_m, strength=1.0):
    """h in metres (H, W), periodic. Returns (DirectX, OpenGL) normal maps 0..1."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * px_per_m * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * px_per_m * strength
    n = np.stack([-gx, gy, np.ones_like(gx)], -1)          # image rows go down; +Y (GL) is up the image
    n /= np.linalg.norm(n, axis=-1, keepdims=True); gl = n * 0.5 + 0.5; dx = gl.copy(); dx[..., 1] = 1 - dx[..., 1]
    return dx, gl
def write_set(outdir, name, base_lin, rough, ao, height, px_per_m, metal=None, nstrength=1.0):
    os.makedirs(outdir, exist_ok=True)
    sd = float(np.std(rough))
    if sd < 0.06:                                                # KB: roughness is never flat. Stretch the (physical) variation
        m = float(np.mean(rough)); rough = m + (rough - m) * (0.06 / max(sd, 1e-4))
    save_png(os.path.join(outdir, name + '_BC.png'), to_srgb(base_lin))
    orm = np.stack([ao, np.clip(rough, 0.05, 0.98), metal if metal is not None else np.zeros_like(ao)], -1)
    save_png(os.path.join(outdir, name + '_ORM.png'), orm)
    dx, gl = normal_from_height(height, px_per_m, nstrength)
    save_png(os.path.join(outdir, name + '_N.png'), dx); save_png(os.path.join(outdir, name + '_N_GL.png'), gl)

# ---------------------------------------------------------------- lookdev
def lookdev(out, cam_loc, target, lens=35, sun_rot=215, sun_el=35, res=(1600, 1000), samples=64, ball_at=None,
            ground=True, meter=True, exposure=None):
    sc = bpy.context.scene
    if ground:
        bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.002)); g = bpy.context.active_object
        gm = bpy.data.materials.new('LD_Ground'); gm.use_nodes = True; gb = gm.node_tree.nodes['Principled BSDF']
        gb.inputs['Base Color'].default_value = (0.08, 0.065, 0.05, 1); gb.inputs['Roughness'].default_value = 0.92; g.data.materials.append(gm)
    w = bpy.data.worlds.new('LD_World'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
    sky = w.node_tree.nodes.new('ShaderNodeTexSky')
    if 'NISHITA' in [e.identifier for e in sky.bl_rna.properties['sky_type'].enum_items]: sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(sun_el); sky.sun_rotation = math.radians(sun_rot); w.node_tree.links.new(sky.outputs[0], bg.inputs['Color'])
    cd = bpy.data.cameras.new('LD_Cam'); cam = bpy.data.objects.new('LD_Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = Vector(cam_loc); cd.lens = lens; cd.clip_end = 500
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    balls = []
    if ball_at is not None:
        for k, (col, met, rgh) in enumerate([((0.18, 0.18, 0.18, 1), 0.0, 0.5), ((0.95, 0.95, 0.95, 1), 1.0, 0.02)]):
            r = 0.16; loc = Vector(ball_at) + Vector((k * 0.42, 0, r))
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24, location=loc); bpy.ops.object.shade_smooth()
            m = bpy.data.materials.new('LD_Ball%d' % k); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
            p.inputs['Base Color'].default_value = col; p.inputs['Metallic'].default_value = met; p.inputs['Roughness'].default_value = rgh
            bpy.context.active_object.data.materials.append(m); balls.append(bpy.context.active_object)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100; sc.render.image_settings.file_format = 'PNG'
    import bpy_extras
    if exposure is not None: sc.view_settings.exposure = exposure
    elif meter and balls:
        uvp = bpy_extras.object_utils.world_to_camera_view(sc, cam, balls[0].location)
        tmp = out + '_meter.png'; sc.render.filepath = tmp; sc.cycles.samples = 16
        sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -5.9
        for it in range(5):
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'; W, H = im.size
            px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im); px = px.reshape(H, W, 4)
            cx, cy = uvp.x * W, uvp.y * H
            top = bpy_extras.object_utils.world_to_camera_view(sc, cam, balls[0].location + Vector((0, 0, 0.16)))
            rp = max(3.0, abs(top.y * H - cy)); yy, xx = np.mgrid[0:H, 0:W]
            disc = (xx - cx) ** 2 + (yy - cy) ** 2 < (0.8 * rp) ** 2
            # the lit side of the ball (75th percentile of the disc), so a back-lit ball doesn't blow the exposure
            if disc.sum() < 5: print('METER: ball not in view, keeping exposure', flush=True); break
            v = float(np.percentile(px[disc][:, :3].mean(1), 75)) * 255
            print('METER grey ball (lit side) %.0f sRGB at exposure %.2f' % (v, sc.view_settings.exposure), flush=True)
            if abs(v - 118) < 4: break
            L = lambda s: ((s / 255 + 0.055) / 1.055) ** 2.4
            sc.view_settings.exposure += math.log2(L(118) / max(L(min(v, 254)), 1e-4)) * (1.0 if v < 250 else 1.6)
        try: os.remove(tmp)
        except OSError: pass
    else: sc.view_settings.exposure = -5.9
    sc.view_settings.view_transform = 'AgX'; sc.cycles.samples = samples
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)
    print('LOOKDEV OK', out, 'exposure %.2f' % sc.view_settings.exposure, flush=True)
    return sc.view_settings.exposure
