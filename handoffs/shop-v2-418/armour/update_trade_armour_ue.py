# #418 shop v2, armour step (TGA). Editor script, safe to re-run. UE 5.8. DATA ONLY: no graph is pasted.
#   py "<repo>/handoffs/shop-v2-418/armour/update_trade_armour_ue.py"
# Puts the four TGA Obsidian pieces in Vesna's Trade with their own art:
#   Vambraces (id 17, Forearms), Rerebraces (16, UpperArms), Fauld (18, Waist), Cuisses (19, Thighs).
# Before this (README steps 1-2): import the 4 meshes (their import_*_ue.py) and re-run obsidian-set-v2/setup_set_v2_ue.py,
# which attaches them to the hero (bones from pieces.csv) and adds them to AvailMask, so the rows appear and are wearable.
# DRY_RUN = True (default): changes nothing, checks the meshes, the set's AvailMask bits and the files; writes update_trade_armour.txt.
# DRY_RUN = False: imports T_VT_Turn_Forearms / UpperArms / Waist / Thighs and the new T_VT_Icons (9 icons) into
#   /Game/CastleDefender/UI/Trade/Vesna (same UI settings as #361), then sets BPC_VesnaTrade's IconUV, IconFromAtlas and
#   TurnTex defaults from vesna-trade-361/build/trade_data.json (regenerated for #418). Nothing else changes.
import os, json, unreal

DRY_RUN = True

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'shop-v2-418', 'armour')
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TEX_DIR = os.path.join(ROOT, 'assets', 'tga', 'VesnaTrade', 'textures')
DEST = '/Game/CastleDefender/UI/Trade/Vesna'
TRADE = '/Game/CastleDefender/Gameplay/Castle/BPC_VesnaTrade'
SETC = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
MESHES = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign'
PIECES = {16: 'UpperArms', 17: 'Forearms', 18: 'Waist', 19: 'Thighs'}
TEXTURES = ['T_VT_Icons'] + ['T_VT_Turn_' + f for f in PIECES.values()]
EAL = unreal.EditorAssetLibrary
D = json.load(open(os.path.join(ROOT, 'handoffs', 'vesna-trade-361', 'build', 'trade_data.json')))['data']
log = ['DRY_RUN = %s' % DRY_RUN]
missing = []

for n in TEXTURES:
    f = os.path.join(TEX_DIR, n + '.png'); ok = os.path.exists(f); log.append('%-8s %s' % ('ok' if ok else 'MISSING', f))
    if not ok: missing.append(f)
for p in (TRADE, SETC):
    ok = EAL.does_asset_exist(p); log.append('%-8s %s' % ('ok' if ok else 'MISSING', p))
    if not ok: missing.append(p)
have_mesh = {pid: [a for a in EAL.list_assets(MESHES, recursive=True, include_folder=False) if ('SM_ObsidianSovereign_' + f) in a] for pid, f in PIECES.items()}
for pid, f in PIECES.items():
    log.append('%-8s id %d %s meshes: %s' % ('ok' if have_mesh[pid] else 'TODO', pid, f, [a.split('.')[-1] for a in have_mesh[pid]] or 'not imported yet (README step 1)'))
if EAL.does_asset_exist(SETC):
    cdo = unreal.get_default_object(unreal.load_asset(SETC).generated_class())
    try:
        av = cdo.get_editor_property('AvailMask')
        log.append('AvailMask %d: %s' % (av, {pid: bool(av & (1 << (pid - 10))) for pid in PIECES}))
        if not all(av & (1 << (pid - 10)) for pid in PIECES): log.append('  -> re-run obsidian-set-v2/setup_set_v2_ue.py after the imports (README step 2)')
    except Exception as e:
        log.append('AvailMask not readable: %s' % e)

def finish(msg):
    out = '#418 shop v2, armour step\n' + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'update_trade_armour.txt'), 'w').write(out); unreal.log(out)

def apply():
    tasks = []
    for n in TEXTURES:
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(TEX_DIR, n + '.png'))
        t.set_editor_property('destination_path', DEST); t.set_editor_property('destination_name', n)
        t.set_editor_property('replace_existing', True); t.set_editor_property('automated', True); t.set_editor_property('save', False)
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for n in TEXTURES:
        tx = unreal.load_asset('%s/%s' % (DEST, n)); tx.modify()
        tx.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tx.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tx.set_editor_property('never_stream', True); tx.set_editor_property('srgb', True)
        tx.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); tx.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
        tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        EAL.save_asset('%s/%s' % (DEST, n)); log.append('texture %s %dx%d' % (n, tx.blueprint_get_size_x(), tx.blueprint_get_size_y()))
    bp = unreal.load_asset(TRADE)
    cdo = unreal.get_default_object(bp.generated_class())
    lc = lambda q: unreal.LinearColor(*q)
    cdo.set_editor_property('IconUV', [lc(q) for q in D['IconUV']])
    cdo.set_editor_property('IconFromAtlas', D['IconFromAtlas'])
    cdo.set_editor_property('TurnTex', [unreal.load_asset('%s/%s' % (DEST, q)) if q else None for q in D['TurnTex']])
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_asset(TRADE)
    log.append('BPC_VesnaTrade: IconUV / IconFromAtlas / TurnTex set for %d pieces; turntables %s' % (len(D['PieceIds']), [q for q in D['TurnTex'] if q]))
    finish('Done. Play: Vesna > ARMOUR shows Vambraces, Rerebraces, Fauld and Cuisses with icons and a turning preview.')

if DRY_RUN:
    finish('DRY RUN only. If nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else 'STOP: MISSING above. Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()
