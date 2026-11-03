import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
p = next(a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'LandscapeStreamingProxy_3_4_0')
print('PROXY methods', [m for m in dir(p) if 'material' in m.lower() or 'landscape' in m.lower()][:40])
try: print('parent', p.get_landscape_actor() if hasattr(p, 'get_landscape_actor') else None)
except Exception as e: print('parent err', e)
print('classes', sorted(set(a.get_class().get_name() for a in EAS.get_all_level_actors() if 'andscape' in a.get_class().get_name())))
c = p.get_components_by_class(unreal.LandscapeComponent)
print('components', len(c), [m for m in dir(c[0]) if 'material' in m.lower()][:30] if c else None)
