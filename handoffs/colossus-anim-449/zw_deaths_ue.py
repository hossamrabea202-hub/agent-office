# Walker deaths (#519 stage 4) - Unreal editor script (Python), adjustedfilm (Claude) 2026-11-06. Run AFTER zw_walkers_ue.py (#521).
#   py ".../colossus-anim-449/zw_deaths_ue.py" --dry-run    report; changes nothing
#   py ".../colossus-anim-449/zw_deaths_ue.py"              install (about 20 s): imports + creates the 4 montages. No existing asset is touched.
# Why: BP_Zombie picks one of 12 death montages; 11 of them wrap the blob-rise clips ZA_Burst_A-K and ZA_Laying_Idle_B
# (a zombie "dies" by playing its spawn animation). The raw burst clips stay as they are (the wave manager plays them
# for the blob rise). The BP paste (manifest_zd519.json) then points the 11 picks at the 4 new montages.
# What "install" does:
#   1. imports ZW_Death_Back / Side / Crumple (fbx/, skeleton animation only) into Zombie/Anims_Walkers/
#   2. creates Zombie/Anim/Death/AM_ZDeath_ZW_Back / _Side / _Crumple / _Collapse (DefaultSlot, blend 0.25 in/out, 2.97 s)
# Rollback: nothing to restore here (new assets only); the paste's rollback is the backup EventGraph export.
import unreal, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:] + os.environ.get('ZD_ARGS', '').split()
DRY = '--dry-run' in args
R = '/Game/CastleDefender/Characters/Enemies/Zombie'
ZW = R + '/Anims_Walkers'; DEATH = R + '/Anim/Death'
EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
CLIPS = ['ZW_Death_Back', 'ZW_Death_Side', 'ZW_Death_Crumple', 'ZW_Death_Collapse']
NEW = {'Back': 'ZW_Death_Back', 'Side': 'ZW_Death_Side', 'Crumple': 'ZW_Death_Crumple', 'Collapse': 'ZW_Death_Collapse'}
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print('ZD519', s); log.append(s)
def montage_of(path):
    m = unreal.load_asset(path); t = m.get_editor_property('slot_anim_tracks')[0].get_editor_property('anim_track').get_editor_property('anim_segments')[0]
    return '%s (%.2f s, %s, slot %s)' % (path.split('/')[-1], m.get_play_length(), t.get_editor_property('anim_reference').get_name(),
                                          m.get_editor_property('slot_anim_tracks')[0].get_editor_property('slot_name'))
say('mode', 'DRY-RUN' if DRY else 'INSTALL')

# 1. import
missing = [c for c in CLIPS if not EAL.does_asset_exist(ZW + '/' + c) and not os.path.exists(os.path.join(HERE, 'fbx', c + '.fbx'))]
if missing: raise SystemExit('ZD519 missing FBX: %s (git pull?)' % missing)
skel = unreal.load_asset(R + '/SK_Zombie_Skeleton'); tasks = []
for c in CLIPS:
    if EAL.does_asset_exist(ZW + '/' + c) and c == 'ZW_Death_Collapse': say('have', c); continue
    say('import', c, '(replace)' if EAL.does_asset_exist(ZW + '/' + c) else '(new)')
    if DRY: continue
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data')
    ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for k, v in [('use_default_sample_rate', False), ('custom_sample_rate', 30)]:
        try: ad.set_editor_property(k, v)
        except Exception: pass
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(HERE, 'fbx', c + '.fbx')); t.set_editor_property('destination_path', ZW)
    t.set_editor_property('destination_name', c); t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True); t.set_editor_property('save', True); t.set_editor_property('options', ui)
    tasks.append(t)
if tasks:
    AT.import_asset_tasks(tasks)
    bad = [c for c in CLIPS if not EAL.does_asset_exist(ZW + '/' + c)]
    if bad: raise SystemExit('ZD519 import failed for %s - nothing else was changed' % bad)

# 2. the 4 new montages (never overwritten: delete by hand to rebuild)
for key, seq in NEW.items():
    p = DEATH + '/AM_ZDeath_ZW_' + key
    if EAL.does_asset_exist(p): say('have montage', montage_of(p)); continue
    say('create montage AM_ZDeath_ZW_%s from %s' % (key, seq))
    if DRY: continue
    s = unreal.load_asset(ZW + '/' + seq)
    f = unreal.AnimMontageFactory(); f.set_editor_property('target_skeleton', s.get_editor_property('skeleton')); f.set_editor_property('source_animation', s)
    m = AT.create_asset('AM_ZDeath_ZW_' + key, DEATH, unreal.AnimMontage, f); EAL.save_loaded_asset(m)
    say('  ->', montage_of(p))
json.dump({'log': log}, open(os.path.join(HERE, 'deaths_install_report.json'), 'w'), indent=1)
say('DONE', 'dry-run, nothing changed' if DRY else 'installed (new assets only). NEXT: the BP_Zombie paste, README stage 4.')
