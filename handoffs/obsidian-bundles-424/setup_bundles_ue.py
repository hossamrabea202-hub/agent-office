# #424 Obsidian set as 4 BUNDLES (i9 helper, 2026-11-02). Editor script for UE 5.8.4, safe to re-run.
#   py "<repo>/handoffs/obsidian-bundles-424/setup_bundles_ue.py"
# DRY_RUN = True (default): changes nothing. Checks every asset / file / variable it needs and writes setup_bundles.txt.
# DRY_RUN = False:
#   1. backups (once): BPC_ObsidianSet_v2_backup, BPC_VesnaTrade_v2_backup (next to the originals)
#   2. imports T_VT_Atlas_424, T_VT_Frame_424, T_VT_Bundles_424 to /Game/CastleDefender/UI/Trade/Vesna (UI settings)
#   3. BPC_ObsidianSet: adds the bundle variables and sets the data (BundleMask, PartPrice, PartBundle, TierAt, TierDR, ...)
#   4. BPC_VesnaTrade: adds BundleTex + IconFromBundle and sets the 7 list rows (4 bundles + 3 shields), new atlas/frame
# Then paste RIGHT AWAY (README steps 3-4): between this script and the two pastes the old graphs read the new data wrong.
# Touches no heavy Blueprint (hero, BP_ZombieHUD, BP_SkillTreeHUD, BP_BarracksHUD, BP_ArmoryHUD are not opened).
import os, json, unreal

DRY_RUN = True

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'obsidian-bundles-424')
TEX_DIR = os.path.join(HERE, 'textures')
DEST = '/Game/CastleDefender/UI/Trade/Vesna'
SETBP = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
TRADE = '/Game/CastleDefender/Gameplay/Castle/BPC_VesnaTrade'
KIT = '/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit'
BACKUPS = {SETBP: SETBP + '_v2_backup', TRADE: TRADE + '_v2_backup'}
NEW_TEX = ['T_VT_Atlas_424', 'T_VT_Frame_424', 'T_VT_Bundles_424']
OLD_TEX = ['T_VT_Icons', 'T_VT_Turn_Chest', 'T_VT_Turn_Gauntlets', 'T_VT_Turn_Shins', 'T_VT_Turn_RoundShield', 'T_VT_Turn_HeaterShield']
GRAPHS = ['BPC_ObsidianSet_v3_graph.txt', 'BPC_VesnaTrade_bd_graph.txt']

# ---------------------------------------------------------------- the bundle data (owner decision 2026-11-02, card #424)
# piece ids (obsidian-set-v2/pieces.csv); bit = id - 10
BUNDLES = [('Obsidian Helm', [15]), ('Obsidian Torso', [10, 11, 16, 20]), ('Obsidian Gauntlets', [12, 17]), ('Obsidian Legs', [13, 14, 18, 19])]
# Decision (#424): part price = 10 gold per DEF point, anchored on the classic rack's cuirass (450 g for +45 DEF).
# Bundle price = sum of its parts = Helm 150, Torso 690, Gauntlets 160, Legs 400 (whole set 1,400). Tune PartPrice here
# or on BPC_ObsidianSet's defaults; the shop shows the price of the parts the player doesn't own yet.
DEF = {10: 45, 11: 12, 12: 8, 13: 8, 14: 10, 15: 15, 16: 8, 17: 8, 18: 10, 19: 12, 20: 4}
PART_PRICE = [DEF[10 + i] * 10 for i in range(11)]
PART_BUNDLE = [next(k for k, (_, ids) in enumerate(BUNDLES) if 10 + i in ids) for i in range(11)]
BUNDLE_MASK = [sum(1 << (i - 10) for i in ids) for _, ids in BUNDLES]
BUNDLE_COST = [sum(PART_PRICE[i - 10] for i in ids) for _, ids in BUNDLES]
# Decision (#424): set tiers by bundles worn 1/2/3/4 -> -3 / -6 / -10 (+ ember shockwave) / -15 % (4/4 = Sovereign)
TIER_AT = [1, 2, 3, 4]
TIER_DR = [0.03, 0.06, 0.10, 0.15]

EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
D = json.load(open(os.path.join(HERE, 'trade_bd_data.json')))['data']
log = ['DRY_RUN = %s' % DRY_RUN,
       'bundles: %s' % ', '.join('%s mask %d cost %d' % (n, m, c) for (n, _), m, c in zip(BUNDLES, BUNDLE_MASK, BUNDLE_COST)),
       'masks cover all 11 parts once: %s' % (sum(BUNDLE_MASK) == 2047 and all(a & b == 0 for i, a in enumerate(BUNDLE_MASK) for b in BUNDLE_MASK[i + 1:])),
       'list rows: %s' % D['PieceIds']]
missing = []
def chk(ok, what):
    log.append('%-8s %s' % ('ok' if ok else 'MISSING', what))
    if not ok: missing.append(what)
for n in NEW_TEX: chk(os.path.exists(os.path.join(TEX_DIR, n + '.png')), os.path.join(TEX_DIR, n + '.png'))
for g in GRAPHS: chk(os.path.exists(os.path.join(HERE, g)), os.path.join(HERE, g))
for p in (SETBP, TRADE, KIT): chk(EAL.does_asset_exist(p), p)
for n in OLD_TEX: chk(EAL.does_asset_exist('%s/%s' % (DEST, n)), '%s/%s' % (DEST, n))

def probe(path, names):
    """UE 5.8: Blueprint.new_variables is not readable from Python (#380). Probe the class default object instead."""
    if not EAL.does_asset_exist(path): return set()
    bp = unreal.load_asset(path); gc = bp.generated_class(); cdo = unreal.get_default_object(gc) if gc else None
    have = set()
    for n in names:
        try:
            cdo.get_editor_property(n); have.add(n)
        except Exception:
            pass
    return have
