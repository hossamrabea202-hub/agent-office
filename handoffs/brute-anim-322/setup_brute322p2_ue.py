# #322 part 2 Flesh Brute animation polish, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/brute-anim-322/setup_brute322p2_ue.py" --dry-run      only reports
#   py "<repo>/handoffs/brute-anim-322/setup_brute322p2_ue.py"                makes ABP_FleshBrute (AnimInstance, SK_FleshBrute
#        skeleton) next to BP_FleshBrute, and a backup copy BP_FleshBrute_BAK322 of the brute before its graph is replaced
#   py ".../setup_brute322p2_ue.py" --finish [--dry-run]                      after the ABP is pasted + compiled: BP_FleshBrute's
#        Mesh -> Animation Mode = Use Animation Blueprint, Anim Class = ABP_FleshBrute; compiles and saves the brute
import os, sys, unreal

A = sys.argv[1:]
DRY, FINISH = '--dry-run' in A, '--finish' in A
DIR = '/Game/CastleDefender/Characters/Enemies/FleshBrute'
ABP, BRUTE, SKEL = DIR + '/ABP_FleshBrute', DIR + '/BP_FleshBrute', DIR + '/SK_FleshBrute_Skeleton'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
log = ['#322 p2 brute anim setup' + (' (DRY RUN, nothing written)' if DRY else '')]

if not FINISH:
    if EAL.does_asset_exist(ABP): log.append('ABP_FleshBrute already there: kept')
    else:
        log.append('create ' + ABP + ' (skeleton SK_FleshBrute_Skeleton, parent AnimInstance)')
        if not DRY:
            f = unreal.AnimBlueprintFactory()
            f.set_editor_property('target_skeleton', unreal.load_asset(SKEL))
            f.set_editor_property('parent_class', unreal.AnimInstance)
            a = AT.create_asset('ABP_FleshBrute', DIR, unreal.AnimBlueprint, f)
            if not a: raise SystemExit('could not create ABP_FleshBrute')
            EAL.save_asset(ABP)
    bak = BRUTE + '_BAK322'
    if EAL.does_asset_exist(bak): log.append('backup already there: ' + bak)
    else:
        log.append('backup ' + BRUTE + ' -> ' + bak)
        if not DRY: EAL.duplicate_asset(BRUTE, bak); EAL.save_asset(bak)
else:
    abp = unreal.load_asset(ABP)
    bp = unreal.load_asset(BRUTE)
    if not abp or not bp: raise SystemExit('missing ABP_FleshBrute or BP_FleshBrute')
    cls = unreal.load_class(None, ABP + '.ABP_FleshBrute_C')
    if not cls: raise SystemExit('ABP_FleshBrute has no compiled class: compile it first')
    cdo = unreal.get_default_object(bp.generated_class())
    mesh = cdo.get_editor_property('mesh')
    log.append('BP_FleshBrute Mesh: mode %s, anim class %s -> ANIMATION_BLUEPRINT, ABP_FleshBrute_C' % (
        mesh.get_editor_property('animation_mode'), mesh.get_editor_property('anim_class')))
    if not DRY:
        mesh.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT)
        mesh.set_editor_property('anim_class', cls)
        BEL.compile_blueprint(bp); EAL.save_asset(BRUTE)
        cdo = unreal.get_default_object(bp.generated_class()); m2 = cdo.get_editor_property('mesh')
        ok = m2.get_editor_property('anim_class') == cls
        log.append('check after save: anim class %s' % ('OK' if ok else 'NOT SET -> MANUAL: BP_FleshBrute > Mesh > Animation: '
                                                            'Animation Mode = Use Animation Blueprint, Anim Class = ABP_FleshBrute, compile, save'))

for l in log: unreal.log(l)
print('\n'.join(log))
