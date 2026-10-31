# Castle stones merge (checkking, 2026-10-31, owner-approved): the castle walls are thousands of single stone actors that
# share one Megascans material. This merges them per wall section (a 20 m grid cell x material) into ONE static mesh actor
# each, same geometry, same material, same transforms -> looks identical, thousands of actors become a few dozen.
#   1. File > Save Current Level As...  ThirdPersonMap_BACKUP_stones   (then reopen ThirdPersonMap)
#   2. py "<repo>/handoffs/castle-stones-merge/merge_castle_stones_ue.py"     with DRY_RUN = True: report only
#   3. set DRY_RUN = False, run again, look around in Play, then Save.
# Writes merge_castle_stones.txt next to itself. Undo = reopen the backup map.
import os, math, unreal

DRY_RUN = True
CELL = 2000.0                    # cm: one merged mesh per 20 m wall section
MIN_GROUP = 8                    # don't merge cells with fewer stones than this
NAME_HINTS = ('stone', 'brick', 'rock', 'masonry', 'block', 'parapet', 'merlon')   # stone mesh names (lower case)
MAX_STONE_SIZE = 400.0           # cm: only small pieces (a stone/brick, not a whole wall mesh)
DEST = '/Game/CastleDefender/Environment/Castle/MergedStones'

try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\castle-stones-merge'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
groups, log = {}, []
for a in eas.get_all_level_actors():
    if not isinstance(a, unreal.StaticMeshActor): continue
    c = a.static_mesh_component; m = c.static_mesh
    if not m or not any(h in m.get_name().lower() for h in NAME_HINTS): continue
    o, e = a.get_actor_bounds(False)
    if max(e.x, e.y, e.z) * 2 > MAX_STONE_SIZE: continue
    mats = tuple(str(c.get_material(i).get_path_name()) if c.get_material(i) else '' for i in range(c.get_num_materials()))
    key = (int(math.floor(o.x / CELL)), int(math.floor(o.y / CELL)), mats)
    groups.setdefault(key, []).append(a)
todo = {k: v for k, v in groups.items() if len(v) >= MIN_GROUP}
n_in = sum(len(v) for v in todo.values())
log.append('stone actors found: %d in %d sections (>= %d stones each); after merge: %d actors' % (n_in, len(todo), MIN_GROUP, len(todo)))
if not DRY_RUN:
    for i, ((cx, cy, mats), actors) in enumerate(sorted(todo.items(), key=lambda kv: (kv[0][0], kv[0][1]))):
        opt = unreal.MergeStaticMeshActorsOptions()
        opt.set_editor_property('destroy_source_actors', True)
        opt.set_editor_property('spawn_merged_actor', True)
        opt.set_editor_property('new_actor_label', 'CastleStones_%d_%d_%d' % (cx, cy, i))
        opt.set_editor_property('base_package_name', '%s/SM_CastleStones_%d_%d_%d' % (DEST, cx, cy, i))
        ms = opt.get_editor_property('mesh_merging_settings')
        ms.set_editor_property('merge_materials', False)          # keep the original Megascans material (no atlas): same look
        ms.set_editor_property('bake_vertex_data_to_mesh', False)
        ms.set_editor_property('generate_light_map_uv', False)
        try: ms.set_editor_property('nanite_settings', unreal.MeshNaniteSettings(enabled=True))
        except Exception: pass
        opt.set_editor_property('mesh_merging_settings', ms)
        merged = sms.merge_static_mesh_actors(actors, opt)
        log.append('  section (%d,%d): %d stones -> %s' % (cx, cy, len(actors), merged.get_actor_label() if merged else 'FAILED'))
log.append('DRY RUN: nothing changed' if DRY_RUN else 'Done: save the level (Ctrl+S). Undo = reopen the backup map.')
out = 'Castle stones merge\n' + '\n'.join(log)
open(os.path.join(HERE, 'merge_castle_stones.txt'), 'w').write(out); unreal.log(out)
