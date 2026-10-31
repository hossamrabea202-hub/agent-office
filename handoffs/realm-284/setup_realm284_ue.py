# MASTER ONLY (UE 5.3). #284 realm bubble setup (TGA, 2026-10-31). Game level open. DRY_RUN = True only prints.
#   py "<repo>/handoffs/realm-284/setup_realm284_ue.py"
# 1. Tags the dome actor (label Realm_Dome) 'RealmBubble' and PPV_Realm 'RealmPPV' (both keep their other tags; the
#    laptop2_realm tag stays, so place_realm_ue.py still owns them). Re-run after re-running place_realm_ue.py.
# 2. Creates /Game/CastleDefender/Gameplay/Realm/BP_RealmDirector (Actor) if missing.
# 3. Places one BP_RealmDirector (label Realm_Director, NOT tagged laptop2_realm) at the dome, once the graph is pasted.
# Save the level afterwards.
import unreal
DRY_RUN = False
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
dome = tag('Realm_Dome', 'RealmBubble'); tag('PPV_Realm', 'RealmPPV')
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
