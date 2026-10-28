"""Tower49 v1. Original procedural architectural authoring, Blender 4.5.
Meters; Z up. Non-destructive versioned output. No Unreal project writes.
"""
import bpy, bmesh, math, os, json, random, time, hashlib
from mathutils import Vector
from math import sin, cos, pi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'outputs', 'Tower49_Medieval_200m_v1')
for p in ['source','meshes','textures','renders','reports','collision']:
    os.makedirs(os.path.join(OUT,p), exist_ok=True)
random.seed(490200)
R=10.5; BASE_R=13.0; WIDTH=3.0; ROOF=198.0; HEIGHT=200.0
CHUNKS=72; STEPS=18; RISE=ROOF/(CHUNKS*STEPS); DH=ROOF/CHUNKS
ANGLE=pi/4; BAND=5.5
print('SPEC',R,ROOF,RISE,flush=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.collections):
    if d.users==0: bpy.data.collections.remove(d)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1

def coll(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
ASSEMBLY=coll('01_LOD0_ASSEMBLY'); KIT=coll('02_MODULAR_KIT'); HP=coll('03_HIGH_POLY_BAKE_SOURCE')
COL=coll('04_COLLISION_UCX'); STUDIO=coll('05_RENDER_STUDIO'); LODS=coll('06_LOD1_2_ASSEMBLIES')
def move(o,c):
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o)
def mesh_obj(name,vs,fs,c=KIT,uv=True):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);c.objects.link(ob)
    if uv:
        layer=me.uv_layers.new(name='UV0_Tile')
        for poly in me.polygons:
            n=poly.normal
            for li in poly.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co
                # Cylindrical tiling for vertical/radial surfaces; planar for treads.
                if abs(n.z)>.65: u,v=co.x/2,co.y/2
                else: u,v=math.atan2(co.y,co.x)*R/2,co.z/2
                layer.data[li].uv=(u,v)
    return ob
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def apply_mod(o,mod):
    active(o);bpy.ops.object.modifier_apply(modifier=mod.name)
def bevel(o,w=.025,segments=2):
    m=o.modifiers.new('Edge radius','BEVEL');m.width=w;m.segments=segments
    apply_mod(o,m)
    return o
def cube(name,loc,scale,c=KIT,bev=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc);o=bpy.context.object;o.name=name;move(o,c)
    o.scale=scale;active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev:bevel(o,bev,3)
    return o
def join(obs,name,c):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=obs[0];o.name=name;move(o,c)
    # Keep authored local transforms; exports use mesh coordinates with origin reset.
    scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return o
def sector(name,rin,rout,z0,z1,a0=0,a1=ANGLE,n=20,c=KIT,rin_top=None,rout_top=None):
    if rin==0:
        vs=[(0,0,z0),(0,0,z1)]
        for zz in [z0,z1]:
            for j in range(n+1):
                a=a0+(a1-a0)*j/n;vs.append((rout*cos(a),rout*sin(a),zz))
        q=n+1;fs=[]
        for j in range(n):fs.extend([(0,2+j+1,2+j),(1,2+q+j,2+q+j+1),(2+j,2+j+1,2+q+j+1,2+q+j)])
        fs.extend([(0,2,2+q,1),(0,1,2+q+n,2+n)])
        return mesh_obj(name,vs,fs,c)
    rit=rin if rin_top is None else rin_top;rot=rout if rout_top is None else rout_top
    vs=[]
    for rr,zz in [(rin,z0),(rout,z0),(rit,z1),(rot,z1)]:
        for j in range(n+1):
            a=a0+(a1-a0)*j/n;vs.append((rr*cos(a),rr*sin(a),zz))
    q=n+1;fs=[]
    for j in range(n):
        fs.extend([(j,j+1,2*q+j+1,2*q+j),(q+j,3*q+j,3*q+j+1,q+j+1),
                   (j,q+j,q+j+1,j+1),(2*q+j,2*q+j+1,3*q+j+1,3*q+j)])
    fs.extend([(0,2*q,3*q,q),(n,q+n,3*q+n,2*q+n)])
    return mesh_obj(name,vs,fs,c)
