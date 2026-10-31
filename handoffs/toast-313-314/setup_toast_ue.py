# #313 / #314 tiny toast, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/toast-313-314/setup_toast_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/toast-313-314/setup_toast_ue.py"
# Makes /Game/CastleDefender/Gameplay/Castle/BPC_Toast (ActorComponent) and adds it to the hero as "Toast".
# Nothing else is changed.
import os, sys, unreal

try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\toast-313-314'
DRY = '--dry-run' in sys.argv
DST, NAME = '/Game/CastleDefender/Gameplay/Castle', 'BPC_Toast'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#313/#314 toast setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


path = DST + '/' + NAME
if EAL.does_asset_exist(path):
    comp = unreal.load_asset(path); log.append('reusing ' + path)
else:
    log.append('create ' + path); comp = None
    if not DRY:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
        comp = AT.create_asset(NAME, DST, unreal.Blueprint, f)
        BEL.compile_blueprint(comp); EAL.save_asset(path)

hero = unreal.load_asset(HERO)
if 'Toast' in names(hero): log.append('hero already has Toast')
else:
    log.append('hero: + Toast (BPC_Toast)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0],
                                                                     new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add Toast: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('Toast'))
        BEL.compile_blueprint(hero); EAL.save_asset(HERO)

out = '\n'.join(log) + '\nNext: README step 2 (9 BPVar lines on BPC_Toast, Compile), then step 3 (paste BPC_Toast_graph.txt).'
if not DRY: open(os.path.join(HERE, 'setup_toast.txt'), 'w').write(out)
unreal.log(out)
