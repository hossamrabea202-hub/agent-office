# Owner 00:56: fix the stretch on the remaining tentacles exactly like _5 / _4 (uniform scale + no-stretch body MI + shell TentScale).
import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
M=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
NS=unreal.load_asset('/Game/CastleDefender/VFX/Tentacle/MI_CorruptedTentacle_NoStretch') or None
L=[]
if NS is None:
    r=unreal.AssetRegistryHelpers.get_asset_registry()
    for x in r.get_assets_by_path('/Game',True):
        if str(x.asset_name)=='MI_CorruptedTentacle_NoStretch': NS=unreal.load_asset(str(x.package_name)); break
L.append('nostretch MI %s'%(NS.get_path_name() if NS else None))
for a in E.get_all_level_actors():
    if not (isinstance(a, unreal.SkeletalMeshActor) and 'CorruptedTentacle' in a.get_actor_label()): continue
    sc=a.get_actor_scale3d(); ab=[abs(sc.x),abs(sc.y),abs(sc.z)]
    uniform=max(ab)-min(ab)<0.01
    s=max(ab)
    if not uniform:
        a.modify(); a.set_actor_scale3d(unreal.Vector(s*(1 if sc.x>=0 else -1), s*(1 if sc.y>=0 else -1), s*(1 if sc.z>=0 else -1)))
        L.append('%s scale %s -> uniform %.3f'%(a.get_actor_label(), [round(v,3) for v in (sc.x,sc.y,sc.z)], s))
    else: L.append('%s already uniform %.3f'%(a.get_actor_label(), s))
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
        for i,m in enumerate(c.get_materials()):
            if not m: continue
            if 'JellyShell' in m.get_name():
                old=M.get_material_instance_scalar_parameter_value(m,'TentScale')
                if abs(old-s)>0.01:
                    M.set_material_instance_scalar_parameter_value(m,'TentScale',s); M.update_material_instance(m); EAL.save_asset(m.get_path_name().split('.')[0])
                L.append('   shell %s TentScale %.3f -> %.3f'%(m.get_name(),old,s))
            elif 'CorruptedTentacle' in m.get_name() and NS and m!=NS and 'NoStretch' not in m.get_name():
                a.modify(); c.modify(); c.set_material(i,NS); L.append('   body slot %d %s -> NoStretch'%(i,m.get_name()))
L.append('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
open(r'C:/Users/hossa/Documents/agent-office/_tent_out.txt','w').write('\n'.join(L))
