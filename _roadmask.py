import unreal, math, json
# Remove Meadow351 plants where the owner's landscape grass does not grow (roads, tracks, bare paths).
# Landscape grass only exists near the editor camera, so the camera visits the meadow on a grid; at each stop we wait
# for the grass to build, then test the meadow instances near that stop. Result -> _roadmask.txt. Aborts if >45% would go.
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); UES=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
OUT=r'C:/Users/hossa/Documents/agent-office/_roadmask.txt'
mead=[a for a in E.get_all_level_actors() if a.get_actor_label()=='Meadow351'][0]
inst=[]   # (comp, idx, x, y, z)
for c in mead.get_components_by_class(unreal.InstancedStaticMeshComponent):
    for i in range(c.get_instance_count()):
        p=c.get_instance_transform(i, True).translation; inst.append([c, i, p.x, p.y, p.z, None])
xs=[r[2] for r in inst]; ys=[r[3] for r in inst]
STEP=4000.0; R=STEP*0.75
stops=[]; x=min(xs)
while x<=max(xs)+1:
    y=min(ys)
    while y<=max(ys)+1:
        if any(abs(r[2]-x)<R and abs(r[3]-y)<R for r in inst[::25]): stops.append((x,y))
        y+=STEP
    x+=STEP
st={'k':0,'wait':0,'h':None,'log':['instances %d stops %d'%(len(inst),len(stops))]}
cam0=UES.get_level_viewport_camera_info()
def grass_comps(cx,cy):
    out=[]
    for a in E.get_all_level_actors():
        if 'Landscape' not in a.get_class().get_name(): continue
        o,e,_=unreal.SystemLibrary.get_component_bounds(a.root_component) if a.root_component else (None,None,None)
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if c.get_instance_count()==0: continue
            o,e,_r=unreal.SystemLibrary.get_component_bounds(c)
            if abs(o.x-cx)<R+e.x+200 and abs(o.y-cy)<R+e.y+200: out.append((c,o,e))
    return out
def evaluate(cx,cy):
    gc=grass_comps(cx,cy); n=0
    if not gc: return 0
    for r in inst:
        if r[5] is not None or abs(r[2]-cx)>R or abs(r[3]-cy)>R: continue
        p=unreal.Vector(r[2],r[3],r[4]); hit=False
        for c,o,e in gc:
            if abs(p.x-o.x)>e.x+200 or abs(p.y-o.y)>e.y+200: continue
            if c.get_instances_overlapping_sphere(p, 200.0, True): hit=True; break
        r[5]=hit; n+=1
    return n
def finish():
    unreal.unregister_slate_post_tick_callback(st['h'])
    UES.set_level_viewport_camera_info(cam0[0], cam0[1])
    rem=[r for r in inst if r[5] is False]; unk=sum(1 for r in inst if r[5] is None)
    st['log'].append('evaluated %d, no grass (remove) %d, not reached %d'%(len(inst)-unk, len(rem), unk))
    if len(rem) > 0.45*len(inst):
        st['log'].append('ABORT: too many, nothing changed')
    else:
        mead.modify(); by={}
        for r in inst: by.setdefault(r[0], []).append(r)
        for c, rows in by.items():
            if not any(r[5] is False for r in rows): continue
            keep=[c.get_instance_transform(r[1], True) for r in rows if r[5] is not False]
            c.modify(); c.clear_instances(); c.add_instances(keep, False, True)
        st['log'].append('removed %d, save %s'%(len(rem), unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)))
    open(OUT,'w').write('\n'.join(st['log']))
def tick(dt):
    try:
        if st['k']>=len(stops): finish(); return
        cx,cy=stops[st['k']]
        if st['wait']==0:
            h=unreal.SystemLibrary.line_trace_single(unreal.EditorLevelLibrary.get_editor_world(), unreal.Vector(cx,cy,30000), unreal.Vector(cx,cy,-30000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True).to_tuple()
            z=h[4].z if h[0] else 0
            UES.set_level_viewport_camera_info(unreal.Vector(cx,cy,z+600), unreal.Rotator(0,-60,0))
        st['wait']+=1
        if st['wait']>=120:
            n=evaluate(cx,cy); st['log'].append('stop %d (%d,%d): %d tested'%(st['k'],cx,cy,n))
            open(OUT,'w').write('\n'.join(st['log'][-3:]))
            st['k']+=1; st['wait']=0
    except Exception as ex:
        import traceback; st['log'].append(traceback.format_exc()); unreal.unregister_slate_post_tick_callback(st['h']); open(OUT,'w').write('\n'.join(st['log']))
st['h']=unreal.register_slate_post_tick_callback(tick)
open(OUT,'w').write('started: %d instances, %d stops'%(len(inst),len(stops)))
