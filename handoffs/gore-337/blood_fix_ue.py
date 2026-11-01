# Blood VFX fix (i5 core, 2026-11-01): finish #337 in two small steps. UE 5.8 Python, safe to re-run.
#   py "<repo>/handoffs/gore-337/blood_fix_ue.py" --decal [--dry-run]   BPC_Gore337.DecalMat = MI_BloodDecal_337 (was empty:
#                                                                        the real splats never spawned)
#   py ".../blood_fix_ue.py" --copy [--dry-run]    BP_BloodBurst_337 = a copy of BP_BloodBurst whose sphere "chunks" use the
#                                                   dark wet droplet material M_BloodParticle_337 at droplet size (x0.25)
#   py ".../blood_fix_ue.py" --swap [--dry-run]    AFTER the owner's OK: the same change on BP_BloodBurst itself
#                                                   (backup BP_BloodBurst_BACKUP337 first, so nothing that spawns it changes)
#   py ".../blood_fix_ue.py" --revert               BP_BloodBurst back from the backup
import sys, unreal
A = sys.argv[1:]
DRY = '--dry-run' in A
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
V, B3 = '/Game/CastleDefender/VFX', '/Game/CastleDefender/VFX/Blood337'
BURST, COPY, BACK = V + '/BP_BloodBurst', V + '/BP_BloodBurst_337', V + '/BP_BloodBurst_BACKUP337'
DROP, SCALE = B3 + '/M_BloodDroplet_Mesh_337', 0.25   # mesh material (blood_droplet_mat_ue.py); the _Particle one renders white on meshes
log = ['blood fix %s%s' % (' '.join(a for a in A if a != '--dry-run'), ' (DRY RUN)' if DRY else '')]


def dropletize(path):
    """sphere chunk components of a BloodBurst Blueprint -> droplet material, x SCALE."""
    bp = unreal.load_asset(path); n = 0; seen = set()
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        c = LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))
        if isinstance(c, unreal.StaticMeshComponent) and c.get_name() not in seen:   # 5.8 lists each template twice
            seen.add(c.get_name())
            m = c.get_editor_property('static_mesh')
            log.append('  %s: mesh %s, mats %s, scale %s' % (c.get_name(), m.get_name() if m else None,
                       [x.get_name() if x else None for x in c.get_editor_property('override_materials')], c.get_editor_property('relative_scale3d')))
            if DRY: continue
            c.set_editor_property('override_materials', [unreal.load_asset(DROP)])
            c.set_editor_property('relative_scale3d', c.get_editor_property('relative_scale3d') * SCALE); n += 1
    if not DRY: BEL.compile_blueprint(bp); EAL.save_asset(path)
    log.append('  %d chunk component(s) changed on %s' % (n, path.split('/')[-1]))


if '--decal' in A:
    bp = unreal.load_asset(B3 + '/BPC_Gore337'); cdo = unreal.get_default_object(bp.generated_class())
    cur = cdo.get_editor_property('DecalMat')
    log.append('BPC_Gore337.DecalMat now %s' % (cur.get_name() if cur else None))
    if cur is None and not DRY:
        cdo.set_editor_property('DecalMat', unreal.load_asset(B3 + '/MI_BloodDecal_337'))
        BEL.compile_blueprint(bp); EAL.save_asset(B3 + '/BPC_Gore337'); log.append('  -> MI_BloodDecal_337, compiled, saved')
elif '--copy' in A:
    log.append('copy %s -> %s' % (BURST, COPY))
    if not DRY:
        if not EAL.does_asset_exist(COPY): EAL.duplicate_asset(BURST, COPY)
        else: log.append('  (copy exists: re-applied on it)')
    dropletize(COPY if not DRY else BURST)
    log.append('Lookdev: drop BP_BloodBurst and BP_BloodBurst_337 side by side (or spawn in PIE), screenshot for the owner.')
elif '--swap' in A:
    log.append('backup %s -> %s, then dropletize %s' % (BURST, BACK, BURST))
    if not DRY and not EAL.does_asset_exist(BACK): EAL.duplicate_asset(BURST, BACK)
    dropletize(BURST)
elif '--revert' in A:
    if not EAL.does_asset_exist(BACK): log.append('no backup: nothing to revert')
    else:
        bb = unreal.load_asset(BACK)
        for h in SDS.k2_gather_subobject_data_for_blueprint(bb):
            c = LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))
            if isinstance(c, unreal.StaticMeshComponent):
                mats, sc = c.get_editor_property('override_materials'), c.get_editor_property('relative_scale3d')
                log.append('  restore %s mats %s scale %s' % (c.get_name(), [x.get_name() if x else None for x in mats], sc))
                if not DRY:
                    live = unreal.load_asset(BURST)
                    for h2 in SDS.k2_gather_subobject_data_for_blueprint(live):
                        c2 = LIB.get_object(SDS.k2_find_subobject_data_from_handle(h2))
                        if isinstance(c2, unreal.StaticMeshComponent) and c2.get_name() == c.get_name():
                            c2.set_editor_property('override_materials', mats); c2.set_editor_property('relative_scale3d', sc)
        if not DRY: BEL.compile_blueprint(unreal.load_asset(BURST)); EAL.save_asset(BURST)
else:
    log.append('pick a mode: --decal, --copy, --swap or --revert')
out = '\n'.join(log); unreal.log(out); print(out)
