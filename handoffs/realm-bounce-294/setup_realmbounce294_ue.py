# #294 setup (adjustedfilm, 2026-10-31 late). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/realm-bounce-294/setup_realmbounce294_ue.py" --dry-run     only reports
#   py ".../setup_realmbounce294_ue.py"                                           creates BPC_RealmBounce, tags the bubble
#   py ".../setup_realmbounce294_ue.py" --attach                                  AFTER the BPVar + graph paste and Compile:
#                                                                                 adds BPC_RealmBounce to BP_Cannonball
# Touches: a NEW component Blueprint, one component added to BP_Cannonball, and the tag 'RealmBubble' on Realm_Bubble_Owner
# (only if missing; #284 already uses that tag). The bubble's mesh, material, transform and COLLISION are not changed.
import os, sys, unreal

A = sys.argv[1:]
DRY, ATTACH = '--dry-run' in A, '--attach' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\realm-bounce-294'
DEST = '/Game/CastleDefender/Gameplay/Realm'
COMP = DEST + '/BPC_RealmBounce'
BALL = '/Game/CastleDefender/Gameplay/Cannon/BP_Cannonball'
BUBBLE_LABEL, TAG = 'Realm_Bubble_Owner', 'RealmBubble'
EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#294 realm bounce %s%s' % ('--attach' if ATTACH else 'setup', ' (DRY RUN)' if DRY else '')]

# ---- the bubble: tag + a read-only report of its collision (it must have query collision for the trace; overlap is fine)
bub = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == BUBBLE_LABEL]
if not bub:
    log.append('NO actor labelled %s in the open level' % BUBBLE_LABEL)
else:
    a = bub[0]
    if TAG in [str(t) for t in a.tags]: log.append('%s already tagged %s' % (BUBBLE_LABEL, TAG))
    else:
        log.append('tag %s %s' % (BUBBLE_LABEL, TAG))
        if not DRY: a.tags = list(a.tags) + [unreal.Name(TAG)]; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    others = [x.get_actor_label() for x in EAS.get_all_level_actors() if TAG in [str(t) for t in x.tags] and x != a]
    if others: log.append('WARNING: also tagged %s: %s (the ball uses the FIRST one found; remove the tag from old domes)' % (TAG, others))
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        log.append('  %s: profile %s, collision %s (needs Query: QueryOnly or QueryAndPhysics)' % (c.get_name(), c.get_collision_profile_name(), c.get_collision_enabled()))

if not ATTACH:
    if EAL.does_asset_exist(COMP): log.append('reusing ' + COMP)
    else:
        log.append('create ' + COMP + ' (ActorComponent)')
        if not DRY:
            f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
            bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset('BPC_RealmBounce', DEST, unreal.Blueprint, f)
            unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_asset(COMP)
    log.append('Next: 6 lines of VARIABLES_BPVar.txt + BPC_RealmBounce_graph.txt into BPC_RealmBounce, Compile, Save, then --attach.')
else:
    ball = unreal.load_asset(BALL) if EAL.does_asset_exist(BALL) else None
    cls = unreal.load_class(None, COMP + '.BPC_RealmBounce_C') if EAL.does_asset_exist(COMP) else None
    if not ball: log.append('BP_Cannonball missing at ' + BALL)
    elif not cls: log.append('BPC_RealmBounce missing: run the setup without --attach first')
    else:
        hs = sds.k2_gather_subobject_data_for_blueprint(ball)
        names = [str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in hs]
        if 'RealmBounce' in names: log.append('BP_Cannonball already has RealmBounce')
        else:
            log.append('BP_Cannonball + RealmBounce (BPC_RealmBounce)')
            if not DRY:
                h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=cls, blueprint_context=ball))
                if not fail.is_empty(): raise RuntimeError('add RealmBounce: %s' % fail)
                sds.rename_subobject(h, unreal.Text('RealmBounce'))
                unreal.BlueprintEditorLibrary.compile_blueprint(ball); EAL.save_asset(BALL)

out = '\n'.join(log)
open(os.path.join(HERE, 'realmbounce294_%s.txt' % ('attach' if ATTACH else 'setup')), 'w').write(out)
unreal.log(out); print(out)
