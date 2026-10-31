# MASTER ONLY (UE 5.3). #284 realm bubble setup (TGA, 2026-10-31). Game level open. DRY_RUN = True only prints.
#   py "<repo>/handoffs/realm-284/setup_realm284_ue.py"
# 1. Tags the dome actor 'RealmBubble'. v2 (#299 owner bug): the live dome is Realm_Bubble_Owner (SM_RealmBubbleHi,
#    owner-sculpted); the script now finds it by label (Realm_Bubble_Owner, then Realm_Dome) or by a mesh named *RealmBubble*, and PPV_Realm 'RealmPPV' (both keep their other tags; the
#    laptop2_realm tag stays, so place_realm_ue.py still owns them). Re-run after re-running place_realm_ue.py.
# 2. Creates /Game/CastleDefender/Gameplay/Realm/BP_RealmDirector (Actor) if missing.
# 3. Places one BP_RealmDirector (label Realm_Director, NOT tagged laptop2_realm) at the dome, once the graph is pasted.
# Save the level afterwards.
import unreal
DRY_RUN = True
DST = '/Game/CastleDefender/Gameplay/Realm'
EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = lambda m: unreal.log('[realm284%s] %s' % (' DRY' if DRY_RUN else '', m))
actors = eas.get_all_level_actors()
def tag(label, t):
    hit = [a for a in actors if a.get_actor_label() == label]
    if not hit: log('no actor labelled %s (run handoffs/realm-169/place_realm_ue.py first?)' % label); return None
    a = hit[0]
    if t in [str(x) for x in a.tags]: log('%s already tagged %s' % (label, t)); return a
    if DRY_RUN: log('would tag %s %s' % (label, t)); return a
    a.tags = list(a.tags) + [unreal.Name(t)]; log('tagged %s %s' % (label, t)); return a
def find_dome():
    for lb in ('Realm_Bubble_Owner', 'Realm_Dome'):
        if [a for a in actors if a.get_actor_label() == lb]: return lb
    for a in actors:
        smc_ = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc_ and smc_.static_mesh and 'RealmBubble' in smc_.static_mesh.get_name(): return a.get_actor_label()
    return 'Realm_Bubble_Owner'
DOME = find_dome(); log('dome actor = %s' % DOME)
dome = tag(DOME, 'RealmBubble')
tag('PPV_Realm', 'RealmPPV')
# ---- #294 dome collision: place_realm_ue.py leaves the dome with NO collision. Make it query-only and block ONLY the
# cannonball's object channel (read from a temporary BP_Cannonball), so soldiers, zombies, wasps and the hero (all
# Pawn / CharacterMesh) walk and fly through, and Visibility/Camera traces (ground snapping, aiming) pass too.
# It never touches the dome's material and it does not affect the NavMesh.
CB = '/Game/CastleDefender/Weapons/BP_Cannonball'
def find_bp(name):
    hits = unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint'))
    hits = [h for h in hits if str(h.asset_name) == name]
    return str(hits[0].package_name) if hits else None
ball_ch = None
cb_path = CB if EAL.does_asset_exist(CB) else find_bp('BP_Cannonball')
if cb_path:
    tmp = eas.spawn_actor_from_class(unreal.load_asset(cb_path).generated_class(), unreal.Vector(0, 0, -100000), unreal.Rotator(0, 0, 0))
    if tmp:
        rc = tmp.root_component; ball_ch = rc.get_collision_object_type()
        if rc.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC) != unreal.CollisionResponseType.ECR_BLOCK:
            log('WARNING: BP_Cannonball does not block WorldDynamic, so it will pass the dome: set its root collision to block WorldDynamic')
        eas.destroy_actor(tmp)
if ball_ch is None: log('BP_Cannonball not found: dome collision left unchanged, tell TGA');
elif dome:
    smc = dome.get_component_by_class(unreal.StaticMeshComponent)          # v2: works for StaticMeshActor and BP actors
    log('cannonball object channel = %s' % ball_ch)
    if ball_ch in (unreal.CollisionChannel.ECC_PAWN, unreal.CollisionChannel.ECC_VISIBILITY):
        log('the cannonball uses the %s channel, so the dome cannot block it alone: dome left unchanged, tell TGA' % ball_ch)
    elif DRY_RUN: log('would set %s collision:' % DOME + ' QueryOnly, ignore all, block %s, no navmesh, complex-as-simple mesh' % ball_ch)
    else:
        sm = smc.static_mesh; bs = sm.get_editor_property('body_setup') if sm else None
        if bs and bs.get_editor_property('collision_trace_flag') != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
            bs.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)  # the shell, not a solid hull
            EAL.save_loaded_asset(sm); log('%s: collision = complex as simple (hits the membrane surface; collision only, material untouched)' % sm.get_name())
        smc.modify(); dome.modify()                                             # v2: record the edit so it is saved with the level
        smc.set_collision_profile_name('Custom')
        smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        smc.set_collision_object_type(unreal.CollisionChannel.ECC_WORLD_DYNAMIC)
        smc.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
        smc.set_collision_response_to_channel(ball_ch, unreal.CollisionResponseType.ECR_BLOCK)
        smc.set_editor_property('can_ever_affect_navigation', False)
        R = unreal.CollisionResponseType
        ok = (smc.get_collision_response_to_channel(ball_ch) == R.ECR_BLOCK and smc.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN) != R.ECR_BLOCK)
        if not ok:                                                              # v2 fallback: a built-in profile that persists
            smc.set_collision_profile_name('OverlapOnlyPawn')                   # query only; overlaps Pawn, blocks everything else
            log('per-channel responses did not stick on %s: used profile OverlapOnlyPawn instead (pawns pass, cannonballs blocked; '
                'it also blocks Camera/Visibility traces, so the camera may pull in when crossing the membrane - tell TGA if it does)' % DOME)
        log('%s collision now: profile %s, enabled %s, %s -> %s, Pawn -> %s - save the level, then re-open it and run this again '
            'with DRY_RUN = True to confirm it stuck' % (DOME, smc.get_collision_profile_name(), smc.get_collision_enabled(), ball_ch,
            smc.get_collision_response_to_channel(ball_ch), smc.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)))
if dome and DRY_RUN:                                                            # read-back for the check after a re-open
    s_ = dome.get_component_by_class(unreal.StaticMeshComponent)
    log('current %s collision: profile %s, enabled %s, Pawn -> %s' % (DOME, s_.get_collision_profile_name(), s_.get_collision_enabled(),
        s_.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)))
path = DST + '/BP_RealmDirector'
if not EAL.does_asset_exist(path):
    if DRY_RUN: log('would create %s' % path)
    else:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_RealmDirector', DST, unreal.Blueprint, f)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_loaded_asset(bp)
        log('created %s: paste VARIABLES.md + BP_RealmDirector_graph.txt, compile, then run this again to place it' % path)
else:
    cls = unreal.load_asset(path).generated_class()
    if [a for a in actors if a.get_class() == cls]: log('Realm_Director already placed')
    elif dome is None: log('no dome, not placing the director')
    elif DRY_RUN: log('would place Realm_Director at the dome')
    else:
        d = eas.spawn_actor_from_class(cls, dome.get_actor_location(), unreal.Rotator(0, 0, 0))
        d.set_actor_label('Realm_Director'); d.set_folder_path('Gameplay/Realm'); log('placed Realm_Director - save the level')
