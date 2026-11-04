# Measures the knight's helmet slot from the licensed FBX (read only; the FBX is never copied here).
#   blender -b --factory-startup -P measure_knight_blender.py -- <ShadowknightUE_SK.fbx> <out.json>
import bpy, sys, json
import numpy as np
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.import_scene.fbx(filepath=a[0], automatic_bone_orientation=False)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
out={'objects':[(o.name,o.type,list(o.scale)) for o in bpy.data.objects],'unit_scale':bpy.context.scene.unit_settings.scale_length}
mw=arm.matrix_world
B={}
for n in ('root','pelvis','spine_03','clavicle_l','clavicle_r','neck_01','head','upperarm_l','upperarm_r'):
    b=arm.data.bones.get(n)
    if b:
        M=mw@b.matrix_local
        B[n]={'head':list(M.translation),'tail':list(mw@b.tail_local),'rot':[list(r) for r in M.to_3x3()]}
out['bones']=B
out['allbones']=[b.name for b in arm.data.bones][:30]
slots={}
for o in bpy.data.objects:
    if o.type!='MESH': continue
    me=o.data; M=np.array(o.matrix_world)
    co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    co=(M[:3,:3]@co.T).T+M[:3,3]
    ids=np.empty(len(me.polygons),int); me.polygons.foreach_get('material_index',ids)
    for k,s in enumerate(o.material_slots):
        fv=[v for p,i in zip(me.polygons,ids) if i==k for v in p.vertices]
        if not fv: continue
        P=co[np.unique(fv)]
        slots[o.name+'/'+s.name]={'nverts':len(P),'tris':int(sum(len(p.vertices)-2 for p,i in zip(me.polygons,ids) if i==k)),'min':P.min(0).tolist(),'max':P.max(0).tolist()}
    # helmet detail: per-height cross section
    for k,s in enumerate(o.material_slots):
        if 'elmet' in s.name:
            fv=[v for p,i in zip(me.polygons,ids) if i==k for v in p.vertices]
            P=co[np.unique(fv)]
            np.save(a[1]+'.helmet.npy',P)
            zs=np.percentile(P[:,2],[0,5,25,50,75,95,100])
            prof=[]
            lo,hi=P[:,2].min(),P[:,2].max()
            for z in np.linspace(lo,hi,14)[:-1]:
                sel=P[(P[:,2]>=z)&(P[:,2]<z+(hi-lo)/13)]
                if len(sel): prof.append([round(z,3)]+[round(x,3) for x in (sel[:,0].min(),sel[:,0].max(),sel[:,1].min(),sel[:,1].max())]+[len(sel)])
            out['helmet_profile_z_xmin_xmax_ymin_ymax_n']=prof
            # weights
            vg={g.index:g.name for g in o.vertex_groups}
            sums={}
            for vi in np.unique(fv):
                for g in me.vertices[int(vi)].groups:
                    sums[vg[g.group]]=sums.get(vg[g.group],0)+g.weight
            out['helmet_weights']=sums
out['slots']=slots
json.dump(out,open(a[1],'w'),indent=1)
print(json.dumps(out)[:6000])
