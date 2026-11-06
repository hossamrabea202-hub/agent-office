# Realm dream look steps A+B (owner target 23:51). A: grade/bloom/DOF on Realm_Vision PP. B: Local Fog Volumes inside the bubble.
import unreal, sys
L=[]
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts=E.get_all_level_actors()
rv=[a for a in acts if a.get_actor_label()=='Realm_Vision'][0]
bub=[a for a in acts if a.get_actor_label()=='Realm_Bubble_Owner'][0]
rv.modify()
pp=rv.get_component_by_class(unreal.PostProcessComponent); pp.modify()
s=pp.get_editor_property('settings')
V=unreal.Vector4; C=unreal.LinearColor
look=[('color_saturation',V(1.30,1.15,1.25,1.0)),('color_contrast',V(1.05,1.05,1.05,1.0)),('color_gamma',V(1.0,0.97,1.0,1.0)),
 ('color_gain',V(1.18,0.92,1.08,1.0)),('color_gain_shadows',V(1.10,0.62,0.85,1.0)),('color_offset_shadows',V(0.035,0.0,0.02,0.0)),
 ('color_gain_highlights',V(1.25,0.95,0.70,1.0)),('scene_color_tint',C(1.0,0.80,0.90,1.0)),('auto_exposure_bias',0.6),
 ('bloom_intensity',3.0),('bloom_threshold',-1.0),('bloom_size_scale',6.0),('lens_flare_intensity',0.6),('lens_flare_tint',C(1.0,0.6,0.8,1.0)),
 ('scene_fringe_intensity',4.0),('vignette_intensity',0.35),('film_grain_intensity',0.12),
 ('depth_of_field_focal_distance',900.0),('depth_of_field_fstop',1.6),('depth_of_field_min_fstop',1.2)]
for k,v in look:
    try: s.set_editor_property('override_'+k,True); s.set_editor_property(k,v); L.append('A %s ok'%k)
    except Exception as e: L.append('A %s SKIP %s'%(k,str(e)[:80]))
pp.set_editor_property('settings',s)
# ---- B: Local Fog Volumes
for a in acts:
    if a.get_actor_label().startswith('Realm_DreamFog_'): E.destroy_actor(a)
o,e=bub.get_actor_bounds(False)
w=unreal.EditorLevelLibrary.get_editor_world()
def ground(x,y):
    h=unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x,y,o.z+e.z), unreal.Vector(x,y,o.z-e.z), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [bub], unreal.DrawDebugTrace.NONE, True)
    try:
        hr=h.to_tuple(); return hr[4].z if hr[0] else None
    except Exception: return None
cls=getattr(unreal,'LocalFogVolume',None)
L.append('LocalFogVolume class %s'%cls)
if cls:
    pts=[(0,0),(0.35,0.2),(-0.35,0.15),(0.2,-0.4),(-0.25,-0.35)]
    for i,(fx,fy) in enumerate(pts):
        x=o.x+fx*e.x; y=o.y+fy*e.y; z=ground(x,y)
        if z is None: L.append('B fog %d no ground'%i); continue
        f=E.spawn_actor_from_class(cls, unreal.Vector(x,y,z+600), unreal.Rotator(0,0,0))
        f.set_actor_label('Realm_DreamFog_%d'%i); f.tags=[unreal.Name('laptop2_realm'),unreal.Name('RealmDream')]
        f.set_actor_scale3d(unreal.Vector(9,9,9))
        c=f.get_component_by_class(unreal.LocalFogVolumeComponent) if hasattr(unreal,'LocalFogVolumeComponent') else f.root_component
        for k,v in [('radial_fog_extinction',0.6),('height_fog_extinction',0.9),('height_fog_falloff',600.0),('height_fog_offset',0.0),
                    ('fog_albedo',C(1.0,0.45,0.65,1.0)),('fog_emissive',C(0.35,0.10,0.14,1.0)),('fog_phase_g',0.4)]:
            try: c.set_editor_property(k,v)
            except Exception as ex: L.append('B %s SKIP %s'%(k,str(ex)[:60]))
        L.append('B fog %d at %d,%d,%d'%(i,x,y,z+600))
L.append('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
open(r'C:/Users/hossa/Documents/agent-office/_dreamAB_out.txt','w').write('\n'.join(L))
