import unreal, sys
# Redo of today's ACTOR edits that save_all_dirty_levels did not write (World Partition keeps each actor in its own package).
r=[]
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def run(p, args):
    sys.argv=['x']+args; exec(open(p).read(), {'__name__':'__main__','__file__':p})
L=lambda: {a.get_actor_label():a for a in E.get_all_level_actors()}
# 1 realm actors off the tentacle
run(r'C:/Users/hossa/Documents/agent-office/_snap.py', ['--apply'])
# 2 realm bubble: pawns pass
b=L()['Realm_Bubble_Owner']; b.modify(); b.static_mesh_component.set_collision_profile_name('OverlapAllDynamic')
# 3 tentacle scale + no-stretch MI
S={'Env_CorruptedTentacle_5':unreal.Vector(-2.5,2.5,2.5),'Env_CorruptedTentacle_4':unreal.Vector(-3.75,3.75,3.75)}
for k,v in S.items(): a=L()[k]; a.modify(); a.set_actor_scale3d(v)
run(r'C:/Users/hossa/Documents/agent-office/_tfix.py', [])
# 4 blob mines flesh on placed instances
F=unreal.load_asset('/Game/CastleDefender/Environment/Flora/BlobMine/MI_BlobMine_Flesh'); n=0
for x in E.get_all_level_actors():
    if x.get_class().get_name()=='BP_BlobMine_C':
        for c in x.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_name()=='Mine': x.modify(); c.set_material(0,F); n+=1
r.append('mines %d'%n)
# 5 meadow off the gate road
run(r'C:/Users/hossa/Documents/agent-office/_road_clear.py', [])
ok=unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
r.append('save_dirty_packages %s'%ok)
l=L(); r.append('check t5 %s bubble %s tower1z %.0f'%(l['Env_CorruptedTentacle_5'].get_actor_scale3d(), l['Realm_Bubble_Owner'].static_mesh_component.get_collision_profile_name(), l['Realm_Gate_Tower_1'].get_actor_location().z))
print('\n'.join(r))
