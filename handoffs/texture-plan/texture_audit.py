# #262 texture plan, step 1 (TGA, 2026-10-31): audit every agent texture in assets/* against the owner's budget.
#   blender -b --factory-startup -P texture_audit.py            -> AUDIT.md + audit.json (step 2 reads audit.json)
# Per texture: size, role (BC / ORM / N / E / mask), disk MB, estimated GPU MB (BC1 0.5 B/px colour + masks, BC5 1 B/px normals,
# BC3/BC7 1 B/px with alpha, x4/3 mips) now and at the budget. Per mesh: median texel density (UV length / 3D length x the
# kit's largest BaseColor size) now and at the budget, flagged outside 512-1024 px/m (props) / 1024-2048 (hero, enemies).
import bpy, os, sys, json, struct, re, numpy as np
from mathutils import Vector
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
ASSETS = os.path.join(REPO, 'assets')
OUT = os.path.dirname(os.path.abspath(__file__))
# budget per kit (owner table on #262; 'keep' = UI / FX / motion graphics, unchanged). Large structures (> ~5 m) are
# listed separately at 2K: at 1K a 10 m siege tower would drop to ~50 px/m (flagged for the owner in AUDIT.md).
BUDGET = {
    'checkking/Obsidian-Sovereign': (2048, 'hero armour'), 'Codex/Obsidian-Sovereign': (2048, 'hero armour'),
    'laptop2/Obsidian-Sovereign': (2048, 'hero armour'), 'checkking/TornCape': (2048, 'hero armour'),
    'tga/HalfHorseZombie': (2048, 'enemy'), 'tga/RealmWasp': (2048, 'enemy'), 'tga/ZombieV2': (2048, 'enemy'), 'tga/FleshBrute': (2048, 'enemy'),
    'tga/Rocks': (2048, 'rocks'),
    'tga/SiegeEngines': (2048, 'large structure'), 'laptop2/SiegeGate': (2048, 'large structure'), 'laptop2/SiegeBarricadeKit': (2048, 'large structure'),
    'tga/OreShed': (2048, 'large structure'), 'laptop2/GroundKit': (2048, 'tiling ground (2 m tiles)'), 'tga/FarmCrops': (2048, 'tiling soil + crop trim'),
    'checkking/Weapons': (1024, 'weapons'), 'laptop2/WeaponPack': (1024, 'weapons'), 'laptop2/FireBallista': (1024, 'weapons'),
    'tga/MinerGear': (1024, 'NPC gear'), 'tga/MedicGear': (1024, 'NPC gear'),
    'laptop2/CampKit': (1024, 'props'), 'laptop2/MineKit': (1024, 'props'), 'laptop2/BarracksProps': (1024, 'props'), 'laptop2/FloraKit': (1024, 'props'),
    'laptop2/RealmKit': (1024, 'props'), 'tga/Feast': (1024, 'props'), 'tga/Fence': (1024, 'props'), 'tga/RealmCrack': (1024, 'props'),
    'tga/RealmDressing': (1024, 'props'), 'tga/SiegeDebris': (1024, 'props'), 'tga/Signs': (1024, 'props'), 'tga/Trough': (1024, 'props'),
    'laptop2/DecalKit': (1024, 'decals'),
    'checkking/RevealMG': (0, 'UI / motion graphics (keep)'), 'laptop2/ShieldFX': (0, 'FX (keep)'), 'laptop2/SwordFire': (0, 'FX (keep)'),
    'laptop2/AtmosKit': (0, 'FX (keep)'),
}
TINY = re.compile(r'(Tankard|Bandage|Armband|Candle|Coin|Apple)', re.I)


def png_size(p):
    with open(p, 'rb') as f: h = f.read(32)
    if h[:8] == b'\x89PNG\r\n\x1a\n': return struct.unpack('>II', h[16:24]) + (h[25],)     # w, h, colour type
    if p.lower().endswith('.tga'): return struct.unpack('<HH', h[12:16]) + (2 if h[16] == 24 else 6,)
    if p.lower().endswith(('.jpg', '.jpeg')):
        with open(p, 'rb') as f: d = f.read()
        i = 2
        while i < len(d):
            if d[i] != 0xFF: i += 1; continue
            m = d[i + 1]
            if m in (0xC0, 0xC2): hgt, wid = struct.unpack('>HH', d[i + 5:i + 9]); return wid, hgt, 2
            i += 2 + struct.unpack('>H', d[i + 2:i + 4])[0]
    return 0, 0, 2


