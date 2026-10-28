"""Finalize authored tower: textured fittings, engine kit and collision exports."""
import bpy,bmesh,math,os,json,hashlib
import numpy as np
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'outputs','Tower49_Medieval_200m_v1')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
scene=bpy.context.scene
for stem in ['T_T49_Masonry_BaseColor','T_T49_Masonry_NormalGL','T_T49_Masonry_AO','T_T49_Masonry_Roughness']:
    if bpy.data.images.get(stem) is None:
        image=bpy.data.images.load(os.path.join(OUT,'textures',stem+'.png'),check_existing=False);image.name=stem
        if 'BaseColor' not in stem:image.colorspace_settings.name='Non-Color'
for image in list(bpy.data.images):
    candidate=os.path.join(OUT,'textures',os.path.basename(image.filepath))
    if os.path.isfile(candidate):
        image.filepath=candidate;image.source='FILE';image.reload()
ASSEMBLY=bpy.data.collections['01_LOD0_ASSEMBLY'];KIT=bpy.data.collections['02_MODULAR_KIT'];COL=bpy.data.collections['04_COLLISION_UCX']
ring=bpy.data.objects.get('SM_T49_IronHandhold')
if ring is not None:
    ring.data.transform(ring.rotation_euler.to_matrix().to_4x4());ring.rotation_euler=(0,0,0)
    for ob in list(ASSEMBLY.objects):
        if ob.name.startswith('SM_T49_IronHandhold'):bpy.data.objects.remove(ob,do_unlink=True)
    for step in range(985,1296,5):
        ob=bpy.data.objects.new('SM_T49_Handhold_'+str(step),ring.data);ASSEMBLY.objects.link(ob)
        ob.location.z=step*198/1296;ob.rotation_euler.z=step*math.pi/72
