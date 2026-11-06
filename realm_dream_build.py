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
if '--remove' in sys.argv:
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
# ---------------- A: grade / bloom / DOF ----------------
try:
    rv.modify(); pp=rv.get_component_by_class(unreal.PostProcessComponent); pp.modify()
    s=pp.get_editor_property('settings')
    for k,v in [('color_saturation',V(1.30,1.15,1.25,1.0)),('color_contrast',V(1.05,1.05,1.05,1.0)),('color_gamma',V(1.0,0.97,1.0,1.0)),
        ('color_gain',V(1.18,0.92,1.08,1.0)),('color_gain_shadows',V(1.10,0.62,0.85,1.0)),('color_offset_shadows',V(0.035,0.0,0.02,0.0)),
        ('color_gain_highlights',V(1.25,0.95,0.70,1.0)),('scene_color_tint',C(1.0,0.80,0.90,1.0)),('auto_exposure_bias',0.6),('white_temp',6200.0),
        ('bloom_intensity',3.0),('bloom_threshold',-1.0),('bloom_size_scale',6.0),('lens_flare_intensity',0.6),('lens_flare_tint',C(1.0,0.6,0.8,1.0)),
        ('scene_fringe_intensity',4.0),('vignette_intensity',0.35),('film_grain_intensity',0.12),
        ('depth_of_field_focal_distance',900.0),('depth_of_field_fstop',1.6),('depth_of_field_min_fstop',1.2)]:
        try: s.set_editor_property('override_'+k,True); s.set_editor_property(k,v)
        except Exception as ex: log('A skip %s: %s'%(k,str(ex)[:70]))
    pp.set_editor_property('settings',s); log('A grade/bloom/DOF set')
except Exception as ex: log('A ERR %s'%ex)
# ---------------- B: Local Fog Volumes ----------------
try:
    cls=getattr(unreal,'LocalFogVolume',None)
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
# ---------------- C: stronger dream post-process ----------------
try:
    mi=unreal.load_asset('/Game/CastleDefender/Gameplay/Realm/MI_RealmDream')
    for n,v in [('Warp',2.6),('Chroma',3.5),('Glow',2.4),('Haze',1.4),('Ghost',1.1),('Lift',1.6),('Lens',1.4),('Heart',0.6)]:
        MEL.set_material_instance_scalar_parameter_value(mi,n,v)
    MEL.update_material_instance(mi); EAL.save_asset(mi.get_path_name().split('.')[0]); log('C dream MI boosted')
