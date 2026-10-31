# READ-ONLY (UE 5.3, Master): dump every stair-related actor for #279/#301 so TGA can fix the placement offline.
#   py "<repo>/assets/tga/StairKit/dump_stairs_ue.py"      -> Saved/stair279_dump.json (changes nothing in the level)
# Push the JSON to handoffs/exports/master/stair279_dump.json (and Saved/stair279_report.json if it is still there).
import unreal, json, os, re
PAT = re.compile(r'(Stair|Step|Tread|Cube_|StoneModule|WalkSlab|Ramp|Landing)', re.I)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if not PAT.search(lab): continue
    o, e = a.get_actor_bounds(False); l = a.get_actor_location(); r = a.get_actor_rotation(); s = a.get_actor_scale3d()
    smc = a.get_component_by_class(unreal.StaticMeshComponent); sm = smc.static_mesh if smc else None
    lb = sm.get_bounds() if sm else None
    out.append(dict(label=lab, cls=a.get_class().get_name(), mesh=sm.get_path_name() if sm else None, folder=str(a.get_folder_path()),
                    hidden=a.is_hidden_ed(), tags=[str(t) for t in a.tags],
                    loc=[l.x, l.y, l.z], rot=[r.pitch, r.yaw, r.roll], scale=[s.x, s.y, s.z],
                    bmin=[o.x - e.x, o.y - e.y, o.z - e.z], bmax=[o.x + e.x, o.y + e.y, o.z + e.z],
                    local=[lb.origin.x, lb.origin.y, lb.origin.z, lb.box_extent.x, lb.box_extent.y, lb.box_extent.z] if lb else None))
p = os.path.join(unreal.Paths.project_saved_dir(), 'stair279_dump.json')
json.dump(out, open(p, 'w'), indent=0)
unreal.log('[stair279 dump] %d actors -> %s (read only, nothing changed)' % (len(out), p))
