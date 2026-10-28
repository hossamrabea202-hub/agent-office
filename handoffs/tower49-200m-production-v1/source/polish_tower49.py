import bpy,bmesh,os,math
import numpy as np
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));OUT=os.path.join(ROOT,'outputs','Tower49_Medieval_200m_v1')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
def pixels(im):
    a=np.empty(im.size[0]*im.size[1]*4,dtype=np.float32);im.pixels.foreach_get(a);return a.reshape(im.size[1],im.size[0],4)
def write(im,rgb):
    a=np.ones((*rgb.shape[:2],4),dtype=np.float32);a[:,:,:3]=rgb;im.pixels.foreach_set(a.ravel());im.filepath_raw=os.path.join(OUT,'textures',im.name.split('.')[0]+'.png');im.file_format='PNG';im.save();im.pack()
raw=bpy.data.images.load(os.path.join(OUT,'textures','T_T49_Masonry_BaseColor_BakeRaw.png'),check_existing=False);rgb=pixels(raw)[:,:,:3]
# Isotropic periodic spectral noise: no repeated sine-grid/checker mottling.
rng=np.random.default_rng(490200);size=2048
white=rng.standard_normal((size,size)).astype(np.float32)
fy=np.fft.fftfreq(size)[:,None]*size;fx=np.fft.rfftfreq(size)[None,:]*size;freq=np.sqrt(fx*fx+fy*fy)
spectrum=np.fft.rfft2(white);field=np.fft.irfft2(spectrum/np.power(5+freq,1.25),s=(size,size)).astype(np.float32)
field=np.clip(field/field.std(),-2.5,2.5)*.075
field=np.repeat(np.repeat(field,2,axis=0),2,axis=1)
col=np.clip(rgb*(1+field[:,:,None]),0,1)
base=bpy.data.images['T_T49_Masonry_BaseColor'];write(base,col)
roughness=np.clip(.84+field*.45,.67,.96);roughness[rgb.mean(axis=2)<.16]=.95
rough=bpy.data.images['T_T49_Masonry_Roughness'];write(rough,np.repeat(roughness[:,:,None],3,axis=2))
orm=bpy.data.images['T_T49_Masonry_ORM'];packed=pixels(orm)[:,:,:3];packed[:,:,1]=roughness;write(orm,packed)
mat=bpy.data.materials['M_T49_BakedLimestone']
for node in mat.node_tree.nodes:
    if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.45
seen=set()
for cname in ['01_LOD0_ASSEMBLY','02_MODULAR_KIT','06_LOD1_2_ASSEMBLIES']:
    for ob in bpy.data.collections[cname].objects:
        if ob.type!='MESH' or ob.data.name in seen:continue
        seen.add(ob.data.name)
        if not ob.data.materials or ob.data.materials[0]!=mat:continue
        uv=ob.data.uv_layers[0]
        for p in ob.data.polygons:
            c=p.center;r=max(.0001,math.hypot(c.x,c.y));nr=abs((p.normal.x*c.x+p.normal.y*c.y)/r);nt=abs((-p.normal.x*c.y+p.normal.y*c.x)/r)
            angles=[math.atan2(ob.data.vertices[ob.data.loops[i].vertex_index].co.y,ob.data.vertices[ob.data.loops[i].vertex_index].co.x) for i in p.loop_indices]
            wrap=max(angles)-min(angles)>math.pi
            for idx,a in zip(p.loop_indices,angles):
                co=ob.data.vertices[ob.data.loops[idx].vertex_index].co
                if abs(p.normal.z)>max(nr,nt):u,v=co.x/2,co.y/2
                elif nr>=nt:u,v=(a+(2*math.pi if wrap and a<0 else 0))*10.5/2,co.z/2
                else:u,v=math.hypot(co.x,co.y)/2,co.z/2
                uv.data[idx].uv=(u,v)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Master.blend'))
print('MATERIAL_AND_UV_POLISH_DONE',flush=True)
exec(compile(open(os.path.join(ROOT,'work','repair_tower49.py'),encoding='utf-8').read(),'repair_tower49.py','exec'))