except Exception as ex: log('C ERR %s'%ex)
# ---------------- D: vortex sky on the bubble's inside face ----------------
VORTEX=r'''
float3 d = WP - (Ctr + float3(0, 0, CoreH));
float L = length(d) + 1e-3; d /= L;
float rho = acos(clamp(d.z, -1.0, 1.0)) / 3.14159265;
float th = atan2(d.y, d.x);
float a = th + Twist / (rho + 0.12) + T * Spd;
float2 q = float2(cos(a), sin(a)) * (rho * 6.0 + 1.0) + T * 0.03;
float n = 0, amp = 0.5;
for (int i = 0; i < 4; i++) { n += amp * (0.5 + 0.5 * sin(q.x * 1.7 + sin(q.y * 1.3 + T * 0.2) * 2.1)); q = q * 2.03 + float2(1.7, 9.2); amp *= 0.5; }
float bands = 0.5 + 0.5 * sin(a * 3.0 + n * 6.0 - rho * 20.0);
float core = exp(-rho * 7.0) * 3.0;
float3 col = lerp(float3(1.0, 0.22, 0.55), float3(1.0, 0.48, 0.12), saturate(bands * n * 1.6)) * (0.5 + 1.5 * n) + float3(1.0, 0.85, 0.7) * core;
col *= Int;
float inside = (Sgn < 0.0) ? saturate(Amt) : 0.0;
return float4(lerp(EmOld, col, inside), lerp(OpOld, OpIn * (0.55 + 0.45 * n), inside));
'''
try:
    src='/Game/CastleDefender/Realm/M_RealmBubble3_Rim2S'
    dst=fresh('M_RealmBubble3_Dream','/Game/CastleDefender/Realm'); m=EAL.duplicate_asset(src,dst); assert m
    em=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    op=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_OPACITY)
    F4=enum(unreal.CustomMaterialOutputType,'CMOT_FLOAT4')
    cu=custom(m,VORTEX,['EmOld','OpOld','Sgn','WP','Ctr','T','Amt','Twist','Spd','CoreH','Int','OpIn'],F4,-300,900,'RealmVortex')
    MEL.connect_material_expressions(em,'',cu,'EmOld'); MEL.connect_material_expressions(op,'',cu,'OpOld')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionTwoSidedSign,-700,950),'',cu,'Sgn')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionWorldPosition,-700,1000),'',cu,'WP')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionObjectPositionWS,-700,1050),'',cu,'Ctr')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionTime,-700,1100),'',cu,'T')
    MEL.connect_material_expressions(mpcp(m,'Amount',-700,1150),'',cu,'Amt')
    for i,(n,v) in enumerate([('VortexTwist',1.2),('VortexSpeed',0.06),('VortexCoreHeight',4000.0),('VortexIntensity',6.0),('VortexOpacity',0.7)]):
        MEL.connect_material_expressions(sp(m,n,v,-700,1200+60*i),'',cu,{'VortexTwist':'Twist','VortexSpeed':'Spd','VortexCoreHeight':'CoreH','VortexIntensity':'Int','VortexOpacity':'OpIn'}[n])
    mrgb=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,-100,880)
    for k,v in (('r',True),('g',True),('b',True),('a',False)): mrgb.set_editor_property(k,v)
    ma=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,-100,980)
    for k,v in (('r',False),('g',False),('b',False),('a',True)): ma.set_editor_property(k,v)
    MEL.connect_material_expressions(cu,'',mrgb,''); MEL.connect_material_expressions(cu,'',ma,'')
    MEL.connect_material_property(mrgb,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(ma,'',unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); EAL.save_asset(dst)
    midst=fresh('MI_RealmBubble3_Dream','/Game/CastleDefender/Realm')
    mi=EAL.duplicate_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Rim2S',midst); MEL.set_material_instance_parent(mi,m); MEL.update_material_instance(mi); EAL.save_asset(midst)
    bub.modify(); bub.static_mesh_component.modify(); bub.static_mesh_component.set_material(0,mi)
    log('D vortex: %s on bubble (outside look unchanged; inside only via MPC Amount)'%midst)
except Exception as ex:
    import traceback; log('D ERR '+traceback.format_exc()[-600:])
# ---------------- E: caustic light ----------------
CAUSTIC=r'''
float2 p = WP.xy / Scale;
float c = 0;
for (int i = 0; i < 2; i++)
{
    float2 q = p * (1.0 + i * 0.73) + float2(T * 0.06 * (i + 1), -T * 0.045 * (i + 1));
    float2 g = floor(q), f = frac(q); float md = 8.0;
    for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++)
    {
        float2 o = float2(x, y);
        float2 h = frac(sin(float2(dot(g + o, float2(127.1, 311.7)), dot(g + o, float2(269.5, 183.3)))) * 43758.5453);
        h = 0.5 + 0.5 * sin(T * 0.6 + 6.2831853 * h);
        md = min(md, length(o + h - f));
    }
    c += pow(saturate(1.0 - md * 1.15), 5.0);
}
return c * Int * (0.15 + 0.85 * saturate(Amt));
'''
try:
    dst=fresh('M_RealmCausticLF'); m=AT.create_asset(dst.split('/')[-1],DEST,unreal.Material,unreal.MaterialFactoryNew())
    m.set_editor_property('material_domain',enum(unreal.MaterialDomain,'MD_LIGHT_FUNCTION'))
    F1=enum(unreal.CustomMaterialOutputType,'CMOT_FLOAT1')
    cu=custom(m,CAUSTIC,['WP','T','Amt','Scale','Int'],F1,-300,0,'RealmCaustic')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionWorldPosition,-700,-100),'',cu,'WP')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionTime,-700,0),'',cu,'T')
    MEL.connect_material_expressions(mpcp(m,'Amount',-700,100),'',cu,'Amt')
    MEL.connect_material_expressions(sp(m,'CausticScale',700.0,-700,200),'',cu,'Scale')
    MEL.connect_material_expressions(sp(m,'CausticIntensity',3.0,-700,300),'',cu,'Int')
    MEL.connect_material_property(cu,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(m.get_path_name().split('.')[0])
    z=ground(o.x,o.y) or (o.z-e.z*0.3)
    lt=E.spawn_actor_from_class(unreal.PointLight, unreal.Vector(o.x,o.y,z+5000), unreal.Rotator(0,0,0))
    lt.set_actor_label('Realm_DreamCaustic'); lt.tags=[unreal.Name('laptop2_realm'),unreal.Name('RealmDream')]
    lc=lt.get_component_by_class(unreal.PointLightComponent)
    lc.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    for k,v in [('intensity',60000.0),('light_color',unreal.Color(255,140,60,255)),('attenuation_radius',max(e.x,e.y)*1.2),('cast_shadows',False),
                ('light_function_material',m),('source_radius',800.0)]:
        try: lc.set_editor_property(k,v)
        except Exception as ex: log('E skip %s: %s'%(k,str(ex)[:60]))
    log('E caustic light at %d,%d,%d'%(o.x,o.y,z+5000))
except Exception as ex:
    import traceback; log('E ERR '+traceback.format_exc()[-600:])
# ---------------- G: glow bulbs ----------------
try:
    dst=fresh('M_RealmGlowBulb'); m=AT.create_asset(dst.split('/')[-1],DEST,unreal.Material,unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model',enum(unreal.MaterialShadingModel,'MSM_UNLIT'))
    gp=MEL.create_material_expression(m,unreal.MaterialExpressionVectorParameter,-500,0); gp.set_editor_property('parameter_name','Glow'); gp.set_editor_property('default_value',C(1.0,0.45,0.25,1))
    mu=MEL.create_material_expression(m,unreal.MaterialExpressionMultiply,-250,0)
    MEL.connect_material_expressions(gp,'',mu,'A'); MEL.connect_material_expressions(sp(m,'GlowIntensity',25.0,-500,150),'',mu,'B')
    MEL.connect_material_property(mu,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(m.get_path_name().split('.')[0])
    sph=unreal.load_asset('/Engine/BasicShapes/Sphere'); random.seed(381); n=0; nl=0
    for i in range(160):
        if n>=60: break
        ang=random.random()*6.283; rr=math.sqrt(random.random())*0.55
        x=o.x+math.cos(ang)*rr*e.x; y=o.y+math.sin(ang)*rr*e.y; z=ground(x,y)
        if z is None: continue
        for j in range(random.randint(1,4)):
            if n>=60: break
            px=x+random.uniform(-150,150); py=y+random.uniform(-150,150); s_=random.uniform(0.08,0.22)
            b=E.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(px,py,z+s_*50+random.uniform(5,40)), unreal.Rotator(0,0,0))
            b.set_actor_label('Realm_DreamBulb_%02d'%n); b.tags=[unreal.Name('laptop2_realm'),unreal.Name('RealmDream')]
            smc=b.static_mesh_component; smc.set_static_mesh(sph); smc.set_material(0,m); smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            smc.set_editor_property('cast_shadow',False); b.set_actor_scale3d(unreal.Vector(s_,s_,s_*1.15)); n+=1
        if nl<10:
            pl=E.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x,y,z+80), unreal.Rotator(0,0,0))
            pl.set_actor_label('Realm_DreamBulbLight_%02d'%nl); pl.tags=[unreal.Name('laptop2_realm'),unreal.Name('RealmDream')]
            c=pl.get_component_by_class(unreal.PointLightComponent)
            for k,v in [('intensity',600.0),('light_color',unreal.Color(255,120,90,255)),('attenuation_radius',700.0),('cast_shadows',False)]:
                try: c.set_editor_property(k,v)
                except Exception: pass
            nl+=1
    log('G %d glow bulbs, %d bulb lights'%(n,nl))
except Exception as ex:
    import traceback; log('G ERR '+traceback.format_exc()[-600:])
log('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
open(OUT,'w').write('\n'.join(L))
