# #418 shop v2, Vesna's Trade with shields + the click fix (TGA). Editor script, safe to re-run. UE 5.8.
#   py "<repo>/handoffs/shop-v2-418/trade/setup_trade_v2_ue.py"
# Run AFTER shields/setup_shieldkit_ue.py (BPC_ShieldKit must exist) and right BEFORE pasting BPC_VesnaTrade_graph.txt (v2):
# the new atlas moves every cell, so the v1 graph draws wrong between this script and the paste.
# DRY_RUN = True (default): changes nothing, checks the files and BPC_ShieldKit, writes setup_trade_v2.txt.
# DRY_RUN = False:
#   1. backup: duplicates BPC_VesnaTrade to BPC_VesnaTrade_v1_backup (only once)
#   2. imports T_VT_Atlas_418 (new name: the v1 T_VT_Atlas stays for the backup), T_VT_Icons (11 icons) and the 6 new turntables
#   3. adds Kit (BPC_ShieldKit), PrevDown, ModeUI to BPC_VesnaTrade and sets every table default from trade_data.json (14 rows)
import os, json, unreal

DRY_RUN = True

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'shop-v2-418', 'trade')
TEX_DIR = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'tga', 'VesnaTrade', 'textures'))
DEST = '/Game/CastleDefender/UI/Trade/Vesna'
TRADE = '/Game/CastleDefender/Gameplay/Castle/BPC_VesnaTrade'
BACKUP = '/Game/CastleDefender/Gameplay/Castle/BPC_VesnaTrade_v1_backup'
KIT = '/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit'
TEXTURES = ['T_VT_Atlas_418', 'T_VT_Icons'] + ['T_VT_Turn_' + f for f in ('Forearms', 'UpperArms', 'Waist', 'Thighs', 'HeaterShield', 'RoundShield')]
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
D = json.load(open(os.path.join(HERE, 'trade_data.json')))
log = ['DRY_RUN = %s' % DRY_RUN]
missing = []
for n in TEXTURES:
    f = os.path.join(TEX_DIR, n + '.png'); ok = os.path.exists(f); log.append('%-8s %s' % ('ok' if ok else 'MISSING', f))
    if not ok: missing.append(f)
for p in (TRADE, KIT):
    ok = EAL.does_asset_exist(p); log.append('%-8s %s' % ('ok' if ok else 'MISSING', p))
    if not ok: missing.append(p)

def finish(msg):
    out = '#418 Vesna trade v2 setup\n' + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'setup_trade_v2.txt'), 'w').write(out); unreal.log(out)

def var_names(bp, wanted):
    BEL.compile_blueprint(bp); have = set()
    gc = bp.generated_class(); cdo = unreal.get_default_object(gc) if gc else None
    for n in wanted:
        try:
            cdo.get_editor_property(n); have.add(n)
        except Exception:
            pass
    return have

def apply():
    if not EAL.does_asset_exist(BACKUP):
        EAL.duplicate_asset(TRADE, BACKUP); EAL.save_asset(BACKUP); log.append('backup: ' + BACKUP)
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
        EAL.save_asset('%s/%s' % (DEST, n)); log.append('texture %s' % n)
    bp = unreal.load_asset(TRADE)
    Bo = BEL.get_basic_type_by_name('bool')
    new = {'Kit': BEL.get_object_reference_type(unreal.load_asset(KIT).generated_class()), 'PrevDown': Bo, 'ModeUI': Bo}
    have = var_names(bp, list(new))
    for n, t in new.items():
        if n not in have:
            if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add ' + n)
            log.append('  + BPC_VesnaTrade.%s' % n)
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    dd = D['data']; lc = lambda q: unreal.LinearColor(*q)
    for n in ('PieceIds', 'PieceDef', 'SlotIds', 'SlotRow', 'IconFromAtlas'): cdo.set_editor_property(n, dd[n])
    for n in ('NameUV', 'DefUV', 'TitleUV', 'TagUV', 'IconUV'): cdo.set_editor_property(n, [lc(q) for q in dd[n]])
    cdo.set_editor_property('ShieldUV', lc(dd['ShieldUV']))
    cdo.set_editor_property('TurnTex', [unreal.load_asset('%s/%s' % (DEST, q)) if q else None for q in dd['TurnTex']])
    cdo.set_editor_property('AtlasTex', unreal.load_asset(DEST + '/T_VT_Atlas_418')); cdo.set_editor_property('IconsTex', unreal.load_asset(DEST + '/T_VT_Icons'))
    EAL.save_asset(TRADE)
    log.append('BPC_VesnaTrade defaults: %d rows (11 set pieces + 3 shields)' % len(dd['PieceIds']))
    finish('Next: paste trade/BPC_VesnaTrade_graph.txt over BPC_VesnaTrade\'s EventGraph (select all, delete, paste), Compile, Save.')

if DRY_RUN:
    finish('DRY RUN only. If nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else 'STOP: MISSING above. Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()
