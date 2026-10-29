# #29 player boundaries, export v2 (laptop2, 2026-10-29). v1 was 5.25 m cells over the whole 1 km map, and its traces
# hit tree canopies. v2 covers only the playable area (the NavMesh bounds + 60 m) at 2.5 m, and separates:
#   ground  = the landscape only (every other actor is ignored by that trace)
#   top     = the first thing hit from above (trees, rocks, walls, castle), so tall cover already there is known
# and renders a fog-free top-down orthographic picture of the same box, for matching the owner's screenshot and for
# the boundary preview. Read-only for the level: the capture actor is spawned, used and destroyed; nothing is saved.
# Run in the editor with the game level open:   py "<repo>/tools/laptop2/export_level_bounds_v2.py"
# Writes handoffs/exports/laptop2/bounds29/v2/: grid2.json, top_ortho.png, meta2.json
import json, os
import unreal

REPO = r''
CELL = 250.0
PAD = 6000.0
try:
    ROOT = REPO or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except NameError:
    ROOT = REPO
if not ROOT:
    raise RuntimeError('set REPO at the top of this script to your office-repo checkout')
OUT = os.path.join(ROOT, 'handoffs', 'exports', 'laptop2', 'bounds29', 'v2')
os.makedirs(OUT, exist_ok=True)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()
land = [a for a in actors if 'Landscape' in a.get_class().get_name() and 'Gizmo' not in a.get_class().get_name()]
others = [a for a in actors if a not in land]

# box = union of the NavMesh bounds volumes + PAD
lo = [1e9, 1e9]; hi = [-1e9, -1e9]
for a in actors:
    if a.get_class().get_name() == 'NavMeshBoundsVolume':
        o, e = a.get_actor_bounds(False)
        lo = [min(lo[0], o.x - e.x), min(lo[1], o.y - e.y)]; hi = [max(hi[0], o.x + e.x), max(hi[1], o.y + e.y)]
lo = [lo[0] - PAD, lo[1] - PAD]; hi = [hi[0] + PAD, hi[1] + PAD]
NX, NY = int((hi[0] - lo[0]) / CELL), int((hi[1] - lo[1]) / CELL)
TOP, BOT = 40000.0, -30000.0

def first_hit(r):
    # UE returns the HitResult (or None); some builds return (bool, HitResult)
    hit = next((x for x in r if isinstance(x, unreal.HitResult)), None) if isinstance(r, tuple) else r
    if hit is None: return None
    t = hit.to_tuple()
    if not t[0]: return None
    act = t[9]
    return t[4].z, (act.get_actor_label() if act else '')

ground = [[None] * NX for _ in range(NY)]; top = [[None] * NX for _ in range(NY)]; topname = {}; names = []
nav = [[0] * NX for _ in range(NY)]
CH = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1
for j in range(NY):
    for i in range(NX):
        x = lo[0] + (i + 0.5) * CELL; y = lo[1] + (j + 0.5) * CELL
        a, b = unreal.Vector(x, y, TOP), unreal.Vector(x, y, BOT)
        g = first_hit(unreal.SystemLibrary.line_trace_single(world, a, b, CH, True, others, unreal.DrawDebugTrace.NONE, True))
        t = first_hit(unreal.SystemLibrary.line_trace_single(world, a, b, CH, False, [], unreal.DrawDebugTrace.NONE, True))
        if g: ground[j][i] = round(g[0])
        if t:
            top[j][i] = round(t[0])
            if t[1] not in topname: topname[t[1]] = len(names); names.append(t[1])
            top[j][i] = [round(t[0]), topname[t[1]]]
        if g:
            p = unreal.NavigationSystemV1.project_point_to_navigation(world, unreal.Vector(x, y, g[0]), None, None, unreal.Vector(40, 40, 250))
            p = p[0] if isinstance(p, tuple) else p
            nav[j][i] = 1 if p is not None and abs(p.x - x) < 60 and abs(p.y - y) < 60 else 0
json.dump({'lo': lo, 'hi': hi, 'cell': CELL, 'nx': NX, 'ny': NY, 'ground': ground, 'top': top, 'top_names': names, 'nav': nav},
          open(os.path.join(OUT, 'grid2.json'), 'w'))

# ---- fog-free orthographic top view of the same box ----
W = 4096; Hpx = int(W * (hi[1] - lo[1]) / (hi[0] - lo[0]))
rt = unreal.RenderingLibrary.create_render_target2d(world, W, Hpx, unreal.TextureRenderTargetFormat.RTF_RGBA8)
cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, TOP), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0))
try:
    c = cap.capture_component2d
    c.set_editor_property('projection_type', unreal.CameraProjectionMode.ORTHOGRAPHIC)
    c.set_editor_property('ortho_width', hi[0] - lo[0])
    c.set_editor_property('texture_target', rt)
    c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    flags = []
    for f in ('Fog', 'VolumetricFog', 'AtmosphericFog', 'Atmosphere', 'Cloud', 'Particles'):
        s = unreal.EngineShowFlagsSetting(); s.set_editor_property('show_flag_name', f); s.set_editor_property('enabled', False); flags.append(s)
    c.set_editor_property('show_flag_settings', flags)
    c.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, rt, OUT, 'top_ortho')
finally:
    eas.destroy_actor(cap)
# the exporter may write .hdr/.png/.exr depending on the format; note what came out
files = sorted(os.listdir(OUT))
json.dump({'box_min': lo, 'box_max': hi, 'cell': CELL, 'nx': NX, 'ny': NY, 'ortho_px': [W, Hpx],
           'ortho_axes': 'top-down, camera yaw 0 (image up = +X?) - check with the player start mark', 'files': files,
           'player_start': [list((a.get_actor_location().x, a.get_actor_location().y)) for a in actors if a.get_class().get_name() == 'PlayerStart']},
          open(os.path.join(OUT, 'meta2.json'), 'w'), indent=1)
unreal.log('#29 export v2: %dx%d cells at %.0f cm, ortho %dx%d -> %s  files=%s' % (NX, NY, CELL, W, Hpx, OUT, files))
