# #369 Quests + daily rewards, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/quests-369/setup_quests369_ue.py" --dry-run / (no flag)
# Makes /Game/CastleDefender/Gameplay/Quests/BPC_Quests (ActorComponent) and adds it to the hero as "Quests".
import sys, unreal
DRY = '--dry-run' in sys.argv
DST, NAME = '/Game/CastleDefender/Gameplay/Quests', 'BPC_Quests'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#369 quests setup' + (' (DRY RUN, nothing written)' if DRY else '')]
path = DST + '/' + NAME
log.append(('reuse ' if EAL.does_asset_exist(path) else 'create ') + path)
if not DRY:
    bp = unreal.load_asset(path)
    if not bp:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
        bp = AT.create_asset(NAME, DST, unreal.Blueprint, f)
    BEL.compile_blueprint(bp); EAL.save_asset(path)
    NOHERO = '--no-hero' in sys.argv   # i5 core: build the component only; the Master adds it to the hero (run without the flag)
    hero = None if NOHERO else unreal.load_asset(HERO)
    have = [] if NOHERO else [str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))) for h in SDS.k2_gather_subobject_data_for_blueprint(hero)]
    if NOHERO: log.append('--no-hero: hero NOT touched; run again without --no-hero to add Quests to the hero')
    elif 'Quests' in have: log.append('hero already has Quests')
    else:
        h, why = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0], new_class=bp.generated_class(), blueprint_context=hero))
        if not LIB.is_handle_valid(h): raise SystemExit('could not add Quests to the hero: %s' % why)
        SDS.rename_subobject(h, unreal.Text('Quests')); log.append('hero: + Quests (BPC_Quests)')
        BEL.compile_blueprint(hero); EAL.save_asset(HERO)
log.append('Next: 12 BPVar lines on BPC_Quests, Compile, paste BPC_Quests_graph.txt, Compile, Save.')
out = '\n'.join(log); unreal.log(out); print(out)
