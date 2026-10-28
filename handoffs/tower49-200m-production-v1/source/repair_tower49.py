import bpy,bmesh,os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));OUT=os.path.join(ROOT,'outputs','Tower49_Medieval_200m_v1')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
assembly=bpy.data.collections['01_LOD0_ASSEMBLY'];kit=bpy.data.collections['02_MODULAR_KIT'];lods=bpy.data.collections['06_LOD1_2_ASSEMBLIES'];col=bpy.data.collections['04_COLLISION_UCX']
for c in [assembly,kit,lods,col]:c.hide_viewport=False
bpy.context.view_layer.update();seen=set()
for o in list(assembly.objects)+list(kit.objects)+list(lods.objects):
    if o.type!='MESH' or o.data.name in seen:continue
    seen.add(o.data.name);bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm,dist=1e-6,edges=list(bm.edges))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
def select(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.context.view_layer.update()
def fbx(path,obs):
    select(obs);bpy.ops.export_scene.fbx(filepath=path,use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False)
for o in kit.objects:
    if o.type=='MESH':fbx(os.path.join(OUT,'meshes','kit',o.name+'.fbx'),[o]+[c for c in col.objects if c.name.startswith('UCX_'+o.name+'_')])
fbx(os.path.join(OUT,'meshes','Tower49_200m_LOD0.fbx'),list(assembly.objects))
select(list(assembly.objects));bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD0.glb'),use_selection=True,export_format='GLB',export_tangents=True)
for level in [1,2]:
    select([o for o in lods.objects if o.get('lod_level')==level]);bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'meshes','Tower49_200m_LOD'+str(level)+'.glb'),use_selection=True,export_format='GLB',export_tangents=True)
for c in [kit,lods,col]:c.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
print('CLEANUP_DONE',flush=True)

