# #433 P1 (Alien): the kit shield sits in the left hand edge-on, like a weapon (i5 / adjustedfilm, 2026-11-02). UE 5.8.
# Cause: BPC_ShieldKit puts the shield (hero component OffHand, parented to bone hand_l) at GripLoc / GripRot per shield,
# and those were left at 0 when the kit was built ("tune later", setup_shieldkit_ue.py). Identity rotation in the hand
# bone's frame = the shield lines up with the hand like a blade.
# This computes, per shield, the grip that a strapped shield has: its FACE (the mesh's thinnest axis, boss side out)
# points out of the back of the hand/forearm, its LONG axis runs along the forearm, and its centre sits on the forearm,
# not in the fist. It uses the hero's real skeleton (reference pose) and each shield mesh's bounds.
#   py fix_shield_grip_ue.py --dry-run          print current and computed GripLoc / GripRot (changes nothing)
#   py fix_shield_grip_ue.py --preview <dir>    TEMPORARY hero mesh + the 3 shields at the computed grip, renders
#                                               <dir>/shield433_<i>.png (front + side), deletes the actors, nothing saved
#   py fix_shield_grip_ue.py --apply            writes GripLoc / GripRot on BPC_ShieldKit (defaults), compile, save
#   --flip                                      turn the face 180 deg (if the preview shows the strap side out)
#   --upside                                    turn the shield 180 deg about its face (owner 2026-11-02: it hung upside down)
#   --revert                                    puts back the values printed by the last --apply (grip433_backup.json)
import json, os, sys, unreal
A = sys.argv[1:]
HERE = os.path.dirname(os.path.abspath(__file__))
EAL, BEL, ML = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.MathLibrary
KIT = '/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
BONE, ELBOW = 'hand_l', 'lowerarm_l'
DATA = json.load(open(os.path.join(HERE, '..', 'shop-v2-418', 'shields', 'shieldkit_data.json')))['shields']
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = ['#433 shield grip' + (' DRY RUN' if '--dry-run' in A else '') + (' FLIP' if '--flip' in A else '') + (' UPSIDE' if '--upside' in A else '')]


def hero_mesh():
    cdo = unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class(HERO))
    sk = cdo.get_editor_property('mesh')
    return sk.get_editor_property('skeletal_mesh_asset'), sk.get_relative_transform() if hasattr(sk, 'get_relative_transform') else None


def unit(v): return v.normal() if hasattr(v, 'normal') else ML.normal(v)


def compute(hand, elbow, mesh, flip):
    """hand / elbow: world transforms of the bones in the reference pose; mesh: shield StaticMesh -> relative transform."""
    f = unit(hand.translation - elbow.translation)                           # forearm direction (elbow -> wrist)
    up = unreal.Vector(0, 0, 1)
    d = unit(up - f * up.dot(f))                                             # back of the forearm (palms face down in the ref pose)
    if flip: d = d * -1.0
    b = mesh.get_bounding_box(); mn, mx = b.min, b.max
    ext = [mx.x - mn.x, mx.y - mn.y, mx.z - mn.z]
    thin = ext.index(min(ext)); long_ = ext.index(max(ext))
    axes = [unreal.Vector(1, 0, 0), unreal.Vector(0, 1, 0), unreal.Vector(0, 0, 1)]
    lo, hi = [mn.x, mn.y, mn.z][thin], [mx.x, mx.y, mx.z][thin]
    sgn = 1.0 if abs(hi) >= abs(lo) else -1.0                                # the boss / face bulges further from the pivot
    rm = ML.make_rot_from_xz(axes[long_] * (-1.0 if '--upside' in A else 1.0), axes[thin] * sgn)                  # mesh frame: X = long, Z = face
    rw = ML.make_rot_from_xz(f, d)                                           # wanted world frame
    # Q maps mesh axes onto the wanted world axes: apply Rm^-1, then Rw (compose_transforms(A, B) = A then B)
    one = unreal.Vector(1, 1, 1)
    q = ML.compose_transforms(ML.invert_transform(unreal.Transform(unreal.Vector(0, 0, 0), rm, one)),
                              unreal.Transform(unreal.Vector(0, 0, 0), rw, one))
    centre = unreal.Vector((mn.x + mx.x) * 0.5, (mn.y + mx.y) * 0.5, (mn.z + mx.z) * 0.5)
    forearm = (hand.translation - elbow.translation).length()
    want_centre = hand.translation - f * (forearm * 0.35) + d * (ext[thin] * 0.5 + 4.0)
    pos = want_centre - ML.transform_direction(q, centre)
    world = unreal.Transform(pos, ML.transform_rotation(q, unreal.Rotator(0, 0, 0)) if hasattr(ML, 'transform_rotation') else q.rotation.rotator(), one)
    rel = ML.compose_transforms(world, ML.invert_transform(hand))           # shield world = rel * hand
    return rel, ext, thin, long_


