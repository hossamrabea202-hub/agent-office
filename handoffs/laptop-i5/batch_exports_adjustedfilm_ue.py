# ONE read-only run for all of adjustedfilm's open data requests (2026-10-31). UE 5.3 Python. Writes nothing in the project.
#   py "<repo>/handoffs/laptop-i5/batch_exports_adjustedfilm_ue.py"
# Output: handoffs/exports/adjustedfilm/batch-1031/ -> push it, done. Covers requests:
#   #348 BP_BloodBurst · #342 BP_Zombie (fresh) · #335 BP_ZombieRisen + BP_SoldierSword · #336 BPC_TentacleStrike (+ BP_Cannonball)
#   #326 BP_WallBreachSpot · #343 M_JellyBlob (whole material incl. its Custom node code) · #291 skill-gain pop-up candidates
#   + fresh BP_ThirdPersonCharacter, BPC_Weather, BP_NoticeHUD, BP_ZombieHUD, BPC_MotionFX, BP_FleshBrute for the merges
# Each asset is exported whole as .T3D (the same text as the editor's copy); adjustedfilm cuts the graphs out on the laptop
# (ckw/flatten.py). Also: components of every exported Blueprint, and every asset whose name hints at the skill pop-up.
import os, unreal

try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\laptop-i5'
OUT = os.path.normpath(os.path.join(HERE, '..', 'exports', 'adjustedfilm', 'batch-1031'))
os.makedirs(OUT, exist_ok=True)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
NAMES = ['BP_BloodBurst', 'BP_Zombie', 'BP_ZombieRisen', 'BP_SoldierSword', 'BPC_TentacleStrike', 'BP_Cannonball', 'BP_WallBreachSpot',
         'M_JellyBlob', 'BP_ThirdPersonCharacter', 'BPC_Weather', 'BP_NoticeHUD', 'BP_ZombieHUD', 'BPC_MotionFX', 'BP_FleshBrute']
log = []
everything = AR.get_assets(unreal.ARFilter(package_paths=['/Game'], recursive_paths=True))
by_name = {}
for ad in everything: by_name.setdefault(str(ad.asset_name), []).append(ad)
for n in NAMES:
    hits = [ad for ad in by_name.get(n, []) if '/Game/' in str(ad.package_name)]
    if not hits: log.append('MISSING %s' % n); continue
    ad = hits[0]; obj = ad.get_asset()
    t = unreal.AssetExportTask()
    t.set_editor_property('object', obj); t.set_editor_property('filename', os.path.join(OUT, n + '.T3D'))
    t.set_editor_property('automated', True); t.set_editor_property('prompt', False); t.set_editor_property('replace_identical', True)
    ok = unreal.Exporter.run_asset_export_task(t)
    log.append('%-26s %-6s %s' % (n, 'OK' if ok else 'FAILED', ad.package_name))
    if isinstance(obj, unreal.Blueprint):
        try:
            rows = []
            for h in SDS.k2_gather_subobject_data_for_blueprint(obj):
                d = SDS.k2_find_subobject_data_from_handle(h); c = LIB.get_object(d)
                extra = ''
                for p in ('static_mesh', 'skeletal_mesh', 'template', 'asset', 'anim_class'):
                    try:
                        v = c.get_editor_property(p)
                        if v: extra += ' %s=%s' % (p, v.get_path_name())
                    except Exception: pass
                rows.append('%s (%s)%s' % (LIB.get_variable_name(d), c.get_class().get_name(), extra))
            open(os.path.join(OUT, n + '_components.txt'), 'w').write('\n'.join(rows))
        except Exception as e: log.append('  components of %s: %s' % (n, e))
# #291: what draws the skill-point pop-up? every asset whose name hints at it
keys = ('skill', 'achiev', 'popup', 'pop_up', 'toast', 'levelup', 'level_up', 'gain')
cand = sorted('%s (%s)' % (ad.package_name, ad.asset_class_path.asset_name) for ad in everything
              if any(k in str(ad.asset_name).lower() for k in keys) and '/Game/' in str(ad.package_name))
open(os.path.join(OUT, 'skill_popup_candidates.txt'), 'w').write('\n'.join(cand))
log.append('skill pop-up candidates: %d (skill_popup_candidates.txt)' % len(cand))
open(os.path.join(OUT, '_batch_log.txt'), 'w').write('\n'.join(log))
unreal.log('\n'.join(log)); print('\n'.join(log)); print('Push handoffs/exports/adjustedfilm/batch-1031 and close requests 348 342 335 336 326 343 291.')
