# #73 step 1 (laptop2, 2026-10-29): creates BPC_Infection with its variables and defaults, adds it to the hero as
# "Infection", and gives BP_Zombie the actor tag "Infects". Safe to re-run (existing assets/variables/tags are reused).
# Run in the editor:  py "<repo>/handoffs/infection-73/bp/create_bpc_infection.py"
# Then paste the graphs (README.md steps 2-4). If a line in the log says BY HAND, do that one yourself (VARS below).
import unreal

D = '/Game/CastleDefender/Gameplay/Castle'
NAME = 'BPC_Infection'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
ZOMBIE = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = []

# name -> (type, default). 'real' = double. Defaults are written on the class defaults after the compile.
VARS = {
    # saved state
    'Infected': ('bool', False), 'AntidotesBought': ('int', 0), 'InfectSeen': ('bool', False),
    # runtime state
    'InfectedAt': ('real', 0.0), 'CuredAt': ('real', -100.0), 'DrainStep': ('int', 0), 'AntidotePrice': ('int', 0),
    'ExplainCard': ('int', 0), 'ExplainT0': ('real', 0.0), 'LastSaveT': ('real', 0.0), 'CardMID': ('mid', None),
    # tuning
    'MaxHP': ('real', 100.0), 'InfectBelow': ('real', 0.30), 'ReinfectGuard': ('real', 60.0), 'DefMul': ('real', 0.666667),
    'DrainEvery': ('real', 2.0), 'DrainPct': ('real', 0.01), 'DrainCap': ('real', 0.95),
}

path = D + '/' + NAME
if EAL.does_asset_exist(path):
    bp = unreal.load_asset(path); log.append('reusing ' + path)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
    bp = tools.create_asset(NAME, D, unreal.Blueprint, f); log.append('created ' + path)

def add_vars(bp, vars_):
    have = set()
    try:
        have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
    except Exception:
        pass
    for n, (t, _) in vars_.items():
        if n in have: continue
        try:
            if t == 'mid':
                pt = BEL.get_object_reference_type(unreal.MaterialInstanceDynamic)
            else:
                pt = BEL.get_basic_type_by_name(t)
                if t == 'real': pt.set_editor_property('pin_sub_category', 'double')
            ok = BEL.add_member_variable(bp, n, pt)
        except Exception as e:
            ok = False; log.append('  %s: %s' % (n, e))
        log.append(('  + %s (%s)' if ok else '  BY HAND: add variable %s (%s)') % (n, t))

add_vars(bp, VARS)
BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
for n, (t, v) in VARS.items():
    if v is None: continue
    try: cdo.set_editor_property(n, v)
    except Exception as e: log.append('  BY HAND: default %s = %s in Class Defaults (%s)' % (n, v, e))
EAL.save_asset(path)

# ---- hero: the component ----
hero = unreal.load_asset(HERO)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(hero)
names = [str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in handles]
if 'Infection' in names:
    log.append('hero already has Infection')
else:
    p = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=bp.generated_class(), blueprint_context=hero)
    h, fail = sds.add_new_subobject(p)
    if not fail.is_empty(): raise RuntimeError('add component: %s' % fail)
    sds.rename_subobject(h, unreal.Text('Infection'))
    log.append('hero: added component Infection')
BEL.compile_blueprint(hero)
EAL.save_asset(HERO)

# ---- BP_Zombie: actor tag "Infects" (the bite check). Add it to the colossus / tentacle BPs too once they hit the hero ----
try:
    z = unreal.load_asset(ZOMBIE)
    zc = unreal.get_default_object(z.generated_class())
    tags = list(zc.get_editor_property('tags'))
    if 'Infects' in [str(t) for t in tags]:
        log.append('BP_Zombie already tagged Infects')
    else:
        tags.append(unreal.Name('Infects')); zc.set_editor_property('tags', tags)
        EAL.save_asset(ZOMBIE, only_if_is_dirty=False)
        log.append('BP_Zombie: tag Infects added')
except Exception as e:
    log.append('BY HAND: BP_Zombie Class Defaults > Actor > Tags: add "Infects" (%s)' % e)

unreal.log('#73 BPC_Infection setup:\n' + '\n'.join(log) + '\nNext: paste BPC_Infection_graph.txt into its EventGraph (README step 2).')