def role(n):
    s = os.path.splitext(n)[0].upper()
    for k, r in (('_N_GL', 'normal-GL'), ('_NORMAL', 'normal'), ('_N', 'normal'), ('_ORM', 'orm'), ('_E', 'emissive'), ('_BCA', 'colour+alpha'), ('_BC', 'colour'),
                 ('_D', 'colour'), ('_ALBEDO', 'colour'), ('_BASECOLOR', 'colour'), ('_MASK', 'mask'), ('_M', 'mask'), ('_R', 'mask'), ('_H', 'mask'), ('_AO', 'mask')):
        if s.endswith(k) or (k + '_') in s: return r
    return 'other'


def gpu_mb(w, h, r, ctype):
    bpp = 1.0 if (r.startswith('normal') or ctype in (4, 6) or r == 'colour+alpha') else 0.5
    return w * h * bpp * 4 / 3 / 1048576


rows, kits = [], {}
for owner in sorted(os.listdir(ASSETS)):
    od = os.path.join(ASSETS, owner)
    if not os.path.isdir(od): continue
    for kit in sorted(os.listdir(od)):
        kd = os.path.join(od, kit); key = owner + '/' + kit
        if not os.path.isdir(kd) or key not in BUDGET: continue
        cap, cat = BUDGET[key]; k = kits.setdefault(key, dict(cap=cap, cat=cat, tex=[], fbx=[]))
        for root, _, files in os.walk(kd):
            if os.sep + 'screens' in root: continue
            for fn in files:
                p = os.path.join(root, fn); rel = os.path.relpath(p, REPO).replace('\\', '/')
                if fn.lower().endswith(('.png', '.tga', '.jpg', '.jpeg')):
                    w, h, ct = png_size(p); r = role(fn); c = cap if not TINY.search(fn) or cap == 0 else 512
                    tw = w if c == 0 or max(w, h) <= c else c; th = h if tw == w else int(h * c / max(w, h)); tw = tw if tw == w else int(w * c / max(w, h))
                    row = dict(kit=key, file=rel, w=w, h=h, role=r, ctype=ct, disk_mb=os.path.getsize(p) / 1048576, gpu_mb=gpu_mb(w, h, r, ct),
                               target_w=tw, target_h=th, gpu_mb_after=gpu_mb(tw, th, r, ct), over=(tw, th) != (w, h))
                    rows.append(row); k['tex'].append(row)
                elif fn.lower().endswith('.fbx'): k['fbx'].append(p)


# ---- texel density per mesh (median over polygons of UV edge / 3D edge, x the kit's biggest colour map)
def density(fbx):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
    try: bpy.ops.import_scene.fbx(filepath=fbx)
    except Exception as e: return None
    vals = []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH' or not o.data.uv_layers: continue
        me = o.data; mw = o.matrix_world
        uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        sc = np.array(mw.to_scale()); co = co * sc
        lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
        ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
        d3 = np.linalg.norm(co[lv[ls + 1]] - co[lv[ls]], axis=1); d2 = np.linalg.norm(uv[ls + 1] - uv[ls], axis=1)
        ok = d3 > 1e-4; vals.append(d2[ok] / d3[ok])
    if not vals: return None
    return float(np.median(np.concatenate(vals)))


for key, k in kits.items():
    cols = [t for t in k['tex'] if t['role'] in ('colour', 'colour+alpha')] or k['tex']
    size = max((t['w'] for t in cols), default=0); after = max((t['target_w'] for t in cols), default=0)
    k['meshes'] = []
    for f in sorted(k['fbx']):
        r = density(f)
        if r is None: continue
        k['meshes'].append(dict(fbx=os.path.relpath(f, REPO).replace('\\', '/'), pxm=r * size, pxm_after=r * after))
    print('KIT', key, len(k['tex']), 'tex', len(k['meshes']), 'meshes', flush=True)

