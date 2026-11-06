import unreal
import _mh
bp = unreal.load_asset(_mh.find('BP_WallBreachSpot')); cls = bp.generated_class()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); L = []
for a in eas.get_all_level_actors():
    if a.get_class() != cls: continue
    n = 0
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.static_mesh
        if sm and sm.get_name().startswith('SM_Rock_'):
            c.modify(); c.set_editor_property('visible', False); c.set_visibility(False, False)
            c.set_editor_property('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO); n += 1
    a.modify(); L.append('%s: %d rocks hidden' % (a.get_actor_label(), n))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(r'C:\Users\hossa\Documents\agent-office\_fix237b.txt', 'w').write('\n'.join(L)); print('FIX237B', L)
