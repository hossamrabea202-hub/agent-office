# Realm vision (owner 2026-10-31): the world looks different while the camera is INSIDE the realm bubble.
# BP_RealmVision = Sphere (shape) + PostProcessComponent (bounded by that sphere, soft blend at the membrane).
# The placed actor is ATTACHED to Realm_Bubble_Owner, so it moves/scales/bounces with the bubble. Never edits the bubble.
# Re-run after reshaping the bubble: it re-fits the sphere to the bubble's current bounds.  --remove deletes the actor.
import unreal, sys
EAL=unreal.EditorAssetLibrary; BEL=unreal.BlueprintEditorLibrary
SDS=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); LIB=unreal.SubobjectDataBlueprintFunctionLibrary
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
P='/Game/CastleDefender/Gameplay/Realm/BP_RealmVision'
log=[]
bub=[a for a in E.get_all_level_actors() if a.get_actor_label()=='Realm_Bubble_Owner'][0]
old=[a for a in E.get_all_level_actors() if a.get_actor_label()=='Realm_Vision']
for a in old: E.destroy_actor(a)
if '--remove' in sys.argv:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); raise SystemExit
if not EAL.does_asset_exist(P):
    f=unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_RealmVision','/Game/CastleDefender/Gameplay/Realm',unreal.Blueprint,f)
    root=SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    h,_=SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root,new_class=unreal.SphereComponent,blueprint_context=bp)); SDS.rename_subobject(h,unreal.Text('Shape'))
    h2,_=SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=h,new_class=unreal.PostProcessComponent,blueprint_context=bp)); SDS.rename_subobject(h2,unreal.Text('Vision'))
    BEL.compile_blueprint(bp); EAL.save_asset(P); log.append('created '+P)
bp=unreal.load_asset(P)
o,e,r=unreal.SystemLibrary.get_component_bounds(bub.static_mesh_component)
a=E.spawn_actor_from_class(bp.generated_class(), o, unreal.Rotator(0,0,0))
a.set_actor_label('Realm_Vision'); a.tags=[unreal.Name('laptop2_realm'),unreal.Name('RealmVision')]
sph=a.get_component_by_class(unreal.SphereComponent); pp=a.get_component_by_class(unreal.PostProcessComponent)
rad=min(e.x,e.y,e.z)*0.98          # fit inside the membrane (works for any reshaped bubble: re-run after sculpting)
sph.set_editor_property('sphere_radius', rad); sph.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
s=pp.get_editor_property('settings')
def S(k,v):
    s.set_editor_property('override_'+k, True); s.set_editor_property(k, v)
S('color_saturation', unreal.Vector4(0.78,0.86,0.80,1.0))
S('color_contrast', unreal.Vector4(1.12,1.12,1.12,1.0))
S('color_gain', unreal.Vector4(0.92,1.04,0.94,1.0))
S('color_gamma', unreal.Vector4(0.97,1.0,1.02,1.0))
S('scene_color_tint', unreal.LinearColor(0.86,1.0,0.88,1.0))
S('scene_fringe_intensity', 1.6)            # chromatic aberration at the edges: seen through a membrane
S('vignette_intensity', 0.75)
S('bloom_intensity', 1.6)
S('film_grain_intensity', 0.25)
S('auto_exposure_bias', -0.35)
pp.set_editor_property('settings', s)
pp.set_editor_property('unbound', False)
pp.set_editor_property('blend_radius', max(300.0, rad*0.04))
pp.set_editor_property('blend_weight', 1.0)
pp.set_editor_property('priority', 5.0)
a.attach_to_actor(bub, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
log.append('Realm_Vision at %s radius %.0f (bubble half-extent %s), attached to Realm_Bubble_Owner'%(o, rad, e))
log.append('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
open(r'C:/Users/hossa/Documents/agent-office/_rv_out.txt','w').write('\n'.join(log))
