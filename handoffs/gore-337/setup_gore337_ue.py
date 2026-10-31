# #337 part 2 editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run. Run AFTER
# assets/adjustedfilm/Blood337/import_blood337_ue.py (textures, decal + cap materials, cap meshes).
#   py "<repo>/handoffs/gore-337/setup_gore337_ue.py" --dry-run
#   py "<repo>/handoffs/gore-337/setup_gore337_ue.py"            makes the 3 Blueprints with their components (README step 1)
#   py ".../setup_gore337_ue.py" --finish [--dry-run]            after the BPVar + graph pastes: BPC_Gore337 defaults (Caps,
#        DecalMat), adds the component "Gore" to BP_Zombie (every child zombie inherits it), compiles and saves
import sys, unreal

A = sys.argv[1:]
DRY, FINISH = '--dry-run' in A, '--finish' in A
D3 = '/Game/CastleDefender/VFX/Blood337'
ZOMBIE = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#337 gore setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def comps(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add(bp, cls, name, parent=None):
    have = comps(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    ph = parent if parent is not None else SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, why = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=ph, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s.%s: %s' % (bp.get_name(), name, why))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


def bp_of(name, parent_cls):
    path = D3 + '/' + name
    if EAL.does_asset_exist(path): log.append('reuse ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent_cls)
    return AT.create_asset(name, D3, unreal.Blueprint, f)


if not FINISH:
    for need in (D3 + '/MI_BloodDecal_337', D3 + '/WoundCaps/SM_WoundCap_Forearm_337'):
        if not EAL.does_asset_exist(need): log.append('MISSING %s: run assets/adjustedfilm/Blood337/import_blood337_ue.py first' % need)
    bp_of('BPC_Gore337', unreal.ActorComponent)
    lb = bp_of('BP_SeveredLimb337', unreal.Actor)
    if lb:
        body = add(lb, unreal.CapsuleComponent, 'Body')
        # the capsule has to be the root (it is the physics body). Adding it to a fresh Actor BP normally replaces the
        # DefaultSceneRoot; if it didn't, it's a one-minute fix:
        if 'DefaultSceneRoot' in comps(lb): log.append('  MANUAL: BP_SeveredLimb337: drag Body onto DefaultSceneRoot so Body is the root')
        body.set_editor_property('capsule_radius', 7.0); body.set_editor_property('capsule_half_height', 20.0)
        body.set_collision_profile_name('NoCollision')
        limb = add(lb, unreal.PoseableMeshComponent, 'Limb', comps(lb)['Body'])
        limb.set_collision_profile_name('NoCollision')
        cap = add(lb, unreal.StaticMeshComponent, 'LimbCap', comps(lb)['Limb']); cap.set_collision_profile_name('NoCollision')
        BEL.compile_blueprint(lb); EAL.save_asset(D3 + '/BP_SeveredLimb337')
    cb = bp_of('BP_WoundCap337', unreal.Actor)
    if cb:
        c = add(cb, unreal.StaticMeshComponent, 'Cap'); c.set_collision_profile_name('NoCollision')
        c.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
        BEL.compile_blueprint(cb); EAL.save_asset(D3 + '/BP_WoundCap337')
    if not DRY:
        gb = unreal.load_asset(D3 + '/BPC_Gore337'); BEL.compile_blueprint(gb); EAL.save_asset(D3 + '/BPC_Gore337')
    log.append('Next: README step 2 (BPVar lines + 3 graph pastes), then --finish')
else:
    g = unreal.load_asset(D3 + '/BPC_Gore337'); z = unreal.load_asset(ZOMBIE)
    if not g or not z: raise SystemExit('missing BPC_Gore337 or BP_Zombie')
    cdo = unreal.get_default_object(g.generated_class())
    caps = [unreal.load_asset(D3 + '/WoundCaps/SM_WoundCap_%s_337' % p) for p in ('Forearm', 'UpperArm', 'Calf', 'Neck')]
    log.append('BPC_Gore337 Caps = %s, DecalMat = MI_BloodDecal_337' % [c.get_name() if c else None for c in caps])
    if not DRY:
        cdo.set_editor_property('Caps', caps); cdo.set_editor_property('DecalMat', unreal.load_asset(D3 + '/MI_BloodDecal_337'))
        BEL.compile_blueprint(g); EAL.save_asset(D3 + '/BPC_Gore337')
    log.append('BP_Zombie: + component Gore (BPC_Gore337)')
    if not DRY:
        add(z, g.generated_class(), 'Gore'); BEL.compile_blueprint(z); EAL.save_asset(ZOMBIE)
    log.append('Next: README step 4 (BP_Zombie hook merge)')

out = '\n'.join(log); unreal.log(out); print(out)