def bone_xforms(sk_comp):
    w = sk_comp.get_socket_transform(BONE, unreal.RelativeTransformSpace.RTS_WORLD)
    e = sk_comp.get_socket_transform(ELBOW, unreal.RelativeTransformSpace.RTS_WORLD)
    return w, e


kit = unreal.load_asset(KIT)
kcdo = unreal.get_default_object(kit.generated_class())
cur_loc, cur_rot = list(kcdo.get_editor_property('GripLoc')), list(kcdo.get_editor_property('GripRot'))
log.append('current GripLoc %s' % [(round(v.x, 1), round(v.y, 1), round(v.z, 1)) for v in cur_loc])
log.append('current GripRot %s' % [(round(r.roll, 1), round(r.pitch, 1), round(r.yaw, 1)) for r in cur_rot])
if '--revert' in A:
    bk = json.load(open(os.path.join(HERE, 'grip433_backup.json')))
    kcdo.set_editor_property('GripLoc', [unreal.Vector(*v) for v in bk['loc']])
    kcdo.set_editor_property('GripRot', [unreal.Rotator(*r) for r in bk['rot']])
    BEL.compile_blueprint(kit); EAL.save_asset(KIT); log.append('reverted to grip433_backup.json, compiled, saved')
    print('\n'.join(log)); raise SystemExit

skm, _ = hero_mesh()
tmp = EAS.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 30000), unreal.Rotator(0, 0, 0))
made = [tmp]
try:
    skc = tmp.skeletal_mesh_component
    skc.set_skinned_asset_and_update(skm) if hasattr(skc, 'set_skinned_asset_and_update') else skc.set_editor_property('skeletal_mesh_asset', skm)
    hand, elbow = bone_xforms(skc)
    locs, rots = [], []
    for i, s in enumerate(DATA):
        mesh = unreal.load_asset(s['mesh'])
        rel, ext, thin, long_ = compute(hand, elbow, mesh, '--flip' in A)
        r = rel.rotation.rotator() if hasattr(rel.rotation, 'rotator') else rel.rotation
        locs.append(rel.translation); rots.append(r)
        log.append('%-24s ext %s thin=%s long=%s -> GripLoc (%.1f, %.1f, %.1f) GripRot (r %.1f, p %.1f, y %.1f)' % (
            s['name'], [round(e) for e in ext], 'XYZ'[thin], 'XYZ'[long_], rel.translation.x, rel.translation.y, rel.translation.z, r.roll, r.pitch, r.yaw))
        if '--preview' in A:
            out = A[A.index('--preview') + 1]
            sh = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 30000), unreal.Rotator(0, 0, 0)); made.append(sh)
            sh.static_mesh_component.set_static_mesh(mesh); sh.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            sh.attach_to_component(skc, BONE, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.KEEP_WORLD, False)
            sh.static_mesh_component.set_relative_transform(rel, False, False)
            log.append('  preview %d: shield at %s, hand at %s' % (i, sh.static_mesh_component.get_world_location(), hand.translation))
            sys.path.insert(0, os.path.join(HERE, '..', 'contact-decals-425')); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
            c = hand.translation
            lookdev_cap.shot('%s/shield433_%d_front.png' % (out, i), c + unreal.Vector(220, 0, 20), c, 1.5, 45)
            lookdev_cap.shot('%s/shield433_%d_side.png' % (out, i), c + unreal.Vector(0, -220, 20), c, 1.5, 45)
            EAS.destroy_actor(sh); made.remove(sh)
    if '--apply' in A:
        json.dump({'loc': [[v.x, v.y, v.z] for v in cur_loc], 'rot': [[r.roll, r.pitch, r.yaw] for r in cur_rot]}, open(os.path.join(HERE, 'grip433_backup.json'), 'w'))
        kcdo.set_editor_property('GripLoc', locs); kcdo.set_editor_property('GripRot', rots)
        BEL.compile_blueprint(kit); EAL.save_asset(KIT); log.append('APPLIED to BPC_ShieldKit defaults (backup grip433_backup.json), compiled, saved')
finally:
    for x in made: EAS.destroy_actor(x)
print('\n'.join(log))
