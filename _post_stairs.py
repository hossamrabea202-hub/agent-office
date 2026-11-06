import subprocess, unreal, json
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
r = subprocess.run(['gh', 'issue', 'create', '--repo', 'hossamrabea202-hub/agent-office', '--title', 'AAA staircases: one watertight mesh per flight, high poly baked to low poly (TGA)', '--body-file', r'C:\Users\hossa\Documents\agent-office\_c_stairs.md'], capture_output=True, text=True, creationflags=0x08000000)
# remove stair-wear decals, thin base grime
A = [a for a in eas.get_all_level_actors() if unreal.Name('CastleV2') in a.tags]
sw = [a for a in A if a.get_actor_label().startswith('V2_StairWear')]
for a in sw: eas.destroy_actor(a)
G = [a for a in A if a.get_actor_label().startswith('V2_BaseGrime')]; keep = []; kill = 0
for a in G:
    p = a.get_actor_location()
    if any((p - q).length() < 300 for q in keep): eas.destroy_actor(a); kill += 1
    else: keep.append(p)
# stair export for TGA
S = []
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor):
        m = a.static_mesh_component.static_mesh; n = (a.get_actor_label() + ' ' + (m.get_name() if m else '')).lower()
        if any(k in n for k in ('stair', 'step', 'tread')):
            o, e = a.get_actor_bounds(False); t = a.get_actor_transform()
            S.append({'label': a.get_actor_label(), 'mesh': m.get_path_name() if m else None, 'folder': str(a.get_folder_path()), 'loc': [t.translation.x, t.translation.y, t.translation.z], 'rot': [t.rotation.rotator().roll, t.rotation.rotator().pitch, t.rotation.rotator().yaw], 'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z], 'bounds_center': [o.x, o.y, o.z], 'bounds_ext': [e.x, e.y, e.z]})
json.dump(S, open(r'C:\Users\hossa\Documents\agent-office\_stairs_export.json', 'w'), indent=0)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
res = 'card rc=%s %s %s | stair decals removed %d | base grime removed %d kept %d | stairs exported %d | actors %d' % (r.returncode, r.stdout.strip(), r.stderr[-150:], len(sw), kill, len(keep), len(S), len(eas.get_all_level_actors()))
open(r'C:\Users\hossa\Documents\agent-office\_post_stairs.txt', 'w').write(res); print(res)
