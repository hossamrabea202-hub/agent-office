# Tune 1 after the owner's Play test 00:08: "very dark green", "glitch at the edge of the screen feels fake".
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L=[]; V=unreal.Vector4; C=unreal.LinearColor
acts=E.get_all_level_actors()
rv=[a for a in acts if a.get_actor_label()=='Realm_Vision'][0]
rv.modify(); pp=rv.get_component_by_class(unreal.PostProcessComponent); pp.modify()
s=pp.get_editor_property('settings')
for k,v in [('auto_exposure_bias',1.6),('auto_exposure_min_brightness',0.6),('scene_color_tint',C(1.0,0.74,0.86,1.0)),('white_temp',5000.0),('white_tint',0.35),
    ('color_gain',V(1.25,0.88,1.05,1.0)),('color_gain_shadows',V(1.25,0.55,0.85,1.0)),('color_offset_shadows',V(0.06,0.005,0.035,0.0)),
    ('color_gain_midtones',V(1.12,0.86,1.0,1.0)),('color_gain_highlights',V(1.25,0.92,0.72,1.0)),('color_saturation',V(1.25,1.05,1.2,1.0)),
    ('scene_fringe_intensity',1.2),('vignette_intensity',0.15),('bloom_intensity',3.5)]:
    try: s.set_editor_property('override_'+k,True); s.set_editor_property(k,v)
    except Exception as ex: L.append('skip %s %s'%(k,str(ex)[:60]))
pp.set_editor_property('settings',s); L.append('grade: brighter, pink, less fringe')
mi=unreal.load_asset('/Game/CastleDefender/Gameplay/Realm/MI_RealmDream')
for n,v in [('Chroma',1.0),('Warp',1.4),('Ghost',0.6),('Lift',2.6),('Glow',2.6),('Haze',1.2),('Heart',0.3)]:
    MEL.set_material_instance_scalar_parameter_value(mi,n,v)
MEL.update_material_instance(mi); EAL.save_asset('/Game/CastleDefender/Gameplay/Realm/MI_RealmDream'); L.append('dream MI: calmer edges, lifted shadows')
# vortex: fewer, softer bands so the near bubble wall doesn't stripe at the screen edge
b=[a for a in acts if a.get_actor_label()=='Realm_Bubble_Owner'][0]
bm=b.static_mesh_component.get_material(0)
if 'Dream' in bm.get_name():
    for n,v in [('VortexOpacity',0.45),('VortexIntensity',4.0),('VortexTwist',0.8)]:
        MEL.set_material_instance_scalar_parameter_value(bm,n,v)
    MEL.update_material_instance(bm); EAL.save_asset(bm.get_path_name().split('.')[0]); L.append('vortex softer on %s'%bm.get_name())
L.append('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
open(r'C:/Users/hossa/Documents/agent-office/_dream_out.txt','w').write('\n'.join(L))
