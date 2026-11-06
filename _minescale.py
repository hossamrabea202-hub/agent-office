import unreal
EAL=unreal.EditorAssetLibrary; S=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
out=[]
for p in EAL.list_assets('/Game/CastleDefender/Environment/Mine', recursive=False):
    o=unreal.load_asset(p)
    if not isinstance(o, unreal.StaticMesh) or not o.get_name().startswith('SM_Mine_'): continue
    e=o.get_bounding_box(); ext=(e.max-e.min).length()
    if ext < 100:
        for lod in range(S.get_lod_count(o)):
            bs=S.get_lod_build_settings(o, lod); bs.set_editor_property('build_scale3d', unreal.Vector(100,100,100)); S.set_lod_build_settings(o, lod, bs)
        for s in o.get_editor_property('sockets') if False else []: pass
        try:
            sk=o.find_socket('Light')
            if sk: sk.set_editor_property('relative_location', sk.get_editor_property('relative_location')*100.0)
        except Exception as ex: out.append('socket %s'%ex)
        EAL.save_asset(p.split('.')[0])
        e2=o.get_bounding_box(); out.append('%s %.1f -> %.1f'%(o.get_name(), ext, (e2.max-e2.min).length()))
    else: out.append('%s ok %.0f'%(o.get_name(), ext))
open(r'C:/Users/hossa/Documents/agent-office/_minescale.txt','w').write('\n'.join(out))
