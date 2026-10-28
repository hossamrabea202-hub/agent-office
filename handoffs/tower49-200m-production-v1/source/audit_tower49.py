import bpy,bmesh,os,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'outputs','Tower49_Medieval_200m_v1')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
assembly=bpy.data.collections['01_LOD0_ASSEMBLY'];lods=bpy.data.collections['06_LOD1_2_ASSEMBLIES']
lods.hide_viewport=False;bpy.context.view_layer.update()
def audit(obs):
    seen=set();result={'objects':0,'triangles_instanced':0,'unique_meshes':0,'unique_triangles':0,'degenerate_faces':0,'nonmanifold_edges':0,'missing_uv0':0,'missing_uv1':0,'min':[1e9]*3,'max':[-1e9]*3}
    for ob in obs:
        if ob.type!='MESH':continue
        result['objects']+=1;result['triangles_instanced']+=sum(len(p.vertices)-2 for p in ob.data.polygons)
        for v in ob.data.vertices:
            co=ob.matrix_world@v.co
            for k in range(3):result['min'][k]=min(result['min'][k],co[k]);result['max'][k]=max(result['max'][k],co[k])
        if ob.data.name in seen:continue
        seen.add(ob.data.name);result['unique_meshes']+=1;result['unique_triangles']+=sum(len(p.vertices)-2 for p in ob.data.polygons)
        result['missing_uv0']+=len(ob.data.uv_layers)<1;result['missing_uv1']+=len(ob.data.uv_layers)<2
        bm=bmesh.new();bm.from_mesh(ob.data);result['degenerate_faces']+=sum(f.calc_area()<1e-10 for f in bm.faces);result['nonmanifold_edges']+=sum(not e.is_manifold for e in bm.edges);bm.free()
    return result
report={'lod0':audit(assembly.objects),'lod1':audit([o for o in lods.objects if o.get('lod_level')==1]),'lod2':audit([o for o in lods.objects if o.get('lod_level')==2])}
verts=[];faces=[]
for ob in assembly.objects:
    if not ob.name.startswith('SM_T49_Stair'):continue
    offset=len(verts);verts.extend([ob.matrix_world@v.co for v in ob.data.vertices]);faces.extend([tuple(offset+i for i in p.vertices) for p in ob.data.polygons])
tree=BVHTree.FromPolygons(verts,faces,all_triangles=False)
misses=[];deltas=[]
for step in range(1296):
    t=(step+.5)/1296;angle=t*18*math.pi;z=t*198;r=13-2.5*min(1,z/11)
    for width in [.2,1.5,2.8]:
        rr=r+width;expected=(step+1)*198/1296
        origin=Vector((rr*math.cos(angle),rr*math.sin(angle),expected+.4))
        loc,norm,face,dist=tree.ray_cast(origin,Vector((0,0,-1)),1)
        if loc is None:misses.append({'step':step,'width':width})
        else:deltas.append(abs(loc.z-expected))
report['route_probes']={'samples':1296*3,'misses':misses[:30],'miss_count':len(misses),'max_floor_error_m':max(deltas) if deltas else None,'nominal_width_m':3,'rise_m':198/1296,'actual_capsule_sweeps':False,'soldier_navigation_tested':False}
report['dimensions']={'above_ground_height_m':report['lod0']['max'][2],'roof_m':198,'below_grade_extent_m':-min(0,report['lod0']['min'][2]),'note':'Datum Z=0 is ground; first consoles/bed extend below grade as foundations.'}
report['engine_status']='not imported or Play-tested'
report['evidence_limits']=['No blanket intersection-free claim; intentional masonry joints overlap.','No dynamic gameplay, wind, enemies or weather implemented.','Static geometry and sampled route probes do not prove capsule clearance or engine performance.']
with open(os.path.join(OUT,'reports','final-audit.json'),'w') as f:json.dump(report,f,indent=2)
print('FINAL_AUDIT',json.dumps(report),flush=True)
# Independent FBX import into an empty file checks actual units/bounds.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD0.fbx'))
fbx=audit(bpy.context.scene.objects)
with open(os.path.join(OUT,'reports','fbx-reimport.json'),'w') as f:json.dump(fbx,f,indent=2)
print('FBX_REIMPORT',json.dumps(fbx),flush=True)