# ---- report
tot = lambda f, rs: sum(r[f] for r in rs)
json.dump(dict(rows=rows, kits={k: dict(cap=v['cap'], cat=v['cat'], meshes=v['meshes']) for k, v in kits.items()}), open(os.path.join(OUT, 'audit.json'), 'w'), indent=1)
L = ['# #262 texture audit (TGA, 2026-10-31)', '',
     'Generated by `texture_audit.py` (Blender, headless) over every texture and FBX in `assets/*`. Screens and licensed files',
     '(not in the repo) are skipped. **GPU MB** = estimated video memory with Unreal compression (BC1/DXT1 0.5 B/px for colour,',
     'ORM, emissive and masks; BC5 or BC3/BC7 1 B/px for normals and anything with alpha) plus mips (x4/3).',
     '`_N_GL` maps are lookdev-only (OpenGL normals for Blender) and never get imported, so they count on disk, not on the GPU.', '',
     '## Totals', '',
     '| | Now | At budget | Saved |', '|---|---|---|---|']
gpu_rows = [r for r in rows if r['role'] != 'normal-GL']
L.append('| Disk (repo PNG/TGA) | %.0f MB | ~%.0f MB (est.) | ~%.0f MB |' % (tot('disk_mb', rows), sum(r['disk_mb'] * (r['target_w'] * r['target_h']) / max(r['w'] * r['h'], 1) for r in rows),
         tot('disk_mb', rows) - sum(r['disk_mb'] * (r['target_w'] * r['target_h']) / max(r['w'] * r['h'], 1) for r in rows)))
L.append('| GPU (imported, compressed) | %.0f MB | %.0f MB | %.0f MB |' % (tot('gpu_mb', gpu_rows), tot('gpu_mb_after', gpu_rows), tot('gpu_mb', gpu_rows) - tot('gpu_mb_after', gpu_rows)))
L += ['', '## Per kit', '', '| Kit | Category | Budget | Textures | Over budget | Largest | Disk MB | GPU MB now -> after | Texel density px/m now -> after (median of meshes) |',
      '|---|---|---|---|---|---|---|---|---|']
flags = []
for key in sorted(kits):
    k = kits[key]; t = k['tex']
    if not t: continue
    big = max(t, key=lambda r: r['w'] * r['h']); over = sum(r['over'] for r in t)
    ms = k['meshes']; dn = np.median([m['pxm'] for m in ms]) if ms else 0; da = np.median([m['pxm_after'] for m in ms]) if ms else 0
    lo, hi = (1024, 2048) if k['cap'] == 2048 else (512, 1024)
    L.append('| %s | %s | %s | %d | %d | %dx%d | %.1f | %.1f -> %.1f | %s |' % (key, k['cat'], ('%dK' % (k['cap'] // 1024)) if k['cap'] else 'keep', len(t), over,
             big['w'], big['h'], tot('disk_mb', t), tot('gpu_mb', [r for r in t if r['role'] != 'normal-GL']), tot('gpu_mb_after', [r for r in t if r['role'] != 'normal-GL']),
             ('%.0f -> %.0f' % (dn, da)) if ms else '-'))
    for m in ms:
        if k['cap'] and (m['pxm_after'] < lo * 0.5 or m['pxm_after'] > hi * 2):
            flags.append('| %s | %s | %.0f | %.0f | %s |' % (key, os.path.basename(m['fbx']), m['pxm'], m['pxm_after'], 'too low: blurry up close' if m['pxm_after'] < lo * 0.5 else 'too high: wasted texels'))
L += ['', '## Texel density flags (after the budget, outside half / double the %d-%d px/m target band)' % (512, 1024), '',
      '| Kit | Mesh | px/m now | px/m after | Note |', '|---|---|---|---|---|'] + (flags or ['| - | none | | | |'])
L += ['', '## Every texture', '', '| File | Role | Size | Target | Disk MB | GPU MB now -> after |', '|---|---|---|---|---|---|']
for r in sorted(rows, key=lambda r: -r['gpu_mb']):
    L.append('| `%s` | %s | %dx%d | %s | %.1f | %.1f -> %.1f |' % (r['file'], r['role'], r['w'], r['h'], ('%dx%d' % (r['target_w'], r['target_h'])) if r['over'] else '=', r['disk_mb'], r['gpu_mb'], r['gpu_mb_after']))
open(os.path.join(OUT, 'AUDIT.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('AUDIT OK', len(rows), 'textures', flush=True)