for folder in ['meshes/kit','source','reports','collision','textures']:
    os.makedirs(os.path.join(OUT,folder),exist_ok=True)
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def select(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
def save_image(name,values,color=False):
    h,w=values.shape[:2];image=bpy.data.images.new(name,width=w,height=h,alpha=False)
    if not color:image.colorspace_settings.name='Non-Color'
    rgba=np.ones((h,w,4),dtype=np.float32);rgba[:,:,:3]=values if values.ndim==3 else values[:,:,None]
    image.pixels.foreach_set(rgba.ravel());image.filepath_raw=os.path.join(OUT,'textures',name+'.png');image.file_format='PNG';image.save();return image
def image_pixels(image):
    a=np.empty(image.size[0]*image.size[1]*4,dtype=np.float32);image.pixels.foreach_get(a);return a.reshape(image.size[1],image.size[0],4)
def pbr_procedural(name,kind,size=2048):
    # Original periodic material authoring for small fittings. Stone has separate HP bakes.
    y,x=np.mgrid[0:size,0:size].astype(np.float32)/size
    if kind=='wood':
        grain=np.sin(x*2*math.pi*53+1.5*np.sin(y*2*math.pi*3)+.4*np.sin(y*2*math.pi*17))
        pores=np.sin(x*2*math.pi*257+y*2*math.pi*29)*.12
        board=(np.cos(x*2*math.pi*8)>.98).astype(np.float32)
        height=.5+.12*grain+.05*pores-.12*board
        shade=.82+.12*grain-.2*board
        col=shade[:,:,None]*np.array([.22,.115,.047],dtype=np.float32)
        rough=np.clip(.79+.08*grain,.5,.95);metal=np.zeros_like(rough)
    else:
        pits=np.sin(x*2*math.pi*137)*np.sin(y*2*math.pi*113)
        hammer=np.sin(x*2*math.pi*13+.4*np.sin(y*2*math.pi*5))*np.sin(y*2*math.pi*17)
        height=.5+.08*pits+.08*hammer
        shade=.85+.15*hammer
        col=shade[:,:,None]*np.array([.075,.067,.056],dtype=np.float32)
        rough=np.clip(.62+.12*pits,.35,.85);metal=np.ones_like(rough)*.85
    dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*5
    dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*5
    normals=np.stack((-dx,-dy,np.ones_like(dx)),axis=-1);normals/=np.linalg.norm(normals,axis=-1,keepdims=True)
    base=save_image('T_T49_'+kind+'_BaseColor',col,True);normal=save_image('T_T49_'+kind+'_NormalGL',normals*.5+.5)
    orm=save_image('T_T49_'+kind+'_ORM',np.stack((np.ones_like(rough),rough,metal),axis=-1))
    m=bpy.data.materials[name];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    for node in list(nt.nodes):
        if node not in [bs,nt.nodes.get('Material Output')]:nt.nodes.remove(node)
    t=nt.nodes.new('ShaderNodeTexImage');t.image=base;nt.links.new(t.outputs['Color'],bs.inputs['Base Color'])
    t=nt.nodes.new('ShaderNodeTexImage');t.image=normal;n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(t.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal'])
    t=nt.nodes.new('ShaderNodeTexImage');t.image=orm;sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(t.outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    return m
pbr_procedural('M_T49_Oak','wood');pbr_procedural('M_T49_ForgedIron','iron')
# Pack verified masonry AO and roughness, retaining raw bake files as well.
ao=bpy.data.images.get('T_T49_Masonry_AO');rough=bpy.data.images.get('T_T49_Masonry_Roughness')
for image in bpy.data.images:
    if image.source=='FILE':
        path=os.path.join(OUT,'textures',os.path.basename(image.filepath));image.filepath=path
        if os.path.isfile(path):image.reload()
# Add authored mineral/mottling detail to the geometric color bake. Preserve raw bakes.
base=bpy.data.images.get('T_T49_Masonry_BaseColor')
raw=image_pixels(base)[:,:,:3].copy()
save_image('T_T49_Masonry_BaseColor_BakeRaw',raw,True)
sz=2048;y,x=np.mgrid[0:sz,0:sz].astype(np.float32)/sz
mottle=np.zeros((sz,sz),dtype=np.float32)
for freq,amp in [(2,.18),(5,.12),(13,.08),(37,.045),(97,.025),(251,.018)]:
    mottle+=amp*np.sin(2*math.pi*(x*freq+y*(freq+1))+.8*np.sin(2*math.pi*y*3))*np.cos(2*math.pi*(y*freq-x*(freq+2)))
mottle=np.repeat(np.repeat(mottle,2,axis=0),2,axis=1)
col=np.clip(raw*(1+mottle[:,:,None]),0,1)
base.pixels.foreach_set(np.concatenate((col,np.ones((*col.shape[:2],1),dtype=np.float32)),axis=2).ravel());base.filepath_raw=os.path.join(OUT,'textures','T_T49_Masonry_BaseColor.png');base.save()
rp0=image_pixels(rough);rp0[:,:,:3]=np.clip(rp0[:,:,:3]+mottle[:,:,None]*.22,.45,.99);rough.pixels.foreach_set(rp0.ravel());rough.save()
ap=image_pixels(ao)[:,:,0];rp=image_pixels(rough)[:,:,0]
orm=save_image('T_T49_Masonry_ORM',np.stack((ap,rp,np.zeros_like(ap)),axis=-1))
m=bpy.data.materials['M_T49_BakedLimestone'];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
t=nt.nodes.new('ShaderNodeTexImage');t.image=orm;sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(t.outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree');group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat');gn=nt.nodes.new('ShaderNodeGroup');gn.node_tree=group;nt.links.new(sep.outputs['Red'],gn.inputs['Occlusion'])
# NormalGL for Blender/glTF and a convention-correct DirectX normal for Unreal.
normal=bpy.data.images.get('T_T49_Masonry_NormalGL');px=image_pixels(normal)[:,:,:3];px[:,:,1]=1-px[:,:,1];save_image('T_T49_Masonry_NormalDX',px)
# Correct cylindrical wrap at the atan2 branch cut without changing tiling density.
seen=set()
for ob in list(ASSEMBLY.objects)+list(KIT.objects)+list(bpy.data.collections['06_LOD1_2_ASSEMBLIES'].objects):
    if ob.type!='MESH' or ob.data.name in seen:continue
    seen.add(ob.data.name);uv=ob.data.uv_layers[0]
    for p in ob.data.polygons:
        if abs(p.normal.z)>.65:continue
        values=[uv.data[i].uv.x for i in p.loop_indices]
        if max(values)-min(values)>10:
            for i in p.loop_indices:
                if uv.data[i].uv.x<0:uv.data[i].uv.x+=math.pi*10.5
# The entrance is its own modular variation, preserving its boolean aperture.
entrance=next(o for o in ASSEMBLY.objects if o.name.startswith('SM_T49_BaseLower_45') and o.data.users==1)
e=entrance.copy();e.data=entrance.data.copy();KIT.objects.link(e);e.name='SM_T49_BaseEntrance_45';e.location=(0,0,0);e.rotation_euler=(0,0,0);e.scale=(1,1,1)
entrance['module']='SM_T49_BaseEntrance_45'
# A ground floor closes the hollow drum at the datum.
deck=bpy.data.objects['SM_T49_RoofDeck_45']
floor=deck.copy();floor.data=deck.data.copy();KIT.objects.link(floor);floor.name='SM_T49_GroundFloor_45'
from mathutils import Matrix
floor.data.transform(Matrix.Diagonal((11.9/13.9,11.9/13.9,1,1)))
for j in range(8):
    ob=bpy.data.objects.new('SM_T49_GroundFloor_'+str(j),floor.data);ASSEMBLY.objects.link(ob);ob.rotation_euler.z=j*math.pi/4
# Keep newly corrected handholds/floor consistent in both LOD assemblies.
lod_collection=bpy.data.collections['06_LOD1_2_ASSEMBLIES']
for ob in list(lod_collection.objects):
    if 'IronHandhold' in ob.name:bpy.data.objects.remove(ob,do_unlink=True)
for level in [1,2]:
    for ob in ASSEMBLY.objects:
        if ob.name.startswith(('SM_T49_Handhold_','SM_T49_GroundFloor_')):
            cp=ob.copy();lod_collection.objects.link(cp);cp.name=ob.name+'_LOD'+str(level);cp['lod_level']=level
# Fix door mapping and triangulate exports explicitly for stable tangent bases.
done=set()
for ob in list(ASSEMBLY.objects)+list(KIT.objects)+list(lod_collection.objects):
    if ob.type!='MESH' or ob.data.name in done:continue
    done.add(ob.data.name)
    if 'OakDoor' in ob.name:
        uv=ob.data.uv_layers[0]
        for li in uv.data:
            pass
        for p in ob.data.polygons:
            for idx in p.loop_indices:
                co=ob.data.vertices[ob.data.loops[idx].vertex_index].co
                uv.data[idx].uv=(co.x/2+.5,co.z/3)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bm.to_mesh(ob.data);bm.free()

def hull(name,coords):
    bm=bmesh.new();vs=[bm.verts.new(v) for v in coords];result=bmesh.ops.convex_hull(bm,input=vs,use_existing_faces=False)
    if result.get('geom_interior'):bmesh.ops.delete(bm,geom=result['geom_interior'],context='VERTS')
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();ob=bpy.data.objects.new(name,me);COL.objects.link(ob);return ob
def obbbox(o):
    vs=[v.co for v in o.data.vertices];return [min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]
def collide_for(ob):
    name=ob.name;obs=[]
    if 'Stair' in name:
        base_index=int(name.split('StairBase')[1][0]) if 'StairBase' in name else 4
        basez=base_index*2.75
        for j in range(8):
            ts=[j/8,(j+1)/8];coords=[];wall=[]
            for t in ts:
                a=t*math.pi/4;r=13-2.5*min(1,(basez+t*2.75)/11);z=t*2.75+.1527777778/2
                for zz in [z-.5,z]:
                    for rr in [r,r+3]:coords.append((rr*math.cos(a),rr*math.sin(a),zz))
                for zz in [z-.5,z+1.1]:
                    for rr in [r+3,r+3.36]:wall.append((rr*math.cos(a),rr*math.sin(a),zz))
            obs.append(hull('UCX_'+name+'_'+str(j).zfill(2),coords));obs.append(hull('UCX_'+name+'_'+str(j+8).zfill(2),wall))
    elif 'Drum' in name or 'Base' in name or 'CrownParapet' in name:
        # Curved strips: preserve the exterior circulation and hollow interior.
        lo,hi=obbbox(ob);z0,z1=lo[2],hi[2]
        if 'BaseLower' in name or 'BaseEntrance' in name:r0,r1=13,11.75
        elif 'BaseUpper' in name:r0,r1=11.75,10.5
        elif 'CrownParapet' in name:r0,r1=14.1,14.1
        else:r0,r1=10.5,10.5
        thick=.55 if 'CrownParapet' in name else 1.15
        for j in range(8):
            coords=[]
            for zz,rr in [(z0,r0),(z1,r1)]:
                for a in [j*math.pi/32,(j+1)*math.pi/32]:
                    for r in [rr-thick,rr]:coords.append((r*math.cos(a),r*math.sin(a),zz))
            # Skip portal span, add sill/header explicitly only if needed after engine review.
            if 'Entrance' in name and j in [3,4]:continue
            obs.append(hull('UCX_'+name+'_'+str(j).zfill(2),coords))
    elif 'RoofDeck' in name or 'GroundFloor' in name:
        radius=11.9 if 'GroundFloor' in name else 13.9
        for j in range(8):
            coords=[(0,0,z) for z in [-.6,0]]
            for z in [-.6,0]:
                for a in [j*math.pi/32,(j+1)*math.pi/32]:coords.append((radius*math.cos(a),radius*math.sin(a),z))
            obs.append(hull('UCX_'+name+'_'+str(j).zfill(2),coords))
    return obs

KIT.hide_viewport=False;COL.hide_viewport=False
kit_report=[]
for ob in list(KIT.objects):
    if ob.type!='MESH':continue
    # Export a real engine module with matching local-space UCX names.
    ob.location=(0,0,0);ob.rotation_euler=(0,0,0);ob.scale=(1,1,1)
    cs=collide_for(ob);select([ob]+cs)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'meshes','kit',ob.name+'.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False)
    kit_report.append({'mesh':ob.name,'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),'ucx_hulls':len(cs),'uv_layers':len(ob.data.uv_layers)})
KIT.hide_viewport=True;COL.hide_viewport=True
manifest=[]
for ob in ASSEMBLY.objects:
    if ob.type!='MESH':continue
    key=ob.get('module') or next((k.name for k in KIT.objects if k.type=='MESH' and k.data==ob.data),None)
    manifest.append({'name':ob.name,'module':key,'location_m':list(ob.location),'rotation_xyz_degrees':[math.degrees(a) for a in ob.rotation_euler],'scale':list(ob.scale)})
with open(os.path.join(OUT,'reports','kit.json'),'w') as f:json.dump(kit_report,f,indent=2)
with open(os.path.join(OUT,'meshes','assembly.json'),'w') as f:json.dump({'units':'meters','source_axes':'Blender Z up; glTF uses standard Y-up conversion','height_m':200,'roof_m':198,'placements':manifest,'note':'Door transform is preserved in complete assembled FBX/GLB. Separate engine module placement must be import-tested.'},f,indent=2)
select(list(ASSEMBLY.objects))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD0.glb'),export_format='GLB',use_selection=True,export_tangents=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD0.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False)
LODS=bpy.data.collections['06_LOD1_2_ASSEMBLIES'];LODS.hide_viewport=False
for level in [1,2]:
    select([o for o in LODS.objects if o.get('lod_level')==level]);bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD'+str(level)+'.glb'),export_format='GLB',use_selection=True,export_tangents=True)
LODS.hide_viewport=True
for image in bpy.data.images:
    candidate=os.path.join(OUT,'textures',os.path.basename(image.filepath))
    if os.path.isfile(candidate):
        image.pack();image.filepath='//../textures/'+os.path.basename(candidate)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
print('FINALIZED_KIT',len(kit_report),flush=True)

