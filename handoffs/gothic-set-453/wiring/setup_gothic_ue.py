# #453 Landshut Gothic as the 2nd set on BPC_ObsidianSet (i5, 2026-11-03). Editor script for UE 5.8.4, safe to re-run.
#   py "<repo>/handoffs/gothic-set-453/wiring/setup_gothic_ue.py"            (DRY_RUN = True: changes nothing)
# DRY_RUN = False:
#   1. backup (once): BPC_ObsidianSet_v3_backup
#   2. adds GothicCount, GTier (int) and KnightCover2 (int array) to BPC_ObsidianSet
#   3. extends the v3 data from 4 bundles / 11 parts to 8 bundles / 22 parts (only if it is still the v3 size):
#      BundleMask, BundleNames, BundleCost [8]; PartPrice, PartBundle [22]; TierDR [8]; KnightCover2 = KnightCover << 11
# Then paste BPC_ObsidianSet_v4_graph.txt right away (README). AvailMask is NOT touched: Gothic parts become buyable
# only when their meshes + hero components exist (setup_gothic_pieces step, after TGA1's models); until then the
# Gothic rows show FORGING. The v3 graph keeps working on the longer arrays in between (no out-of-range reads).
import os, unreal

DRY_RUN = True

SETBP = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
BACKUP = SETBP + '_v3_backup'
GRAPH = 'BPC_ObsidianSet_v4_graph.txt'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = ''
for h in (HERE, r'C:\Users\hossa\Documents\agent-office\handoffs\gothic-set-453\wiring',      # i9 Master checkout
          r'C:\Users\hossam.rabea\agent-office\handoffs\gothic-set-453\wiring'):               # i5 (inbox copies run elsewhere)
    if h and os.path.exists(os.path.join(h, GRAPH)): HERE = h; break

# ---------------------------------------------------------------- the Gothic data (card #453, RESEARCH.md)
# Gothic part = Obsidian part + 11 (ids 21..31, bit = id - 10 = 11..21), same bundles shifted by 4.
# Decision (#453): part price = 80 % of the Obsidian part (plain steel, no ember magic); DEF is the Gothic column.
GOTHIC_NAMES = ['Gothic Helm', 'Gothic Torso', 'Gothic Gauntlets', 'Gothic Legs']
GOTHIC_DR = [0.02, 0.05, 0.08, 0.12]        # bundles worn 1/2/3/4 (Obsidian: 0.03/0.06/0.10/0.15)

EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
log, missing = ['DRY_RUN = %s' % DRY_RUN], []
def chk(ok, what):
    log.append('%-8s %s' % ('ok' if ok else 'MISSING', what))
    if not ok: missing.append(what)

def probe(path, names):
    """UE 5.8: Blueprint.new_variables is not readable from Python (#380). Probe the class default object instead."""
    bp = unreal.load_asset(path); cdo = unreal.get_default_object(bp.generated_class()); have = set()
    for n in names:
        try: cdo.get_editor_property(n); have.add(n)
        except Exception: pass
    return have

chk(EAL.does_asset_exist(SETBP), SETBP)
chk(os.path.exists(os.path.join(HERE, GRAPH)), os.path.join(HERE, GRAPH))
NEED = ['ObsOwned', 'ObsWorn', 'WornEff', 'AvailMask', 'KnightCover', 'BundleMask', 'BundleNames', 'BundleCost', 'PartPrice', 'PartBundle',
        'TierAt', 'TierDR', 'BundleCount', 'BundleWorn']
have = probe(SETBP, NEED + ['GothicCount', 'GTier', 'KnightCover2']) if EAL.does_asset_exist(SETBP) else set()
for n in NEED: chk(n in have, 'BPC_ObsidianSet.' + n + ' (v3)')

new = {}
if not missing:
    cdo = unreal.get_default_object(unreal.load_asset(SETBP).generated_class())
    g = lambda n: list(cdo.get_editor_property(n))
    bm, pp, pb, bc, tdr, kc = g('BundleMask'), g('PartPrice'), g('PartBundle'), g('BundleCost'), g('TierDR'), g('KnightCover')
    names = [str(x) for x in g('BundleNames')]
    log.append('now: BundleMask %s PartPrice %s PartBundle %s TierDR %s KnightCover %s' % (bm, pp, pb, [round(x, 3) for x in tdr], kc))
    if len(bm) == 8 and len(pp) == 22:
        log.append('already v4 size (8 bundles / 22 parts): data left as it is')
    elif len(bm) == 4 and len(pp) == 11 and len(tdr) == 4:
        gp = [int(round(p * 0.8)) for p in pp]
        new = {'BundleMask': bm + [m << 11 for m in bm], 'BundleNames': names + GOTHIC_NAMES,
               'PartPrice': pp + gp, 'PartBundle': pb + [k + 4 for k in pb],
               'BundleCost': bc + [sum(gp[i] for i in range(11) if pb[i] == k) for k in range(4)],
               'TierDR': tdr + GOTHIC_DR, 'KnightCover2': [c << 11 for c in kc]}
        allm = new['BundleMask']
        log.append('masks cover all 22 parts once: %s' % (sum(allm) == (1 << 22) - 1 and all(a & b == 0 for i, a in enumerate(allm) for b in allm[i + 1:])))
        for k, v in new.items(): log.append('  -> %s = %s' % (k, v))
    else:
        chk(False, 'BPC_ObsidianSet data is neither v3 (4/11) nor v4 (8/22) size: %d bundles, %d parts' % (len(bm), len(pp)))

def finish(msg):
    out = '#453 Gothic set setup\n' + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'setup_gothic.txt'), 'w', encoding='utf-8').write(out); unreal.log(out)

def apply():
    if not EAL.does_asset_exist(BACKUP):
        EAL.duplicate_asset(SETBP, BACKUP); EAL.save_asset(BACKUP); log.append('backup: ' + BACKUP)
    else:
        log.append('backup already there: ' + BACKUP)
    sb = unreal.load_asset(SETBP)
    I = BEL.get_basic_type_by_name('int')
    for n, t in (('GothicCount', I), ('GTier', I), ('KnightCover2', BEL.get_array_type(I))):
        if n not in have:
            if not BEL.add_member_variable(sb, n, t): raise RuntimeError('could not add ' + n)
            log.append('  + BPC_ObsidianSet.' + n)
    BEL.compile_blueprint(sb)
    cdo = unreal.get_default_object(sb.generated_class())
    for n, v in new.items(): cdo.set_editor_property(n, v)
    EAL.save_asset(SETBP)
    finish('Next, right away: paste %s into BPC_ObsidianSet (Ctrl+A, BackSpace, Ctrl+V), Refresh All Nodes, compile, save.' % GRAPH)

if DRY_RUN:
    finish('DRY RUN only. If nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else 'STOP: MISSING above. Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()
