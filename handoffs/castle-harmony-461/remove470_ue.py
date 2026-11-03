# #470 REMOVE the fake crack overlay from the stone base materials (i5, 2026-11-03). Owner: "i dont want it turned off i want
# it removed". In every stone material the same 5 HLSL lines draw it (world-space T_CrackMask, darkens up to 88 %):
#     float3 pc = WP / CrackSize;   float Crack = Texture2DSample(CrackTex, ...);   float region=saturate((N2-0.42)*5.0)*CrackAmt;
#     float k=saturate(Crack*region*1.4);   c*=1.0-k*0.88;
# Per material: (1) backup copy <name>_bak470 (once), (2) those lines deleted from every Custom node (refused if any other crack
# reference would remain), (3) the Custom nodes' crack inputs (CrackTex / Crack / CrackAmt / CrackSize) removed, (4) the crack
# parameters (CrackAmount, CrackSize_cm, CrackMask) and every node that samples the crack texture deleted, (5) recompile + save.
#   py remove470_ue.py --dry-run                 what would change, per material (nothing changed)
#   py remove470_ue.py --apply [--nosave]        do it (--nosave: in memory only, for a test)
#   py remove470_ue.py ... --only <MaterialName>     limit to one material (test)
#   py remove470_ue.py --revert                  every user of a changed material is pointed back at its _bak470 copy
# Wood (drawbridge) and the fountain's carved cracks are other materials and are not touched. Aborts in PIE.
import re, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
DEAD = [r'^\s*float3\s+pc\s*=\s*WP\s*/\s*CrackSize\s*;\s*$', r'^\s*float\s+Crack\s*=\s*Texture2DSample\(CrackTex.*;\s*$',
        r'^\s*float\s+region\s*=\s*saturate\(\(N2-0\.42\)\*5\.0\)\*CrackAmt\s*;\s*$', r'^\s*float\s+k\s*=\s*saturate\(Crack\*region\*1\.4\)\s*;\s*$',
        r'^\s*c\s*\*=\s*1\.0-k\*0\.88\s*;\s*$']
CRACK_INPUTS = ('CrackTex', 'Crack', 'CrackAmt', 'CrackSize')
CRACK_PARAMS = ('CrackAmount', 'CrackSize_cm', 'CrackMask')
ar = unreal.AssetRegistryHelpers.get_asset_registry()
flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'Material')], package_paths=['/Game/CastleDefender'], recursive_paths=True)

def exprs(m, cls):
    mp = m.get_path_name()
    return [x for x in unreal.ObjectIterator(cls) if x.get_path_name().startswith(mp + ':') or x.get_path_name().startswith(mp + '.')]

targets = []
for ad in ar.get_assets(flt):
    p = str(ad.package_name)
    if p.endswith('_bak470') or '/AssetPacks/' in p or re.search(r'_(BACKUP|PRETILE|PREDETILE)$', p): continue      # archived copies: not in use
    if '--only' in A and p.split('/')[-1] != A[A.index('--only') + 1]: continue
    m = unreal.load_asset(p)
    if not m: continue
    cust = [x for x in exprs(m, unreal.MaterialExpressionCustom) if 'CrackAmt' in x.get_editor_property('code') or 'CrackTex' in x.get_editor_property('code')]
    if cust: targets.append((p, m, cust))

if '--revert' in A:
    for p, m, cust in targets: pass
    n = 0
    for ad in ar.get_assets(flt):
        p = str(ad.package_name)
        if not p.endswith('_bak470'): continue
        orig = p[:-len('_bak470')]
        if EAL.does_asset_exist(orig):
            EAL.consolidate_assets(unreal.load_asset(p), [unreal.load_asset(orig)]); n += 1
            print('REVERT: users of', orig.split('/')[-1], '-> backup', p.split('/')[-1])
    print('reverted', n); raise SystemExit

for p, m, cust in targets:
    print('==', p)
    plan_ok = True; new_codes = []
    for x in cust:
        code = x.get_editor_property('code'); lines = code.split('\n')
        keep = [l for l in lines if not any(re.match(r, l) for r in DEAD)]
        rest = '\n'.join(keep)
        left = [w for w in ('CrackTex', 'CrackAmt', 'CrackSize', 'Crack', 'region', ' k)', 'k*', '*k') if w in rest.replace('CrackSampler', '')]
        print('   %s: %d crack lines removed, %d lines left%s' % (x.get_name(), len(lines) - len(keep), len(keep), ('  STILL REFERENCES ' + str(left)) if left else ''))
        if left or len(lines) - len(keep) < 3: plan_ok = False
        new_codes.append((x, rest))
    params = [x for cls in (unreal.MaterialExpressionScalarParameter, unreal.MaterialExpressionTextureObjectParameter, unreal.MaterialExpressionTextureSampleParameter2D)
              for x in exprs(m, cls) if str(x.get_editor_property('parameter_name')) in CRACK_PARAMS]
    samples = [x for x in exprs(m, unreal.MaterialExpressionTextureSample) if x not in params and x.get_editor_property('texture') and 'CrackMask' in x.get_editor_property('texture').get_name()]
    print('   delete params', sorted(set(str(x.get_editor_property('parameter_name')) for x in params)), '+', len(samples), 'crack texture samples')
    if not plan_ok: print('   SKIP: crack code not in the expected form, left untouched'); continue
    if '--apply' not in A: continue
    bak = p + '_bak470'
    if not EAL.does_asset_exist(bak): EAL.duplicate_asset(p, bak); EAL.save_asset(bak); print('   backup', bak)
    m.modify()
    for x, rest in new_codes:
        x.modify(); x.set_editor_property('code', rest)
        ins = [i for i in x.get_editor_property('inputs') if str(i.get_editor_property('input_name')) not in CRACK_INPUTS]
        x.set_editor_property('inputs', ins)
    for x in params + samples: MEL.delete_material_expression(m, x)
    MEL.recompile_material(m)
    if '--nosave' not in A: EAL.save_loaded_asset(m)
    print('   APPLIED' + (' (not saved)' if '--nosave' in A else ' + saved'))
if '--apply' not in A: print('DRY RUN: nothing changed')
