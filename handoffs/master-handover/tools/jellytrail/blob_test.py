"""blob_test.py (Simulate, parked RevengeTestBall): STEP file blob_step.txt = hit | land | fire | after"""
import unreal, os, json
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
LOG = os.path.join(D, 'jellytrail', 'blob_test_log.txt')
step = open(os.path.join(D, 'jellytrail', 'blob_step.txt')).read().strip()
GS = unreal.GameplayStatics
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
L = ['--- %s t=%.1f' % (step, GS.get_time_seconds(w) if w else -1)]
acts = GS.get_all_actors_of_class(w, unreal.Actor)
mgr = [a for a in acts if a.get_class().get_name() == 'BP_JellyTrailManager_C'][0]
blobs = [a for a in acts if a.get_class().get_name() == 'BP_JellyBlob_C']
shells = [a for a in acts if a.get_class().get_name() == 'BP_ZombieJellyShield_C']
L.append('Head %d blobs %d hatched-shields %d Active %d' % (mgr.get_editor_property('Head'), len(blobs), len(shells), len(mgr.get_editor_property('Active'))))
if step == 'hit':
    ball = [a for a in acts if a.get_actor_label() == 'RevengeTestBall'][0]
    cannons = [a for a in acts if a.get_class().get_name() == 'BP_Cannon_C']
    v = [a for a in acts if a.get_actor_label() == 'TentacleVitals_Fog1_11'][0]
    hit = [a for a in v.get_attach_parent_actor().get_attached_actors() if a.actor_has_tag('TentacleHit')]
    hit.sort(key=lambda a: a.get_actor_location().z)
    ball.set_owner(cannons[0]); ball.set_actor_location(hit[2].get_actor_location() + unreal.Vector(0, 0, 200), False, True)
    GS.apply_damage(hit[2], 2000.0, None, ball, None)
    L.append('hit %s at %s' % (hit[2].get_actor_label(), hit[2].get_actor_location()))
for b in blobs:
    body = b.get_editor_property('Body')
    L.append('  %s at %s scale %s' % (b.get_name(), body.get_world_location(), b.get_editor_property('Blob').get_editor_property('relative_scale3d')))
if step == 'fire':
    for b in blobs:
        mgr.call_method('Ignite', (b.get_editor_property('Body').get_world_location(), 150.0))
    L.append('ignited under %d blobs -> Active %d' % (len(blobs), len(mgr.get_editor_property('Active'))))
open(LOG, 'a').write('\n'.join(L) + '\n')
