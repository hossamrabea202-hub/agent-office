# MASTER ONLY (UE 5.3). #225 siege engines setup (TGA, 2026-10-31). Idempotent; DRY_RUN = True only prints.
#   py "<repo>/handoffs/siege-225/setup_siege_ue.py"
# Run 1 (Blueprints missing) creates in /Game/CastleDefender/Gameplay/Siege/:
#   BP_SiegeEngine  (Character)  components Body (StaticMesh, BlockAllDynamic so cannonballs / bolts / swords hit it,
#                                z -150 so the mesh stands on the ground) + Bridge (StaticMesh, no collision; the graph snaps it to
#                                the Body's Bridge_Hinge socket); capsule r 140 / hh 150; AI possess on spawn, AIController,
#                                orient to movement, yaw rate 45; walk speed is set by the graph.
#   BP_SiegeRam, BP_SiegeTower   children of BP_SiegeEngine (no graph, defaults only)
#   BP_SiegeDirector (Actor)     no components (place it outside the walls where engines should appear)
# Then paste VARIABLES.md into BP_SiegeEngine + BP_SiegeDirector and the two graphs, compile (README).
# Run 2 (Blueprints exist) fills the children's defaults (meshes from /Game/CastleDefender/Props/Siege, #251) and compiles.
import unreal
DRY_RUN = False
DST = '/Game/CastleDefender/Gameplay/Siege'
ART = '/Game/CastleDefender/Props/Siege/'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); LIB = unreal.SubobjectDataBlueprintFunctionLibrary
DEFAULTS = {
    'BP_SiegeRam':   {'Kind': 0, 'MaxHP': 900.0, 'BaseSpeed': 120.0, 'MeshYaw': 180.0, 'GatePeriod': 5.0, 'RamHit': 20.0,
                      'IntactMesh': 'SM_Siege_Ram', 'WreckMesh': 'SM_Siege_RamWreck'},
    'BP_SiegeTower': {'Kind': 1, 'MaxHP': 1800.0, 'BaseSpeed': 90.0, 'MeshYaw': -90.0, 'SpillLeft': 10, 'SpillPeriod': 2.5,
                      'IntactMesh': 'SM_Siege_Tower', 'WreckMesh': 'SM_Siege_TowerWreck', 'BridgeMesh': 'SM_Siege_TowerBridge'},
}
log = lambda m: unreal.log('[siege setup%s] %s' % (' DRY' if DRY_RUN else '', m))


def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): return unreal.load_asset(path), False
    if DRY_RUN: log('would create %s (parent %s)' % (path, parent.get_name() if hasattr(parent, 'get_name') else parent)); return None, True
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DST, unreal.Blueprint, f), True


def add_comp(bp, cls, name):
    root = SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: adding %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


made = []
eng, new = make_bp('BP_SiegeEngine', unreal.Character)
if new and eng:
    body = add_comp(eng, unreal.StaticMeshComponent, 'Body'); body.set_collision_profile_name('BlockAllDynamic')
    body.set_editor_property('relative_location', unreal.Vector(0, 0, -150))
    br = add_comp(eng, unreal.StaticMeshComponent, 'Bridge'); br.set_collision_profile_name('BlockAllDynamic')
    cdo = unreal.get_default_object(eng.generated_class())
    cdo.set_editor_property('auto_possess_ai', unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    cdo.set_editor_property('ai_controller_class', unreal.AIController)
    cdo.set_editor_property('use_controller_rotation_yaw', False)
    cdo.get_editor_property('capsule_component').set_capsule_size(140.0, 150.0)
    mv = cdo.get_editor_property('character_movement')
    mv.set_editor_property('orient_rotation_to_movement', True); mv.set_editor_property('rotation_rate', unreal.Rotator(0, 0, 45))
    mv.set_editor_property('max_walk_speed', 120.0)
    BEL.compile_blueprint(eng); EAL.save_loaded_asset(eng); made.append('BP_SiegeEngine')
for n in ('BP_SiegeRam', 'BP_SiegeTower'):
    parent = eng.generated_class() if eng else 'BP_SiegeEngine'
    bp, new = make_bp(n, parent)
    if new and bp: BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp); made.append(n)
d, new = make_bp('BP_SiegeDirector', unreal.Actor)
if new and d: BEL.compile_blueprint(d); EAL.save_loaded_asset(d); made.append('BP_SiegeDirector')

if not made and not DRY_RUN:          # run 2: defaults on the children (the variables exist now)
    for n, vals in DEFAULTS.items():
        bp = unreal.load_asset(DST + '/' + n); cdo = unreal.get_default_object(bp.generated_class())
        for k, v in vals.items():
            if isinstance(v, str):
                m = unreal.load_asset(ART + v)
                if not m: log('missing %s%s: run assets/tga/SiegeEngines/import_siege_ue.py first' % (ART, v)); continue
                v = m
            try: cdo.set_editor_property(k, v)
            except Exception as e: log('%s.%s not set (%s): paste VARIABLES.md into BP_SiegeEngine and compile, then run again' % (n, k, e))
        BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp); log('%s defaults set' % n)
log('created: %s' % (', '.join(made) or 'nothing new (defaults pass)'))
