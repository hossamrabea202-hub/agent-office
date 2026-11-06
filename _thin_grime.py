import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
G = [a for a in eas.get_all_level_actors() if unreal.Name('CastleV2') in a.tags and a.get_actor_label().startswith('V2_BaseGrime')]
keep, kill = [], []
for a in G:
    p = a.get_actor_location()
    if any((p - q).length() < 300 for q in keep): kill.append(a)
    else: keep.append(p)
for a in kill: eas.destroy_actor(a)
S = [a for a in eas.get_all_level_actors() if unreal.Name('CastleV2') in a.tags and a.get_actor_label().startswith('V2_StairWear')]
ks, kk = [], []
for a in S:
    p = a.get_actor_location()
    if any((p - q).length() < 20 for q in ks): kk.append(a)
    else: ks.append(p)
for a in kk: eas.destroy_actor(a)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
r = 'base grime %d -> %d, stair wear %d -> %d, actors now %d' % (len(G), len(keep), len(S), len(ks), len(eas.get_all_level_actors()))
open(r'C:\Users\hossa\Documents\agent-office\_thin_grime.txt', 'w').write(r); print('THIN', r)
