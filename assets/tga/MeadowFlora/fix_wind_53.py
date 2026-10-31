# #356 follow-up (TGA, 2026-10-31): wire the meadow wind in UE 5.3, where Python has no MP_WORLD_POSITION_OFFSET.
# Run in the editor:   py "<repo>/assets/tga/MeadowFlora/fix_wind_53.py"      DRY_RUN = True only reports what it would do.
# Builds NEW parents M_MeadowFloraWind (opaque) and M_MeadowCardsWind (masked) with the wind on World Position Offset
# (route A / B / C from meadow_mat53.py; the log says which), used_with_instanced_static_meshes on, then re-parents
# MI_MeadowFlora / MI_MeadowCards to them. Meshes and the #351 scatter keep pointing at the MIs, so nothing else changes.
# Undo: re-parent the two MIs back to M_MeadowFlora / M_MeadowCards and delete the two *Wind materials.
import os, sys
import unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meadow_mat53

DRY_RUN = True
DST = '/Game/CastleDefender/Environment/Flora/Meadow'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
log = lambda m: unreal.log('[wind356%s] %s' % (' DRY' if DRY_RUN else '', m))
mp = [n for n in dir(unreal.MaterialProperty) if n.startswith('MP_')]
log('MaterialProperty in this build: %s' % mp)
route = 'A' if any('WORLD' in n and 'POSITION' in n for n in mp) else 'B' if any('MATERIAL' in n and 'ATTRIBUTES' in n for n in mp) else 'C (one manual wire)'
for mi in ('MI_MeadowFlora', 'MI_MeadowCards'):
    if not EAL.does_asset_exist('%s/%s' % (DST, mi)): log('WARNING %s/%s missing: run import_flora_meadow_ue.py first' % (DST, mi))
if DRY_RUN:
    log('would build M_MeadowFloraWind + M_MeadowCardsWind via route %s and re-parent MI_MeadowFlora / MI_MeadowCards' % route); raise SystemExit
for par, atlas, masked, mi in (('M_MeadowFloraWind', 'T_MeadowFlora', False, 'MI_MeadowFlora'), ('M_MeadowCardsWind', 'T_MeadowCards', True, 'MI_MeadowCards')):
    m, r = meadow_mat53.build(DST, par, atlas, masked, log)
    inst = unreal.load_asset('%s/%s' % (DST, mi)); MEL.set_material_instance_parent(inst, m); EAL.save_asset('%s/%s' % (DST, mi))
    log('%s built (route %s), %s re-parented' % (par, r, mi))
lp2 = [a.split('.')[0] for a in EAL.list_assets('/Game/CastleDefender/Environment/Flora', recursive=True) if a.split('.')[0].endswith('/M_LP2Foliage')]
for p in ['%s/M_MeadowFlora' % DST, '%s/M_MeadowCards' % DST] + lp2:
    if EAL.does_asset_exist(p):
        o = unreal.load_asset(p); o.set_editor_property('used_with_instanced_static_meshes', True); MEL.recompile_material(o); EAL.save_asset(p)
log('done. Check: Play, stand by a hawthorn and a poppy patch: stems sway from the base, leaves flutter; set WindIntensity on the MIs if too strong.')
