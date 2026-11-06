import unreal, sys
DRY='--apply' not in sys.argv
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); w=unreal.EditorLevelLibrary.get_editor_world()
SKIP=('Tentacle','Fog','Dome','Bubble')
def probe(a):
    p=a.get_actor_location(); ign=[a]; first=None
    for _ in range(15):
        h=unreal.SystemLibrary.line_trace_single(w, p+unreal.Vector(0,0,300), p-unreal.Vector(0,0,40000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ign, unreal.DrawDebugTrace.NONE, True)
        t=h.to_tuple() if h else None
        if not t or not t[0] or not t[9]: return first, None
        lab=t[9].get_actor_label()
        if first is None: first=lab
        if any(k in lab for k in SKIP) or 'laptop2_realm' in [str(x) for x in t[9].tags] and t[9].get_class().get_name()!='StaticMeshActor': ign.append(t[9]); continue
        return first, t[4].z
    return first, None
out=[]; moved=0
for a in E.get_all_level_actors():
    if 'laptop2_realm' not in [str(t) for t in a.tags]: continue
    lab=a.get_actor_label()
    if any(k in lab for k in SKIP+('Light','Director','Spawn','Fire','Breach','PPV','Wisp','Glow','Crack')): continue
    first, z = probe(a)
    if first and any(k in first for k in SKIP) and z is not None:
        p=a.get_actor_location()
        out.append('%-28s on %-28s drop %.0f'%(lab, first, p.z-z))
        if not DRY: a.modify(); a.set_actor_location(unreal.Vector(p.x,p.y,z), False, False); moved+=1
print('DRY' if DRY else 'APPLIED', 'realm actors sitting on tentacle/fog:', len(out), 'moved', moved)
print('\n'.join(out))
if not DRY: print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels())
