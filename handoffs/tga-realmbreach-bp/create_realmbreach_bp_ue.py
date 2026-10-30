# MASTER ONLY (UE 5.3). Two steps in one script, both idempotent:
#  A. Creates /Game/CastleDefender/Realm/BP_RealmBreach (parent Actor, no components).
#  B. After its variables + graph are pasted (README): places 'Realm_Wall_Breached' (SM_SiegeBarricade_Breach, hidden, no
#     collision) between laptop2's Realm_Wall_Breach_A/B, spawns 'Realm_Breach_BP' there and wires WaveManager,
#     BreachA/B, BreachedWall, RealmSpawns (Realm_Spawn_Zombie_NN) and GiantSpawns (Realm_Spawn_Giant_NN).
# Run once before pasting (A) and once after (B). Save the level afterwards.
#   py "<repo>/handoffs/tga-realmbreach-bp/create_realmbreach_bp_ue.py"
import unreal
DST, NAME = '/Game/CastleDefender/Realm', 'BP_RealmBreach'
MESH = '/Game/CastleDefender/Environment/Boundaries/SiegeKit/SM_SiegeBarricade_Breach'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
path = DST + '/' + NAME
if not EAL.does_asset_exist(path):
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, DST, unreal.Blueprint, f)
    BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp)
    unreal.log('Created %s. Paste BP_RealmBreach_vars.txt (line by line) + the EventGraph, compile, then run this script again.' % path)
else:
    cls = unreal.load_asset(path).generated_class()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    if 'Realm_Wall_Breach_A' not in acts or 'Realm_Wall_Breach_B' not in acts:
        raise RuntimeError('Realm_Wall_Breach_A/B missing: run laptop2 place_realm_ue.py (#169 stage 1) first')
    for old in ('Realm_Breach_BP', 'Realm_Wall_Breached'):
        if old in acts: eas.destroy_actor(acts[old])
    A, B = acts['Realm_Wall_Breach_A'], acts['Realm_Wall_Breach_B']
    la, lb = A.get_actor_location(), B.get_actor_location(); mid = unreal.Vector((la.x + lb.x) / 2, (la.y + lb.y) / 2, min(la.z, lb.z))
    wall = eas.spawn_actor_from_object(unreal.load_asset(MESH), mid, A.get_actor_rotation())
    wall.set_actor_label('Realm_Wall_Breached'); wall.set_folder_path('Gameplay/Realm')
    wall.get_editor_property('static_mesh_component').set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    wall.set_actor_hidden_in_game(True); wall.set_actor_enable_collision(False)
    g = eas.spawn_actor_from_class(cls, mid, unreal.Rotator(0, 0, 0)); g.set_actor_label('Realm_Breach_BP'); g.set_folder_path('Gameplay/Realm')
    def put(name, value):
        for p in (name, ''.join('_' + c.lower() if c.isupper() else c for c in name).lstrip('_')):
            try: g.set_editor_property(p, value); return
            except Exception: pass
        raise RuntimeError('BP_RealmBreach has no variable %s: paste BP_RealmBreach_vars.txt first' % name)
    wm = [a for a in eas.get_all_level_actors() if a.get_class().get_name() == 'BP_ZombieWaveManager_C']
    if not wm: raise RuntimeError('No BP_ZombieWaveManager in the level')
    put('WaveManager', wm[0]); put('BreachA', A); put('BreachB', B); put('BreachedWall', wall)
    put('RealmSpawns', [acts[k] for k in sorted(acts) if k.startswith('Realm_Spawn_Zombie_')])
    put('GiantSpawns', [acts[k] for k in sorted(acts) if k.startswith('Realm_Spawn_Giant_')])
    unreal.log('Realm_Breach_BP wired: breaks at BreachWave (5) -> broken wall, smoke + shake, SwarmUnlocked, realm horde. Save the level.')
