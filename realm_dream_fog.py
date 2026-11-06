# Realm dream look, full build by the Master (owner target 2026-10-31 23:51, handoffs/realm-dream-research).
#   A grade/bloom/DOF on Realm_Vision    B pink Local Fog Volumes       C stronger dream post-process (MI_RealmDream)
#   D vortex sky on the bubble's INSIDE face (only while inside, via MPC Amount)   E moving caustic light   G glow bulbs
# Run: (no args) builds/rebuilds everything.  --remove: deletes the spawned actors and puts the bubble back on MI_RealmBubble3_Rim2S.
import unreal, sys, random, math
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary; AT=unreal.AssetToolsHelpers.get_asset_tools()
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
DEST='/Game/CastleDefender/Gameplay/Realm/Dream'
MPC='/Game/CastleDefender/Gameplay/Realm/MPC_RealmDream'
OUT=r'C:/Users/hossa/Documents/agent-office/_dream_out.txt'
L=[]; V=unreal.Vector4; C=unreal.LinearColor
def log(s): L.append(s)
acts=E.get_all_level_actors()
rv=[a for a in acts if a.get_actor_label()=='Realm_Vision'][0]
bub=[a for a in acts if a.get_actor_label()=='Realm_Bubble_Owner'][0]
for a in acts:
    if a.get_actor_label().startswith(('Realm_DreamFog_','Realm_DreamBulb_','Realm_DreamBulbLight_','Realm_DreamCaustic')): E.destroy_actor(a)
if False:
    bub.modify(); bub.static_mesh_component.modify()
    bub.static_mesh_component.set_material(0, unreal.load_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Rim2S'))
    log('removed; bubble back on Rim2S; save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
    open(OUT,'w').write('\n'.join(L)); raise SystemExit
def enum(cls,*names):
    for n in names:
        if hasattr(cls,n): return getattr(cls,n)
def custom(m,code,ins,otype,x,y,desc):
    c=MEL.create_material_expression(m,unreal.MaterialExpressionCustom,x,y)
    c.set_editor_property('code',code); c.set_editor_property('output_type',otype); c.set_editor_property('description',desc)
    arr=[]
    for n in ins:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
    c.set_editor_property('inputs',arr); return c
def sp(m,n,v,x,y):
    e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,x,y); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v); return e
def mpcp(m,n,x,y):
    e=MEL.create_material_expression(m,unreal.MaterialExpressionCollectionParameter,x,y)
    e.set_editor_property('collection',unreal.load_asset(MPC)); e.set_editor_property('parameter_name',n); return e
def fresh(name,parent_dir=DEST):
    p=parent_dir+'/'+name; i=0
    while EAL.does_asset_exist(p): i+=1; p='%s/%s_%d'%(parent_dir,name,i)
    return p
if not EAL.does_directory_exist(DEST): EAL.make_directory(DEST)
o,e=bub.get_actor_bounds(False)
w=unreal.EditorLevelLibrary.get_editor_world()
def ground(x,y):
    try:
        h=unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x,y,o.z+e.z), unreal.Vector(x,y,o.z-e.z), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [bub], unreal.DrawDebugTrace.NONE, True)
        t=h.to_tuple()
        return t[4].z if t[0] else None
    except Exception as ex: log('trace err %s'%ex); return None
# ---------------- B: Local Fog Volumes ----------------
try:
    cls=getattr(unreal,'LocalFogVolume',None) or unreal.load_class(None,'/Script/Engine.LocalFogVolume')
    log('B class %s'%cls)
    if not cls: log('B: no LocalFogVolume class in this build')
    else:
        for i,(fx,fy) in enumerate([(0,0),(0.35,0.2),(-0.35,0.15),(0.2,-0.4),(-0.25,-0.35)]):
            x=o.x+fx*e.x; y=o.y+fy*e.y; z=ground(x,y)
            if z is None: log('B fog %d: no ground'%i); continue
            f=E.spawn_actor_from_class(cls, unreal.Vector(x,y,z+700), unreal.Rotator(0,0,0))
            f.set_actor_label('Realm_DreamFog_%d'%i); f.tags=[unreal.Name('laptop2_realm'),unreal.Name('RealmDream')]
            f.set_actor_scale3d(unreal.Vector(10,10,10))
            comps=f.get_components_by_class(unreal.ActorComponent); c=[x for x in comps if 'Fog' in x.get_class().get_name()]
            c=c[0] if c else f.root_component
            for k,v in [('radial_fog_extinction',0.5),('height_fog_extinction',0.8),('height_fog_falloff',500.0),
                        ('fog_albedo',C(1.0,0.45,0.65,1.0)),('fog_emissive',C(0.30,0.08,0.12,1.0)),('fog_phase_g',0.4)]:
                try: c.set_editor_property(k,v)
                except Exception as ex: log('B skip %s: %s'%(k,str(ex)[:60]))
            log('B fog %d at %d,%d,%d'%(i,x,y,z+700))
except Exception as ex: log('B ERR %s'%ex)
log('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
open(OUT,'w').write('\n'.join(L))
