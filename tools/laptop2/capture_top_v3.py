# #29 export v3 (laptop2, 2026-10-29): a clean top-down picture of the play area, so the owner's marked fog zones can be
# traced in world coordinates. v2's capture was covered by the far mountain meshes and the fog/sky cubes; v3 hides
# every actor wider than 150 m (mountains, sky, fog volumes) and the fog/cloud/particle show flags, and writes two tiles:
#   top_full.png   the whole play box (NavMesh bounds + 60 m), 4096 px wide
#   top_castle.png 400 m x 400 m around the castle, 4096 px (~10 cm per pixel)
# Axes are written into meta3.json: image right = +Y, image up = +X (camera yaw 0, pitch -90), plus a test marker:
# a 10 m red cube is spawned at the castle centre for the shot and removed after, so the orientation can't be misread.
# Read-only for the level: everything spawned is destroyed, nothing is saved.
# Run in the editor with the game level open:   py "<repo>/tools/laptop2/capture_top_v3.py"
import json, os
import unreal

REPO = r''
try:
    ROOT = REPO or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except NameError:
    ROOT = REPO
if not ROOT:
    raise RuntimeError('set REPO at the top of this script to your office-repo checkout')
OUT = os.path.join(ROOT, 'handoffs', 'exports', 'laptop2', 'bounds29', 'v3')
os.makedirs(OUT, exist_ok=True)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()

lo = [1e9, 1e9]; hi = [-1e9, -1e9]
for a in actors:
    if a.get_class().get_name() == 'NavMeshBoundsVolume':
        o, e = a.get_actor_bounds(False)
        lo = [min(lo[0], o.x - e.x), min(lo[1], o.y - e.y)]; hi = [max(hi[0], o.x + e.x), max(hi[1], o.y + e.y)]
lo = [lo[0] - 6000, lo[1] - 6000]; hi = [hi[0] + 6000, hi[1] + 6000]
hide = []
for a in actors:
    try:
        o, e = a.get_actor_bounds(False)
    except Exception:
        continue
    n = a.get_actor_label(); c = a.get_class().get_name()
    if max(e.x, e.y) > 15000 and 'Landscape' not in c and n != 'MB_Forest':
        hide.append(a)
    elif 'Fog' in n or 'Fog' in c or 'Sky' in c or 'Cloud' in c:
        hide.append(a)
castle = [1500.0, 1750.0]
marker = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(castle[0] + 3000, castle[1], 3000), unreal.Rotator(0, 0, 0))
marker.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
marker.set_actor_scale3d(unreal.Vector(10, 2, 2))      # a 10 m bar pointing +X from beside the castle: "this way is +X"
try:
    m = unreal.load_asset('/Engine/BasicShapes/BasicShapeMaterial')
    marker.static_mesh_component.set_material(0, m)
except Exception:
    pass

def shot(name, cx, cy, width, px=4096, aspect=1.0):
    rt = unreal.RenderingLibrary.create_render_target2d(world, px, int(px * aspect), unreal.TextureRenderTargetFormat.RTF_RGBA8)
    cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(cx, cy, 60000), unreal.Rotator(-90, 0, 0))
    try:
        c = cap.capture_component2d
        c.set_editor_property('projection_type', unreal.CameraProjectionMode.ORTHOGRAPHIC)
        c.set_editor_property('ortho_width', width)
        c.set_editor_property('texture_target', rt)
        c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        c.set_editor_property('hidden_actors', hide)
        flags = []
        for f in ('Fog', 'VolumetricFog', 'AtmosphericFog', 'Atmosphere', 'Cloud', 'Particles', 'Translucency'):
            s = unreal.EngineShowFlagsSetting(); s.set_editor_property('show_flag_name', f); s.set_editor_property('enabled', False); flags.append(s)
        c.set_editor_property('show_flag_settings', flags)
        c.capture_scene()
        unreal.RenderingLibrary.export_render_target(world, rt, OUT, name)
    finally:
        eas.destroy_actor(cap)
try:
    W = hi[0] - lo[0]; Hh = hi[1] - lo[1]
    # camera yaw 0 / pitch -90: the image's up is +X and its right is +Y, so the box's Y size is the image width
    shot('top_full', (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, Hh, 4096, W / Hh)
    shot('top_castle', castle[0] - 10000, castle[1] - 10000, 40000, 4096, 1.0)
finally:
    eas.destroy_actor(marker)
json.dump({'full': {'center': [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2], 'width_y': hi[1] - lo[1], 'height_x': hi[0] - lo[0]},
           'castle_tile': {'center': [castle[0] - 10000, castle[1] - 10000], 'width': 40000},
           'axes': 'expected: image up = +X, image right = +Y; verify with the 10 m bar 30 m on the +X side of the castle (it lies along +X)',
           'hidden': [a.get_actor_label() for a in hide], 'files': sorted(os.listdir(OUT))},
          open(os.path.join(OUT, 'meta3.json'), 'w'), indent=1)
unreal.log('#29 export v3 written to ' + OUT + ' (hidden %d big/fog actors)' % len(hide))