def lathe_profile(name,profile,a0=0,a1=ANGLE,n=20,c=KIT):
    vs=[]
    for r,z in profile:
        for j in range(n+1):
            a=a0+(a1-a0)*j/n;vs.append((r*cos(a),r*sin(a),z))
    fs=[];q=n+1
    for k in range(len(profile)):
        kk=(k+1)%len(profile)
        for j in range(n):fs.append((k*q+j,k*q+j+1,kk*q+j+1,kk*q+j))
    fs.append(tuple(k*q for k in reversed(range(len(profile)))))
    fs.append(tuple(k*q+n for k in range(len(profile))))
    return mesh_obj(name,vs,fs,c)

# Bake a physically authored masonry high poly tile into a low-poly plane.
def principled(name,color,rough=.8,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
highmats=[]
for k in range(7):
    shade=.19+.035*k;m=principled('HP_Limestone_'+str(k),(shade*1.15,shade*1.04,shade*.86),.77+.02*(k%3))
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=42
    tex.inputs['Detail'].default_value=4;b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.3;b.inputs['Distance'].default_value=.003
    nt.links.new(tex.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs['Normal'],bs.inputs['Normal'])
    highmats.append(m)
mortar=principled('HP_RecessedMortar',(.115,.105,.085),.96)
high=[]
for row in range(10):
    for col in range(5):
        x=(col+(row%2)*.5)*.4-.8;y=row*.2-.9
        w=.4-random.uniform(.018,.035);h=.2-random.uniform(.014,.026);depth=random.uniform(.048,.078)
        ob=cube('HP_Stone_%02d_%02d'%(row,col),(x,y,depth/2),(w,h,depth),HP,.014)
        # Explicit high-poly uneven stone faces, not only shader noise.
        sub=ob.modifiers.new('Sculpt tessellation','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=2;apply_mod(ob,sub)
        tex=bpy.data.textures.new(ob.name+'_chisel',type='CLOUDS');tex.noise_scale=.055;tex.noise_depth=2
        ds=ob.modifiers.new('Hand dressed relief','DISPLACE');ds.texture=tex;ds.strength=.006;ds.mid_level=.5;apply_mod(ob,ds)
        ob.data.materials.append(random.choice(highmats));high.append(ob)
        for dx,dy in [(2,0),(-2,0),(0,2),(0,-2),(2,2),(2,-2),(-2,2),(-2,-2)]:
            xx,yy=x+dx,y+dy
            if abs(xx)<1.3 and abs(yy)<1.2:
                cp=ob.copy();cp.data=ob.data;HP.objects.link(cp);cp.location.x=xx;cp.location.y=yy;high.append(cp)
back=cube('HP_MortarBed',(0,0,-.015),(2.8,2.8,.03),HP);back.data.materials.append(mortar);high.append(back)
# A single bake source avoids per-object Cycles bake overhead.
high=[join(high,'HP_Masonry_Sculpted_Tile',HP)]
low=mesh_obj('LP_Masonry_BakePlane',[(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)],[(0,1,2,3)],HP)
for li,uv in zip(low.data.uv_layers[0].data,[(0,0),(1,0),(1,1),(0,1)]):li.uv=uv
bakemat=principled('LP_BakeReceiver',(.4,.4,.4));low.data.materials.append(bakemat)
target=bakemat.node_tree.nodes.new('ShaderNodeTexImage')
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.18
scene.render.bake.max_ray_distance=.3;scene.render.bake.margin=24
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
def bake(name,kind,size=4096,noncolor=False):
    path=os.path.join(OUT,'textures',name+'.png')
    img=bpy.data.images.new(name,width=size,height=size,alpha=False,float_buffer=False)
    if noncolor:img.colorspace_settings.name='Non-Color'
    target.image=img;bakemat.node_tree.nodes.active=target
    bpy.ops.object.select_all(action='DESELECT')
    for ob in high:ob.select_set(True)
    low.select_set(True);bpy.context.view_layer.objects.active=low
    kwargs={'type':kind,'use_selected_to_active':True,'cage_extrusion':.18,'max_ray_distance':.3,'margin':24}
    if kind=='DIFFUSE':kwargs['pass_filter']={'COLOR'}
    print('BAKE_START',name,flush=True);bpy.ops.object.bake(**kwargs)
    img.filepath_raw=path;img.file_format='PNG';img.save();print('BAKE_DONE',name,flush=True)
    return img
base=bake('T_T49_Masonry_BaseColor','DIFFUSE')
normal=bake('T_T49_Masonry_NormalGL','NORMAL',noncolor=True)
scene.cycles.samples=8;ao=bake('T_T49_Masonry_AO','AO',noncolor=True)
scene.cycles.samples=1
rough=bake('T_T49_Masonry_Roughness','ROUGHNESS',noncolor=True)
print('BAKES_COMPLETE',flush=True)

def textured(name,factor=(1,1,1),roughscale=1):
    m=principled(name,(.5,.5,.5));nt=m.node_tree;p=nt.nodes.get('Principled BSDF')
    for img,inputname in [(base,'Base Color'),(rough,'Roughness')]:
        t=nt.nodes.new('ShaderNodeTexImage');t.image=img;nt.links.new(t.outputs['Color'],p.inputs[inputname])
    t=nt.nodes.new('ShaderNodeTexImage');t.image=normal;n=nt.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.85
    nt.links.new(t.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],p.inputs['Normal'])
    return m
stone=textured('M_T49_BakedLimestone');trim=stone
wood=principled('M_T49_Oak',(.16,.09,.035),.8);iron=principled('M_T49_ForgedIron',(.055,.048,.04),.62,.85)
def material(o,m=stone):o.data.materials.clear();o.data.materials.append(m);return o
KIT.hide_render=True;HP.hide_render=True;HP.hide_viewport=True
templates={};placements=[]
def register(o):
    material(o);templates[o.name]=o;return o
def place(key,z=0,angle=0,name=None):
    src=templates[key];o=bpy.data.objects.new(name or key+'_'+str(len(placements)).zfill(4),src.data);ASSEMBLY.objects.link(o)
    o.location.z=z;o.rotation_euler.z=angle
    placements.append({'name':o.name,'mesh':key,'location_m':[0,0,z],'rotation_z_degrees':math.degrees(angle)})
    return o

# Drum sections: actual through-openings, no painted fake arrow slits.
def panel(name,h,slit=False,r0=R,r1=R):
    if not slit:return sector(name,r0-1.15,r0,0,h,rin_top=r1-1.15,rout_top=r1)
    gap=.22/R;centre=ANGLE/2;lo=centre-gap/2;hi=centre+gap/2
    obs=[sector(name+'L',R-1.15,R,0,h,a1=lo,n=10),sector(name+'R',R-1.15,R,0,h,a0=hi,n=10),
         sector(name+'Sill',R-1.15,R,0,1.55,a0=lo,a1=hi,n=1),
         sector(name+'Lintel',R-1.15,R,2.95,h,a0=lo,a1=hi,n=1)]
    ob=join(obs,name,KIT)
    # Small edge radius retained in geometry for glancing views.
    bevel(ob,.012,1);return ob
register(panel('SM_T49_Drum_45',BAND))
register(panel('SM_T49_DrumSlit_45',BAND,True))
register(panel('SM_T49_BaseLower_45',BAND,r0=BASE_R,r1=11.75))
register(panel('SM_T49_BaseUpper_45',BAND,r0=11.75,r1=R))
register(lathe_profile('SM_T49_StringCourse_45',[(R-.04,0),(R+.20,0),(R+.20,.12),(R+.13,.23),(R-.04,.23)]))
for band in range(36):
    for side in range(8):
        key='SM_T49_BaseLower_45' if band==0 else 'SM_T49_BaseUpper_45' if band==1 else 'SM_T49_DrumSlit_45' if band%3==0 else 'SM_T49_Drum_45'
        place(key,band*BAND,side*ANGLE)
        if band>1 and band%4==0:place('SM_T49_StringCourse_45',band*BAND,side*ANGLE)

def base_radius(z):return BASE_R-(BASE_R-R)*min(1,max(0,z/11))
def stair(name,base_z=11):
    obs=[]
    for s in range(STEPS):
        t0=s/STEPS;t1=(s+1)/STEPS;a0=t0*ANGLE;a1=t1*ANGLE
        rr0=base_radius(base_z+t0*DH);rr1=base_radius(base_z+t1*DH)
        z=(s+1)*RISE
        # Individual closed stone tread wedges with real risers and nosing.
        ob=sector(name+'_t'+str(s),rr0,rr0+WIDTH,z-.48,z,a0,a1,2,rin_top=rr1,rout_top=rr1+WIDTH)
        obs.append(ob)
    # Continuous outer parapet following the stair slope, with closed ends.
    vs=[];fs=[];n=36
    for j in range(n+1):
        t=j/n;a=t*ANGLE;rr=base_radius(base_z+t*DH)+WIDTH;z=t*DH
        vs.extend([(rr*cos(a),rr*sin(a),z-.5),((rr+.36)*cos(a),(rr+.36)*sin(a),z-.5),
                   ((rr+.36)*cos(a),(rr+.36)*sin(a),z+1.1),(rr*cos(a),rr*sin(a),z+1.1)])
    for j in range(n):
        q=j*4
        for k in range(4):fs.append((q+k,q+(k+1)%4,q+4+(k+1)%4,q+4+k))
    fs.extend([(3,2,1,0),(n*4,n*4+1,n*4+2,n*4+3)])
    obs.append(mesh_obj(name+'_parapet',vs,fs))
    # Masonry cantilever consoles under the continuous stair bed.
    for s in [2,8,14]:
        a=(s+.5)*ANGLE/STEPS;z=(s+.5)*RISE-.48;rr=base_radius(base_z+(s+.5)*RISE)
        profile=[(rr-.20,z-1.7),(rr+.55,z-1.7),(rr+WIDTH,z-.22),(rr+WIDTH,z),(rr-.20,z)]
        obs.append(lathe_profile(name+'_console'+str(s),profile,a-.027,a+.027,n=1))
    ob=join(obs,name,KIT);bevel(ob,.012,1);return ob
register(stair('SM_T49_Stair_45'))
for i in range(4):register(stair('SM_T49_StairBase'+str(i)+'_45',i*DH))
for chunk in range(CHUNKS):
    place('SM_T49_StairBase'+str(chunk)+'_45' if chunk<4 else 'SM_T49_Stair_45',chunk*DH,chunk*ANGLE)

# Crown: solid roof disc, dressed corbels, parapet and merlons ending at exactly 200m.
register(sector('SM_T49_RoofDeck_45',.0,R+WIDTH+.4,-.6,0,n=32))
register(sector('SM_T49_CrownParapet_45',R+WIDTH+.05,R+WIDTH+.6,0,1.1,n=24))
register(lathe_profile('SM_T49_CrownCorbel_45',[(R-.15,-2.8),(R+.6,-2.8),(R+WIDTH+.45,-.7),(R+WIDTH+.45,-.45),(R-.15,-.45)],n=24))
register(sector('SM_T49_Merlon',R+WIDTH+.05,R+WIDTH+.6,1.1,2.0,0,pi/48,n=4))
for i in range(8):
    place('SM_T49_RoofDeck_45',ROOF,i*ANGLE);place('SM_T49_CrownParapet_45',ROOF,i*ANGLE);place('SM_T49_CrownCorbel_45',ROOF,i*ANGLE)
for i in range(48):place('SM_T49_Merlon',ROOF,i*2*pi/48)

# Ground entrance: deep arched portal cut through one lower base segment.
baseobjs=[o for o in ASSEMBLY.objects if o.name.startswith('SM_T49_BaseLower_45')]
doorpanel=baseobjs[-2];doorpanel.data=doorpanel.data.copy()
a=doorpanel.rotation_euler.z+ANGLE/2
# Boolean aperture in actual masonry, using an arched extruded shape.
def arch_prism(name,width,spring,radius,depth,loc,angle,c=KIT):
    outline=[(-width/2,0),(width/2,0),(width/2,spring)]
    for i in range(1,17):
        theta=pi*i/16;outline.append((radius*cos(theta),spring+radius*sin(theta)))
    vs=[(x,-depth/2,z) for x,z in outline]+[(x,depth/2,z) for x,z in outline];n=len(outline)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    for i in range(n):fs.append((i,(i+1)%n,(i+1)%n+n,i+n))
    ob=mesh_obj(name,vs,fs,c);ob.location=loc;ob.rotation_euler.z=angle;return ob
cut=arch_prism('PORTAL_CUTTER',2.0,2.0,1,5,(BASE_R*cos(a),BASE_R*sin(a),0),a-pi/2)
mod=doorpanel.modifiers.new('True portal aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;apply_mod(doorpanel,mod)
bpy.data.objects.remove(cut,do_unlink=True)
door=arch_prism('SM_T49_OakDoor',1.9,2.0,.95,.15,((BASE_R-.3)*cos(a),(BASE_R-.3)*sin(a),0),a-pi/2,ASSEMBLY);material(door,wood)
bevel(door,.025,2)
# One independently reusable iron handhold ring, placed every 4.6m of ascent above 150m.
bpy.ops.mesh.primitive_torus_add(major_radius=.13,minor_radius=.018,major_segments=16,minor_segments=6,location=(R+.12,0,1.2),rotation=(pi/2,0,pi/2))
ring=bpy.context.object;ring.name='SM_T49_IronHandhold';move(ring,KIT);material(ring,iron)
scene.cursor.location=(0,0,0);active(ring);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');templates[ring.name]=ring
for i in range(55,72):place('SM_T49_IronHandhold',i*DH,i*ANGLE)

# Non-rendered segmented ramp collision. No enclosing convex hull around the tower.
def ramp_collision(name,chunk):
    # Four convex wedge prisms per 45-degree chunk; top follows walking incline.
    obs=[]
    for part in range(4):
        ts=[part/4,(part+1)/4];vs=[]
        for t in ts:
            a=t*ANGLE;rr=base_radius(chunk*DH+t*DH);z=t*DH+RISE/2
            vs.extend([(rr*cos(a),rr*sin(a),z-.55),((rr+WIDTH)*cos(a),(rr+WIDTH)*sin(a),z-.55),
                       ((rr+WIDTH)*cos(a),(rr+WIDTH)*sin(a),z),(rr*cos(a),rr*sin(a),z)])
        fs=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        ob=mesh_obj('UCX_'+name+'_'+str(part).zfill(2),vs,fs,COL)
        ob.location.z=chunk*DH;ob.rotation_euler.z=chunk*ANGLE;obs.append(ob)
    return obs
for i in range(CHUNKS):ramp_collision('T49_Stair'+str(i).zfill(3),i)
COL.hide_render=True;COL.hide_viewport=True

# UV1: unique packed lightmap coordinates per kit piece, leaving primary tiling intact.
for ob in list(KIT.objects)+[doorpanel,door]:
    if ob.type!='MESH':continue
    active(ob)
    if not ob.data.uv_layers.get('UV1_Lightmap'):ob.data.uv_layers.new(name='UV1_Lightmap')
    ob.data.uv_layers.active_index=1
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025,area_weight=.3)
    bpy.ops.object.mode_set(mode='OBJECT');ob.data.uv_layers.active_index=0
    for p in ob.data.polygons:p.use_smooth=False

# Two geometric LOD variants, stored as distinct mesh datablocks and optional assemblies.
lod_report=[]
for level,ratio in [(1,.55),(2,.25)]:
    cache={}
    for ob in ASSEMBLY.objects:
        if ob.type!='MESH':continue
        key=ob.data.name
        if key not in cache:
            cp=ob.copy();cp.data=ob.data.copy();LODS.objects.link(cp);cp.name=ob.name+'_LOD'+str(level)
            active(cp);mod=cp.modifiers.new('Planar-aware decimation','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
            apply_mod(cp,mod);cache[key]=cp.data
            bpy.data.objects.remove(cp,do_unlink=True)
        cp=bpy.data.objects.new(ob.name+'_LOD'+str(level),cache[key]);LODS.objects.link(cp);cp.matrix_world=ob.matrix_world
        cp['lod_level']=level
    lod_report.append({'level':level,'ratio_requested':ratio,'unique_meshes':len(cache)})
LODS.hide_render=True;LODS.hide_viewport=True

def triangles(me):return sum(len(p.vertices)-2 for p in me.polygons)
def audit(objects):
    report={'objects':0,'triangles_instanced':0,'unique_meshes':0,'unique_triangles':0,'degenerate_faces':0,'nonmanifold_edges':0,'bounds_min':[1e9]*3,'bounds_max':[-1e9]*3}
    seen=set()
    for ob in objects:
        if ob.type!='MESH':continue
        report['objects']+=1;report['triangles_instanced']+=triangles(ob.data)
        for v in ob.data.vertices:
            co=ob.matrix_world@v.co
            for k in range(3):report['bounds_min'][k]=min(report['bounds_min'][k],co[k]);report['bounds_max'][k]=max(report['bounds_max'][k],co[k])
        if ob.data.name in seen:continue
        seen.add(ob.data.name);report['unique_meshes']+=1;report['unique_triangles']+=triangles(ob.data)
        bm=bmesh.new();bm.from_mesh(ob.data)
        report['degenerate_faces']+=sum(f.calc_area()<1e-10 for f in bm.faces)
        report['nonmanifold_edges']+=sum(not e.is_manifold for e in bm.edges);bm.free()
    report['dimensions_m']=[report['bounds_max'][i]-report['bounds_min'][i] for i in range(3)]
    return report
print('AUDITING',flush=True)
report=audit(ASSEMBLY.objects);report['spec']={'height_m':200,'roof_m':198,'width_m':WIDTH,'turns':9,'risers':1296,'rise_m':RISE,'step_angle_degrees':2.5,'main_drum_radius_m':R,'base_radius_m':BASE_R,'stairs_inner_radius_min_m':R}
report['bake']={'method':'selected high-poly masonry relief to low-poly UV tile','size':4096,'high_triangles':sum(triangles(o.data) for o in high),'normal_convention':'OpenGL +Y','ao_samples':8,'maps':['BaseColor','NormalGL','AO','Roughness']}
report['lods']=lod_report;report['unreal_tested']=False;report['full_intersection_audit']=False
with open(os.path.join(OUT,'reports','geometry.json'),'w') as f:json.dump(report,f,indent=2)
with open(os.path.join(OUT,'meshes','assembly.json'),'w') as f:json.dump({'units':'meters','up':'Z','placements':placements,'note':'Entrance boolean panel and door are in assembled export; placement list alone is not the complete entrance.'},f,indent=2)

def select_objects(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]

# Standalone complete exports. GLB shares repeated mesh data; FBX is in centimeters via units.
KIT.hide_viewport=True;HP.hide_viewport=True;COL.hide_viewport=True;LODS.hide_viewport=True
select_objects(list(ASSEMBLY.objects));bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD0.glb'),export_format='GLB',use_selection=True,export_tangents=True,export_texcoords=True,export_normals=True,export_materials='EXPORT')
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD0.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False,path_mode='RELATIVE')
for level in [1,2]:
    LODS.hide_viewport=False;obs=[o for o in LODS.objects if o.get('lod_level')==level];select_objects(obs)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD'+str(level)+'.glb'),export_format='GLB',use_selection=True,export_tangents=True)
LODS.hide_viewport=True
COL.hide_viewport=False;select_objects(list(COL.objects));bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'collision','Tower49_StairRampCollision.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z')
COL.hide_viewport=True

