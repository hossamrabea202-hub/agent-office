import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
bub=[a for a in E.get_all_level_actors() if a.get_actor_label()=='Realm_Bubble_Owner'][0]
o,e=bub.get_actor_bounds(False)
L=[]
for a in E.get_all_level_actors():
    if a==bub: continue
    l=a.get_actor_location()
    if abs(l.x-o.x)>e.x+3000 or abs(l.y-o.y)>e.y+3000: continue
    cn=a.get_class().get_name()
    if 'Landscape' in cn or 'Foliage' in cn or 'Instanced' in cn: continue
    parts=[]
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        m=''
        try: m=c.get_material(0).get_name() if c.get_num_materials() else ''
        except: pass
        mesh=''
        if isinstance(c,unreal.StaticMeshComponent) and c.static_mesh: mesh=c.static_mesh.get_name()
        parts.append('%s:%s:%s'%(c.get_class().get_name()[:14],mesh,m))
    for c in a.get_components_by_class(unreal.DecalComponent):
        dm=c.get_decal_material(); parts.append('Decal:%s'%(dm.get_name() if dm else ''))
    ao,ae=a.get_actor_bounds(False)
    L.append('%s | %s | loc %d,%d,%d | half %d,%d,%d | hidden %s | %s'%(a.get_actor_label(),cn,l.x,l.y,l.z,ae.x,ae.y,ae.z,a.is_hidden_ed(),' ; '.join(parts[:4])))
open(r'C:/Users/hossa/Documents/agent-office/_strip_out.txt','w').write('\n'.join(sorted(L)))
