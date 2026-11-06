import unreal
EAL=unreal.EditorAssetLibrary; E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L=[]
for p in ['/Game/CastleDefender/Environment/Mud/BPC_MudPrints','/Game/CastleDefender/Environment/Mud/BP_MudPad','/Game/CastleDefender/Environment/Mud/MI_MudPrint']:
    L.append('%s exists=%s'%(p,EAL.does_asset_exist(p)))
bp=unreal.load_asset('/Game/CastleDefender/Environment/Mud/BPC_MudPrints')
if bp:
    cdo=unreal.get_default_object(bp.generated_class())
    for v in ['FootDrop','Stride','PrintsLeft','Pads','PadRadius','Interval']:
        try: L.append('var %s=%s'%(v,cdo.get_editor_property(v)))
        except Exception as e: L.append('var %s missing'%v)
    try:
        g=[x for x in unreal.BlueprintEditorLibrary.find_event_graph(bp).get_editor_property('nodes')] 
        L.append('graph nodes %d'%len(g))
    except Exception as e: L.append('graph ? %s'%e)
acts=E.get_all_level_actors()
pads=[a for a in acts if a.actor_has_tag('MudPad')]
L.append('MudPads %d: %s'%(len(pads),[(a.get_actor_label(),[round(c) for c in (a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z)]) for a in pads]))
hero=unreal.load_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
L.append('hero %s'%bool(hero))
sl=[]
for a in acts:
    lab=a.get_actor_label(); n=lab.lower()
    hit=any(k in n for k in ['slime','goo','ooze','blobmine','blob_mine','jelly','puddle'])
    if not hit:
        for c in a.get_components_by_class(unreal.DecalComponent):
            m=c.get_decal_material()
            if m and any(k in m.get_name().lower() for k in ['slime','goo','ooze','jelly','flesh']): hit=True
    if hit:
        l=a.get_actor_location(); sl.append('%s|%s|%d,%d,%d'%(lab,a.get_class().get_name(),l.x,l.y,l.z))
L.append('slime-like %d'%len(sl)); L+=sl[:80]
open(r'C:/Users/hossa/Documents/agent-office/_mud_out.txt','w').write('\n'.join(L))