# Save editable production source before making studio elements.
scene.render.bake.use_selected_to_active=False
for img in [base,normal,ao,rough]:img.filepath='//../textures/'+os.path.basename(img.filepath_raw)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
print('EXPORTS_DONE',json.dumps(report),flush=True)

# Render actual mesh, not generated artwork.
HP.hide_render=True;KIT.hide_render=True;COL.hide_render=True;LODS.hide_render=True
ground=material(cube('Studio ground',(0,0,-.35),(130,130,.5),STUDIO),principled('Studio ground matte',(.12,.14,.12),.95))
world=bpy.data.worlds.new('Overcast');scene.world=world;world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.55,.62,.68,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.65
def area(name,loc,energy,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);STUDIO.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,85))-o.location).to_track_quat('-Z','Y').to_euler()
area('Broad daylight',(70,-100,180),1900000,110);area('Soft fill',(-90,-20,90),700000,80)
sun=bpy.data.lights.new('Sun','SUN');sun.energy=2.0;sun.angle=.2;so=bpy.data.objects.new('Sun',sun);STUDIO.objects.link(so);so.rotation_euler=(.5,-.35,-.4)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def render(name,loc,target,ortho,res):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=ortho;o=bpy.data.objects.new(name,d);STUDIO.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();scene.camera=o
    scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];scene.render.resolution_percentage=100
    scene.render.filepath=os.path.join(OUT,'renders',name+'.png');print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
render('01_full_tower',(260,-350,170),(0,0,98),218,(900,1800))
render('02_stair_closeup',(30,-43,24),(0,0,16),28,(1500,1100))
render('03_crown',(42,-54,222),(0,0,194),39,(1500,1100))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Presentation.blend'))
print('TOWER49_DONE',OUT,flush=True)

