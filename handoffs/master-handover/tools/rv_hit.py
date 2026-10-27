import unreal, os, json
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
GS = unreal.GameplayStatics
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
L = []
GS.set_game_paused(gw, False)
acts = GS.get_all_actors_of_class(gw, unreal.Actor)
ball = [a for a in acts if a.get_actor_label() == 'RevengeTestBall']
cannons = [a for a in acts if a.get_class().get_name() == 'BP_Cannon_C' and a.actor_has_tag('Cannon')]
vit = [a for a in acts if a.get_class().get_name() == 'BP_TentacleVitals_C']
L.append('ball %s cannons %d vitals %d t=%.1f' % (bool(ball), len(cannons), len(vit), GS.get_time_seconds(gw)))
info = []
for v in vit:
    t = v.get_attach_parent_actor()
    sk = t.get_component_by_class(unreal.SkeletalMeshComponent)
    root = sk.get_socket_location('seg_00')
    ds = sorted(((c.get_actor_location() - root).length(), c) for c in cannons)
    inr = [(d, c) for d, c in ds if d <= 19000]
    shell = [c for c in t.get_components_by_class(unreal.SkeletalMeshComponent) if c.component_has_tag('JellyShell')]
    smax = shell[0].create_dynamic_material_instance(0).get_scalar_parameter_value('ShieldMax') if shell else -1
    hits = [a for a in t.get_attached_actors() if a.actor_has_tag('TentacleHit')]
    info.append((v, t, inr, smax, hits))
    L.append('%s in-range %s smax %.0f hits %d' % (v.get_actor_label(), ['%s %.0f' % (c.get_actor_label(), d) for d, c in inr[:3]], smax, len(hits)))
two = [x for x in info if len(x[2]) >= 2]
one = [x for x in info if len(x[2]) >= 1 and x not in two[:1]]
ids = {}
if two and ball:
    v, t, inr, smax, hits = two[0]
    B = inr[1][1]                                     # second-nearest = the attacker
    ball[0].set_owner(B)
    GS.apply_damage(hits[0], smax + 1000.0, None, ball[0], None)
    ids['A'] = [v.get_path_name(), B.get_path_name(), inr[0][1].get_path_name()]
    L.append('A: %s shield-break by ball owned by %s (nearest is %s)' % (v.get_actor_label(), B.get_actor_label(), inr[0][1].get_actor_label()))
if one:
    v, t, inr, smax, hits = one[0]
    GS.apply_damage(hits[0], smax + 95000.0, None, None, None)
    ids['C'] = [v.get_path_name(), inr[0][1].get_path_name()]
    L.append('C: %s HP-drop, no causer (nearest %s)' % (v.get_actor_label(), inr[0][1].get_actor_label()))
json.dump(ids, open(os.path.join(D, 'rv_ids.json'), 'w'))
open(os.path.join(D, 'rv_hit_log.txt'), 'w').write('\n'.join(L))
