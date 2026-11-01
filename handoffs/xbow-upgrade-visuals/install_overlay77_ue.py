# #77 phase 1 install (i5 core, 2026-11-01): checkking's step 2 done by script. UE 5.8 Python.  [--dry-run]
#   - runs make_M_XbowElectric.py when MI_XbowElectric_Noble doesn't exist yet;
#   - BP_Crossbow (backup BP_Crossbow_BACKUP77 once) and BP_TradeShowcase: every StaticMesh/SkeletalMesh component whose mesh
#     is the Noble crossbow gets Overlay Material = MI_XbowElectric_Noble, the Golden Sovereign one gets ..._Sovereign;
#     compile + save.
import os, sys, unreal
DRY = '--dry-run' in sys.argv
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
D = '/Game/CastleDefender/VFX/XbowUpgrade/'
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/xbow-upgrade-visuals'
log = ['#77 overlay install' + (' (DRY RUN)' if DRY else '')]
if not EAL.does_asset_exist(D + 'MI_XbowElectric_Noble'):
    log.append('MI_XbowElectric_* missing: ' + ('would run make_M_XbowElectric.py' if DRY else 'running make_M_XbowElectric.py'))
    if not DRY: exec(compile(open(HERE + '/make_M_XbowElectric.py', encoding='utf-8').read(), 'make_M_XbowElectric.py', 'exec'), {'__name__': '__main__'})
mi = {k: unreal.load_asset(D + 'MI_XbowElectric_' + k) if EAL.does_asset_exist(D + 'MI_XbowElectric_' + k) else None for k in ('Noble', 'Sovereign')}
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
for bpp in ('/Game/CastleDefender/Gameplay/Crossbow/BP_Crossbow', '/Game/CastleDefender/UI/Trade/BP_TradeShowcase'):
    if not EAL.does_asset_exist(bpp): log.append('no ' + bpp); continue
    bp = unreal.load_asset(bpp); hits = 0
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
        if not isinstance(o, unreal.MeshComponent): continue
        m = o.get_editor_property('static_mesh') if isinstance(o, unreal.StaticMeshComponent) else o.get_editor_property('skeletal_mesh_asset') if isinstance(o, unreal.SkeletalMeshComponent) else None
        nm = (m.get_name() if m else '') + ' ' + o.get_name()
        mn = m.get_name().lower() if m else ''
        k = 'Sovereign' if 'golden_sovereign' in mn else 'Noble' if 'noble_crossbow' in mn or ('crossbow' in mn and 'bolt' not in mn) else None   # crossbow meshes only (not the Obsidian Sovereign chest)
        if not k: continue
        log.append('%s: %s (%s) -> MI_XbowElectric_%s' % (bp.get_name(), o.get_name(), m.get_name() if m else None, k)); hits += 1
        if not DRY and mi[k]: o.set_editor_property('overlay_material', mi[k])
    if hits and not DRY:
        if not EAL.does_asset_exist(bpp + '_BACKUP77'): EAL.duplicate_asset(bpp, bpp + '_BACKUP77'); EAL.save_asset(bpp + '_BACKUP77')
        BEL.compile_blueprint(bp); EAL.save_asset(bpp, only_if_is_dirty=False); log.append('saved ' + bp.get_name())
print('\n'.join(log))