NEED_SET = ['ObsOwned', 'ObsWorn', 'WornEff', 'AvailMask', 'TierAt', 'TierDR', 'Tier', 'NextPrice', 'ShieldLevel']
NEED_TRADE = ['Set', 'Kit', 'PieceIds', 'PieceDef', 'NameUV', 'DefUV', 'TitleUV', 'TagUV', 'IconUV', 'IconFromAtlas', 'TurnTex', 'ShieldUV',
              'AtlasTex', 'FrameTex', 'IconsTex', 'Sel', 'Scroll']
h = probe(SETBP, NEED_SET); [chk(n in h, 'BPC_ObsidianSet.' + n) for n in NEED_SET]
h = probe(TRADE, NEED_TRADE); [chk(n in h, 'BPC_VesnaTrade.' + n) for n in NEED_TRADE]

def finish(msg):
    out = '#424 Obsidian bundles setup\n' + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'setup_bundles.txt'), 'w', encoding='utf-8').write(out); unreal.log(out)

def add_vars(bp, path, new):
    have = probe(path, list(new))
    for n, t in new.items():
        if n not in have:
            if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add %s to %s' % (n, path))
            log.append('  + %s.%s' % (path.rsplit('/', 1)[1], n))
    BEL.compile_blueprint(bp)

def apply():
    # 1. backups
    for src, dst in BACKUPS.items():
        if not EAL.does_asset_exist(dst):
            EAL.duplicate_asset(src, dst); EAL.save_asset(dst); log.append('backup: ' + dst)
        else:
            log.append('backup already there: ' + dst)
    # 2. textures
    tasks = []
    for n in NEW_TEX:
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(TEX_DIR, n + '.png'))
        t.set_editor_property('destination_path', DEST); t.set_editor_property('destination_name', n)
        t.set_editor_property('replace_existing', True); t.set_editor_property('automated', True); t.set_editor_property('save', False)
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for n in NEW_TEX:
        tx = unreal.load_asset('%s/%s' % (DEST, n)); tx.modify()
        tx.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tx.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tx.set_editor_property('never_stream', True); tx.set_editor_property('srgb', True)
        tx.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); tx.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
        tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        EAL.save_asset('%s/%s' % (DEST, n)); log.append('texture %s/%s' % (DEST, n))
    I, R, Sx = BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('real'), BEL.get_basic_type_by_name('string')
    Bo = BEL.get_basic_type_by_name('bool')
    ARR = BEL.get_array_type
    # 3. BPC_ObsidianSet
    sb = unreal.load_asset(SETBP)
    add_vars(sb, SETBP, {'BundleMask': ARR(I), 'PartPrice': ARR(I), 'PartBundle': ARR(I), 'BundleCost': ARR(I), 'BundleNames': ARR(Sx),
                         'BundleOwned': I, 'BundleWorn': I, 'BundleAvail': I, 'BundleCount': I})
    cdo = unreal.get_default_object(sb.generated_class())
    for n, v in (('BundleMask', BUNDLE_MASK), ('PartPrice', PART_PRICE), ('PartBundle', PART_BUNDLE), ('BundleCost', BUNDLE_COST),
                 ('BundleNames', [n for n, _ in BUNDLES]), ('BundleOwned', 0), ('BundleWorn', 0), ('BundleAvail', 0), ('BundleCount', 0),
                 ('TierAt', TIER_AT), ('TierDR', TIER_DR)):
        cdo.set_editor_property(n, v)
    EAL.save_asset(SETBP)
    log.append('BPC_ObsidianSet: BundleMask %s, PartPrice %s, PartBundle %s, TierAt %s, TierDR %s' % (BUNDLE_MASK, PART_PRICE, PART_BUNDLE, TIER_AT, TIER_DR))
    # 4. BPC_VesnaTrade
    tb = unreal.load_asset(TRADE)
    add_vars(tb, TRADE, {'BundleTex': BEL.get_object_reference_type(unreal.Texture2D), 'IconFromBundle': ARR(Bo)})
    cdo = unreal.get_default_object(tb.generated_class())
    lc = lambda q: unreal.LinearColor(*q)
    for n in ('PieceIds', 'PieceDef', 'IconFromAtlas', 'IconFromBundle'): cdo.set_editor_property(n, D[n])
    for n in ('NameUV', 'DefUV', 'TitleUV', 'TagUV', 'IconUV'): cdo.set_editor_property(n, [lc(q) for q in D[n]])
    cdo.set_editor_property('ShieldUV', lc(D['ShieldUV']))
    cdo.set_editor_property('TurnTex', [unreal.load_asset('%s/%s' % (DEST, q)) if q else None for q in D['TurnTex']])
    cdo.set_editor_property('AtlasTex', unreal.load_asset(DEST + '/T_VT_Atlas_424'))
    cdo.set_editor_property('FrameTex', unreal.load_asset(DEST + '/T_VT_Frame_424'))
    cdo.set_editor_property('BundleTex', unreal.load_asset(DEST + '/T_VT_Bundles_424'))
    cdo.set_editor_property('Sel', 1); cdo.set_editor_property('Scroll', 0)
    EAL.save_asset(TRADE)
    log.append('BPC_VesnaTrade: %d rows (4 bundles + 3 shields), atlas/frame/bundle textures set' % len(D['PieceIds']))
    finish('Next, right away: paste BPC_ObsidianSet_v3_graph.txt into BPC_ObsidianSet, compile, save; then\n'
           'BPC_VesnaTrade_bd_graph.txt into BPC_VesnaTrade, compile, save (README steps 3-4).')

if DRY_RUN:
    finish('DRY RUN only. If nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else 'STOP: MISSING above. Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()
