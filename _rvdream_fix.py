import unreal
L=[]
mi=unreal.load_asset('/Game/CastleDefender/Gameplay/Realm/MI_RealmDream')
L.append('MI %s'%mi)
def addb(pp,where):
    s=pp.get_editor_property('settings')
    wb=s.get_editor_property('weighted_blendables')
    arr=[x for x in list(wb.get_editor_property('array')) if x.get_editor_property('object')!=mi]
    w=unreal.WeightedBlendable(); w.set_editor_property('weight',1.0); w.set_editor_property('object',mi); arr.append(w)
    wb2=unreal.WeightedBlendables(); wb2.set_editor_property('array',arr)
    s.set_editor_property('weighted_blendables',wb2)
    pp.set_editor_property('settings',s)
    chk=[b.get_editor_property('object') for b in pp.get_editor_property('settings').get_editor_property('weighted_blendables').get_editor_property('array')]
    L.append('%s blendables now %s'%(where,[c.get_name() if c else None for c in chk]))
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in E.get_all_level_actors():
    if a.get_actor_label()=='Realm_Vision':
        a.modify()
        for c in a.get_components_by_class(unreal.PostProcessComponent):
            c.modify(); addb(c,'Realm_Vision')
L.append('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
open(r'C:/Users/hossa/Documents/agent-office/_rvdream_out.txt','w').write('\n'.join(L))
