import bpy,bmesh,os,json
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));OUT=os.path.join(ROOT,'outputs','Tower49_Medieval_200m_v1')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
K=bpy.data.collections['02_MODULAR_KIT'];C=bpy.data.collections['04_COLLISION_UCX'];A=bpy.data.collections['01_LOD0_ASSEMBLY'];K.hide_viewport=False;C.hide_viewport=False
door=bpy.data.objects['SM_T49_OakDoor'];module=door.copy();K.objects.link(module);module.name='SM_T49_OakDoor_Module';module.location=(0,0,0);module.rotation_euler=(0,0,0);module.scale=(1,1,1)
lo=[min(v.co[k] for v in module.data.vertices) for k in range(3)];hi=[max(v.co[k] for v in module.data.vertices) for k in range(3)]
bm=bmesh.new();vs=[bm.verts.new((x,y,z)) for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]];bmesh.ops.convex_hull(bm,input=vs,use_existing_faces=False);me=bpy.data.meshes.new('DoorClosedCollision');bm.to_mesh(me);bm.free()
ucx=bpy.data.objects.new('UCX_'+module.name+'_00',me);C.objects.link(ucx)
bpy.ops.object.select_all(action='DESELECT');module.select_set(True);ucx.select_set(True);bpy.context.view_layer.objects.active=module
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'meshes','kit',module.name+'.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False)
door['module']=module.name
manifest_path=os.path.join(OUT,'meshes','assembly.json');manifest=json.load(open(manifest_path))
for entry in manifest['placements']:
    if entry['name']==door.name:entry['module']=module.name
json.dump(manifest,open(manifest_path,'w'),indent=2)
kitpath=os.path.join(OUT,'reports','kit.json');kit=json.load(open(kitpath));kit.append({'mesh':module.name,'triangles':sum(len(p.vertices)-2 for p in module.data.polygons),'ucx_hulls':1,'uv_layers':len(module.data.uv_layers)});json.dump(kit,open(kitpath,'w'),indent=2)
K.hide_viewport=True;C.hide_viewport=True;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
print('DOOR_MODULE_DONE',flush=True)

