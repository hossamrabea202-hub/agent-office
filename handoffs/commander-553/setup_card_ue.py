# #553 commander card, step 1: creates BPC_CommanderCard (variables + defaults from build/card_data.json), adds it to the hero as
# "CommanderCard". New assets only. Safe to re-run. Run stroke_material_ue.py --apply first.
#   py setup_card_ue.py --dry-run | --apply     (--no-hero: i5 lab, no hero there)
import os, sys, json, unreal
A = sys.argv[1:]
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossam.rabea\agent-office\handoffs\commander-553'
HERE = os.environ.get('CC553_DIR', HERE)
D = json.load(open(os.path.join(HERE, 'build', 'card_data.json')))
COMP_DIR, COMP = '/Game/CastleDefender/Gameplay/Castle', 'BPC_CommanderCard'
PATH = COMP_DIR + '/' + COMP
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
STROKE = '/Game/CastleDefender/UI/Barracks/Commander/M_CC_Stroke'
BUST = '/Game/CastleDefender/UI/Barracks/Muster/T_MU_Bust_Cmdr'
GATE, WM = '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl', '/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
NEEDS = [GATE, WM, '/Game/CastleDefender/Characters/Knight/BP_SoldierSword', '/Game/CastleDefender/Characters/Knight/BP_SoldierCommander', '/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals', STROKE, BUST] + ([] if '--no-hero' in A else [HERO])
missing = [p for p in NEEDS if not EAL.does_asset_exist(p)]
for p in NEEDS: print('CARD %-8s %s' % ('MISSING' if p in missing else 'ok', p))
if '--apply' not in A: print('CARD dry run, nothing changed'); raise SystemExit
if missing and '--lab' not in A: raise SystemExit('STOP: missing %s' % missing)
if EAL.does_asset_exist(PATH): bp = unreal.load_asset(PATH)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(COMP, COMP_DIR, unreal.Blueprint, f)
I, Dd, Bo, St, Na = (BEL.get_basic_type_by_name(x) for x in ('int', 'real', 'bool', 'string', 'name'))
OBJ = BEL.get_object_reference_type; ARR = BEL.get_array_type
ACT = OBJ(unreal.Actor)
def cls(p):
    a = unreal.load_asset(p); return a.generated_class() if a else unreal.Actor
TY = {'bool': Bo, 'int': I, 'double': Dd, 'string': St, 'name': Na, 'actor': ACT, 'actors': ARR(ACT), 'material': OBJ(unreal.MaterialInterface), 'mid': OBJ(unreal.MaterialInstanceDynamic),
      'tex': OBJ(unreal.Texture2D), 'strings': ARR(St), 'ints': ARR(I)}
have = [str(x) for x in BEL.list_member_variable_names(bp)] if hasattr(BEL, 'list_member_variable_names') else []
for n, (t, v) in D['vars'].items():
    if n in have: continue
    ty = OBJ(cls(v)) if t == 'obj' else TY[t]
    if not BEL.add_member_variable(bp, n, ty): raise RuntimeError('could not add ' + n)
print('CARD vars added', len(D['vars']) - len(have), 'compile', BEL.compile_blueprint(bp))
cdo = unreal.get_default_object(bp.generated_class())
for n, (t, v) in D['vars'].items():
    if t in ('bool', 'int', 'double', 'string') and v not in (None, ''): cdo.set_editor_property(n, v)
for n in ('Names', 'Ages', 'RankNames'): cdo.set_editor_property(n, D['data'][n])
if EAL.does_asset_exist(STROKE): cdo.set_editor_property('StrokeMat', unreal.load_asset(STROKE))
if EAL.does_asset_exist(BUST): cdo.set_editor_property('BustTex', unreal.load_asset(BUST))
EAL.save_asset(PATH, only_if_is_dirty=False)
if '--no-hero' not in A:
    hero = unreal.load_asset(HERO)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(hero)
    names = [str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in handles]
    if 'CommanderCard' in names: print('CARD hero already has it')
    else:
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=bp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add component: %s' % fail)
        sds.rename_subobject(h, unreal.Text('CommanderCard')); print('CARD hero: added')
    BEL.compile_blueprint(hero); EAL.save_asset(HERO, only_if_is_dirty=False)
print('CARD saved. Next: paste build/BPC_CommanderCard_graph.txt into its EventGraph, Compile, Save.')
