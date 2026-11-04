# #491 (i5 for i9, READ-ONLY, ~10 s): world transform of every placed mesh named like a box in the *_specs.json, so
# layout_kit491.py can cut the walls at the deck. Changes nothing, saves nothing.
#   py <repo>/handoffs/stone-kit-491/dump_wall_xforms_ue.py           writes handoffs/stone-kit-491/wall_xforms.json
import json, os, unreal
HERE = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(HERE, 'curtain_specs.json')):          # run from a copy (i5 inbox): the folder in the same repo
    HERE = os.path.join(HERE.split('handoffs')[0], 'handoffs', 'stone-kit-491')
names = set()
for f in ('curtain_specs.json', 'keep_specs.json', 'mason2_specs.json'):
    names |= {b['name'] for b in json.load(open(os.path.join(HERE, f)))['boxes']}
out = {}
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.static_mesh
        if not m or m.get_name() not in names: continue
        t = c.get_world_transform(); r = t.rotation.rotator()
        out.setdefault(m.get_name(), []).append(dict(actor=a.get_actor_label(), loc=[round(t.translation.x, 2), round(t.translation.y, 2), round(t.translation.z, 2)],
                                                     rot=[round(r.roll, 3), round(r.pitch, 3), round(r.yaw, 3)], scale=[round(t.scale3d.x, 4), round(t.scale3d.y, 4), round(t.scale3d.z, 4)]))
dst = os.path.join(HERE, 'wall_xforms.json'); json.dump(out, open(dst, 'w'), indent=1)
print('wall_xforms: %d of %d box meshes placed, %d placements -> %s' % (len(out), len(names), sum(len(v) for v in out.values()), dst))
