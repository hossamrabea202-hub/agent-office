# #169 stage 1: the realm gate's E-to-open behaviour WITHOUT a new Blueprint: the level's BP_CastleGateControl already
# does E prompt (3 m), MoveComponentTo on two door pivots + a lever, a ZombieStop blocker, damage/repair. This script
# spawns one at the realm gate (where place_realm_ue.py put Realm_Gate_Frame) and overrides, on that instance only:
#   DoorLeftWood / DoorRightWood  -> SM_SiegeGate_LeafL / _LeafR (their pivots are already on the hinge line)
#   DoorLeftIron / DoorRightIron  -> hidden (the siege gate has no iron door layer; the bands are in the leaf mesh)
#   DoorLeft / DoorRight pivots   -> the hinge positions from gate_meta.json (+-2.88 m, outside = -Y of the frame)
#   LeverPivot                    -> the lever pin (-4.03, 0.40, 1.18 m) with SM_SiegeGate_Lever
#   ZombieStop                    -> scaled to the 5.8 m opening
# and removes the static Realm_Gate_LeafL/LeafR/Bar/Lever actors (the frame stays). Run AFTER place_realm_ue.py:
#   py "<repo>/handoffs/realm-169/place_realm_gate_bp.py"
# Idempotent: an existing Realm_Gate_BP is replaced. If the open angle swings the wrong way, flip the sign of the
# door pivots' open rotation on the instance (BP_CastleGateControl exposes it as a variable) or mirror the Y here.
import unreal
GATE = '/Game/CastleDefender/Environment/Boundaries/SiegeGate/'
BPC = '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl'
FOLDER, TAG = 'Gameplay/Realm', 'laptop2_realm'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()
frame = next((a for a in actors if a.get_actor_label() == 'Realm_Gate_Frame'), None)
if frame is None: raise RuntimeError('Realm_Gate_Frame not found: run place_realm_ue.py first')
for a in actors:
    if a.get_actor_label() in ('Realm_Gate_BP', 'Realm_Gate_LeafL', 'Realm_Gate_LeafR', 'Realm_Gate_Bar', 'Realm_Gate_Lever'): eas.destroy_actor(a)
cls = unreal.load_asset(BPC)
if cls is None: raise RuntimeError('BP_CastleGateControl not found at ' + BPC)
loc, rot = frame.get_actor_location(), frame.get_actor_rotation()
gate = eas.spawn_actor_from_object(cls, loc, rot)
gate.set_actor_label('Realm_Gate_BP'); gate.set_folder_path(FOLDER); gate.tags = [unreal.Name(TAG)]
comps = {c.get_name(): c for c in gate.get_components_by_class(unreal.SceneComponent)}
def comp(name): return next((c for n, c in comps.items() if n.lower().startswith(name.lower())), None)
m = lambda n: unreal.load_asset(GATE + n)
leafL, leafR, lever = m('SM_SiegeGate_LeafL'), m('SM_SiegeGate_LeafR'), m('SM_SiegeGate_Lever')
if not (leafL and leafR and lever): raise RuntimeError('SiegeGate meshes not imported (assets/laptop2/SiegeGate/import_kit_ue.py)')
log = []
for pivot, mesh, iron, px in (('DoorLeft', leafL, 'DoorLeftIron', -288.0), ('DoorRight', leafR, 'DoorRightIron', 288.0)):
    p = comp(pivot)
    if p is None: log.append('no component ' + pivot); continue
    p.set_relative_location(unreal.Vector(px, -3.5, 0.0), False, False); p.set_relative_rotation(unreal.Rotator(0, 0, 0), False, False)
    w = comp(pivot + 'Wood')
    if w: w.set_static_mesh(mesh); w.set_relative_location(unreal.Vector(0, 0, 0), False, False); w.set_relative_rotation(unreal.Rotator(0, 0, 0), False, False); w.set_relative_scale3d(unreal.Vector(1, 1, 1))
    i = comp(iron)
    if i: i.set_visibility(False, True); i.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    log.append('%s -> %s' % (pivot, mesh.get_name()))
lp = comp('LeverPivot')
if lp:
    lp.set_relative_location(unreal.Vector(-403.0, 40.0, 118.0), False, False)
    lm = next((c for c in lp.get_children_components(False) if isinstance(c, unreal.StaticMeshComponent)), None)
    if lm: lm.set_static_mesh(lever); lm.set_relative_location(unreal.Vector(0, 0, 0), False, False); lm.set_relative_rotation(unreal.Rotator(0, 0, 0), False, False)
    log.append('LeverPivot -> SM_SiegeGate_Lever')
zs = comp('ZombieStop')
if zs:
    zs.set_relative_location(unreal.Vector(0, 0, 170.0), False, False); zs.set_relative_scale3d(unreal.Vector(9.5, 1.0, 5.5)); log.append('ZombieStop scaled to the 5.8 m opening')
unreal.log('#169 Realm_Gate_BP placed at %s: %s. Play-test E at the gate; tune the open angle on the instance if a leaf swings into the frame.' % (loc, '; '.join(log)))
