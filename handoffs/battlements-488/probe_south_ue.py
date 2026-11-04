# #488 (i5, read-only): curtain / merlon actors on the open map, with bounds, to plan the south row.
import unreal
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = []
for a in sub.get_all_level_actors():
    lab = a.get_actor_label()
    if not any(k in lab.lower() for k in ('curtain', 'merlon', 'battlement', 'castlestones', 'parapet')): continue
    o, e = a.get_actor_bounds(False)
    rows.append((lab, a.get_class().get_name(), round(o.x), round(o.y), round(o.z), round(e.x), round(e.y), round(e.z), str(a.get_folder_path())))
print('world', unreal.EditorLevelLibrary.get_editor_world().get_name(), len(rows))
for r in sorted(rows)[:80]: print(r)
