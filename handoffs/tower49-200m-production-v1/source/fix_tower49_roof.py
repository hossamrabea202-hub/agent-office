import bpy,os,math,json
from mathutils import Matrix
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));OUT=os.path.join(ROOT,'outputs','Tower49_Medieval_200m_v1')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
A=bpy.data.collections['01_LOD0_ASSEMBLY'];K=bpy.data.collections['02_MODULAR_KIT'];C=bpy.data.collections['04_COLLISION_UCX'];L=bpy.data.collections['06_LOD1_2_ASSEMBLIES']
for c in [A,K,C,L]:c.hide_viewport=False
bpy.context.view_layer.update()
src=bpy.data.objects['SM_T49_RoofDeck_45'];inner=src.copy();inner.data=src.data.copy();K.objects.link(inner);inner.name='SM_T49_RoofDeckInner_45';inner.data.transform(Matrix.Diagonal((10.5/13.9,10.5/13.9,1,1)))
target=next(o for o in A.objects if o.data==src.data and round(math.degrees(o.rotation_euler.z))%360==315)
target.data=inner.data;target['module']=inner.name
for o in L.objects:
    if o.name.startswith(target.name+'_LOD'):o.data=inner.data
remove=[]
for o in A.objects:
    if o.name.startswith('SM_T49_CrownCorbel_45') and round(math.degrees(o.rotation_euler.z))%360 in [270,315]:remove.append(o)
for o in remove:
    name=o.name
    for low in list(L.objects):
        if low.name.startswith(name+'_LOD'):bpy.data.objects.remove(low,do_unlink=True)
    bpy.data.objects.remove(o,do_unlink=True)
rail_source=bpy.data.objects['SM_T49_CrownParapet_45'];rail=rail_source.copy();rail.data=rail_source.data.copy();K.objects.link(rail);rail.name='SM_T49_StairwellGuard_45';rail.data.transform(Matrix.Diagonal((10.45/14.1,10.45/14.1,1,1)))
o=bpy.data.objects.new('SM_T49_StairwellGuard',rail.data);A.objects.link(o);o.location.z=198;o.rotation_euler.z=7*math.pi/4;o['module']=rail.name
for level in [1,2]:
    cp=o.copy();L.objects.link(cp);cp.name=o.name+'_LOD'+str(level);cp['lod_level']=level
for source,new,scale in [(src,inner,10.5/13.9),(rail_source,rail,10.45/14.1)]:
    for old in list(C.objects):
        if old.name.startswith('UCX_'+source.name+'_'):
            cp=old.copy();cp.data=old.data.copy();C.objects.link(cp);cp.name=old.name.replace('UCX_'+source.name+'_','UCX_'+new.name+'_');cp.data.transform(Matrix.Diagonal((scale,scale,1,1)))
manifest=[]
for o in A.objects:
    key=o.get('module') or next((k.name for k in K.objects if k.type=='MESH' and k.data==o.data),None)
    manifest.append({'name':o.name,'module':key,'location_m':list(o.location),'rotation_xyz_degrees':[math.degrees(a) for a in o.rotation_euler],'scale':list(o.scale)})
with open(os.path.join(OUT,'meshes','assembly.json'),'w') as f:json.dump({'units':'meters','height_m':200,'roof_m':198,'roof_stairwell':'outer 45-degree sector at 315..360 degrees open, inner edge guarded','placements':manifest},f,indent=2)
with open(os.path.join(OUT,'reports','kit.json'),'w') as f:json.dump([{'mesh':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'ucx_hulls':sum(c.name.startswith('UCX_'+o.name+'_') for c in C.objects),'uv_layers':len(o.data.uv_layers)} for o in K.objects if o.type=='MESH'],f,indent=2)
for c in [K,C,L]:c.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
exec(compile(open(os.path.join(ROOT,'work','repair_tower49.py'),encoding='utf-8').read(),'repair_tower49.py','exec'))

