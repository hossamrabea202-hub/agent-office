# #296 / #297 (adjustedfilm, 2026-10-31): READ-ONLY dump of the cave, for texturing (#296) and the dungeon door (#297).
# Run in the editor with ThirdPersonMap open:  py "<repo>/handoffs/cave-296-297/dump_cave_ue.py"
# Changes nothing. Writes <repo>/handoffs/exports/adjustedfilm/cave-296-297/cave_dump.json, then commit + push that file.
# Finds every level actor whose label, class, mesh or material path contains "cave" (or a word in EXTRA below),
# and lists the streaming sub-levels and the player start.
import os, json
import unreal

EXTRA = ['cave', 'cavern', 'grotto', 'mine', 'tunnel']
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'exports', 'adjustedfilm', 'cave-296-297', 'cave_dump.json'))
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

def v(x): return [round(x.x, 1), round(x.y, 1), round(x.z, 1)]
def r(x): return [round(x.pitch, 2), round(x.yaw, 2), round(x.roll, 2)]
def hit(*texts): return any(w in (t or '').lower() for t in texts for w in EXTRA)

rows = []
for a in EAS.get_all_level_actors():
    comps = []
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.get_editor_property('static_mesh')
        mats = [m.get_path_name() if m else None for m in c.get_materials()]
        comps.append({'comp': c.get_name(), 'mesh': sm.get_path_name() if sm else None, 'materials': mats,
                      'world_scale': v(c.get_world_scale())})
    if not hit(a.get_actor_label(), a.get_class().get_name(), *[c['mesh'] for c in comps], *[m for c in comps for m in c['materials']]):
        continue
    o, e = a.get_actor_bounds(False)
    rows.append({'label': a.get_actor_label(), 'class': a.get_class().get_path_name(), 'folder': str(a.get_folder_path()),
                 'loc': v(a.get_actor_location()), 'rot': r(a.get_actor_rotation()), 'scale': v(a.get_actor_scale3d()),
                 'bounds_center': v(o), 'bounds_extent': v(e), 'mesh_comps': comps[:8]})

starts = [{'label': a.get_actor_label(), 'loc': v(a.get_actor_location())} for a in EAS.get_all_level_actors() if isinstance(a, unreal.PlayerStart)]
try:
    levels = [l.get_path_name() for l in unreal.EditorLevelUtils.get_levels(world)]
except Exception as ex:
    levels = ['(could not list: %s)' % ex]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({'map': world.get_path_name(), 'actors': rows, 'player_starts': starts, 'levels': levels}, open(OUT, 'w'), indent=1)
print('[cave dump] %d actors -> %s' % (len(rows), OUT))
