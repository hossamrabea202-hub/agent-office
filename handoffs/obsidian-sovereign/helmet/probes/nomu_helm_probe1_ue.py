# Read-only (#485): set data + hero copy + piece bounds. No saves, no spawns.
import unreal, json
print('PIE', bool(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()))
ROOT='/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign'
setc=unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet').generated_class()
cdo=unreal.get_default_object(setc)
hero=unreal.load_asset('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);L=unreal.SubobjectDataBlueprintFunctionLibrary
tpl=None;comps={}
for h in sub.k2_gather_subobject_data_for_blueprint(hero):
    d=L.get_data(h);o=L.get_object(d)
    if not o: continue
    comps[str(L.get_variable_name(d))]=o
    if o.get_class()==setc: tpl=o
for lab,obj in (('CDO',cdo),('HERO',tpl)):
    print(lab, obj)
    for n in ('AvailMask','ObsOwned','ObsWorn','KnightCover','PieceId','PieceBone','BundleMask','PartPrice','PartBundle','BundleCost','BundleNames','TierAt','TierDR','SetNames','HiddenMat'):
        try:
            v=obj.get_editor_property(n)
            print(' ',n,[str(x) for x in v] if hasattr(v,'__iter__') and not isinstance(v,str) else v)
        except Exception as e: print(' ',n,'ERR',e)
    po=obj.get_editor_property('PieceOffset')
    for i,t in enumerate(po):
        r=t.rotation.rotator()
        print('  off',i,[round(x,3) for x in (t.translation.x,t.translation.y,t.translation.z,r.roll,r.pitch,r.yaw,t.scale3d.x)])
print('comps',sorted(comps))
for n,c in sorted(comps.items()):
    if n.startswith('Obs_') :
        sm=c.get_editor_property('static_mesh');b=sm.get_bounding_box()
        print(n,[str(t) for t in c.get_editor_property('component_tags')],sm.get_name(),'tris',sm.get_num_triangles(0) if hasattr(sm,'get_num_triangles') else '?','min',[round(x,1) for x in (b.min.x,b.min.y,b.min.z)],'max',[round(x,1) for x in (b.max.x,b.max.y,b.max.z)],'vis',c.get_editor_property('visible'),'overlay',c.get_editor_property('overlay_material'),'cast',c.get_editor_property('cast_shadow'), 'rel', c.get_editor_property('relative_location'))
mi=unreal.load_asset(ROOT+'/Shoulders/MI_ObsidianSovereign_Shoulders')
print('MI parent',mi.get_editor_property('parent'),[ (str(p.parameter_info.name),p.scalar_value) for p in mi.get_editor_property('scalar_parameter_values')],[ (str(p.parameter_info.name),p.parameter_value.get_name()) for p in mi.get_editor_property('texture_parameter_values')],[ (str(p.parameter_info.name),p.parameter_value) for p in mi.get_editor_property('vector_parameter_values')])
