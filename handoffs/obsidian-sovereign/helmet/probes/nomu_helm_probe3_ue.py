# Read-only (#485): vertex clouds of the head and gorget, written outside the repo (argv[1]); no asset is changed.
import unreal, sys, time
out=sys.argv[1]
for path,tag in (('/Game/CastleDefender/Characters/Knight/SM_HeroHead','head'),('/Game/CastleDefender/Characters/Knight/Gorget/SM_Gorget_Neck','gneck'),('/Game/CastleDefender/Characters/Knight/Gorget/SM_Gorget_Spine','gspine')):
    t0=time.time();sm=unreal.load_asset(path);d=sm.get_static_mesh_description(0);n=d.get_vertex_count()
    st=max(1,n//12000)
    print(tag,'n',n,'step',st)
    with open(out+'/'+tag+'.txt','w') as f:
        for i in range(0,n,st):
            p=d.get_vertex_position(unreal.VertexID(i));f.write('%.3f %.3f %.3f\n'%(p.x,p.y,p.z))
    print(' t',round(time.time()-t0,2))
