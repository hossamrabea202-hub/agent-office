import bpy,os,math
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));OUT=os.path.join(ROOT,'outputs','Tower49_Medieval_200m_v1')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
scene=bpy.context.scene
for c in scene.collection.children:
    c.hide_render=c.name!='01_LOD0_ASSEMBLY'
studio=bpy.data.collections.new('07_FINAL_PRESENTATION');scene.collection.children.link(studio)
def move(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    studio.objects.link(o)
bpy.ops.mesh.primitive_plane_add(size=600,location=(0,0,-.015));ground=bpy.context.object;move(ground)
mat=bpy.data.materials.new('Presentation ground');mat.diffuse_color=(.12,.105,.085,1);mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.12,.105,.085,1);p.inputs['Roughness'].default_value=.9;ground.data.materials.append(mat)
world=bpy.data.worlds.new('Soft daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.3,.35,.4,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.45
d=bpy.data.lights.new('Daylight sun','SUN');d.energy=2.2;d.angle=.2;d.color=(1,.93,.83);o=bpy.data.objects.new(d.name,d);studio.objects.link(o);o.rotation_euler=(.5,-.4,-.35)
def area(name,loc,watts,size,target):
    d=bpy.data.lights.new(name,'AREA');d.energy=watts;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Sky fill',(-50,-50,120),50000,100,(0,0,90))
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.2
def render(name,loc,target,scale,res):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();scene.camera=o
    scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];scene.render.resolution_percentage=100;scene.render.filepath=os.path.join(OUT,'renders',name+'.png');print('FINAL_RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
render('02_stair_closeup',(30,-40,15),(0,0,7),26,(1600,1200))
render('01_full_tower',(260,-350,170),(0,0,98),218,(1000,2000))
render('03_crown',(42,-54,222),(0,0,194),39,(1600,1200))
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_distance=230;a.spaces.active.region_3d.view_location=(0,0,100)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Presentation.blend'))
print('FINAL_RENDERS_DONE',flush=True)

