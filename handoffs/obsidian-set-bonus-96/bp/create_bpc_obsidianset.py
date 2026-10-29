# #96 step 1 (laptop2, 2026-10-29): creates BPC_ObsidianSet with its variables, adds it to the hero as "ObsidianSet",
# and adds the hero bool ObsBlocked. Safe to re-run (existing assets/variables are reused).
# Run in the editor:  py "<repo>/handoffs/obsidian-set-bonus-96/bp/create_bpc_obsidianset.py"
# Then paste the graphs (README.md steps 2-3).
import unreal

D = '/Game/CastleDefender/Gameplay/Castle'
NAME = 'BPC_ObsidianSet'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = []

path = D + '/' + NAME
if EAL.does_asset_exist(path):
    bp = unreal.load_asset(path); log.append('reusing ' + path)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
    bp = tools.create_asset(NAME, D, unreal.Blueprint, f); log.append('created ' + path)

# name -> (type, default). Defaults are written on the class defaults after the compile.
VARS = {
    'ObsOwned': ('int', 0), 'ObsWorn': ('int', 0), 'ObsBought': ('int', 0), 'WornCount': ('int', 0),
    'ShieldLevel': ('int', 0), 'NextPrice': ('int', 450), 'NextShieldPrice': ('int', 600),
    'ObsPriceMul': ('real', 1.45), 'WasComplete': ('bool', False),
    'ShockReadyAt': ('real', 0.0), 'ShockCooldown': ('real', 12.0), 'ShockDamage': ('real', 40.0), 'ShockRadius': ('real', 400.0),
}

def add_vars(bp, vars_):
    have = set()
    try:
        have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
    except Exception:
        pass
    for n, (t, _) in vars_.items():
        if n in have: continue
        pt = BEL.get_basic_type_by_name(t)
        if t == 'real':
            pt.set_editor_property('pin_sub_category', 'double')
        if not BEL.add_member_variable(bp, n, pt):
            raise RuntimeError('could not add variable %s' % n)
        log.append('  + %s (%s)' % (n, t))

add_vars(bp, VARS)
BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
for n, (t, v) in VARS.items():
    try: cdo.set_editor_property(n, v)
    except Exception as e: log.append('  default %s not set: %s (set it in Class Defaults)' % (n, e))
EAL.save_asset(path)

# ---- hero: ObsBlocked + the component ----
hero = unreal.load_asset(HERO)
add_vars(hero, {'ObsBlocked': ('bool', False)})
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(hero)
names = [str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in handles]
if 'ObsidianSet' in names:
    log.append('hero already has ObsidianSet')
else:
    p = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=bp.generated_class(), blueprint_context=hero)
    h, fail = sds.add_new_subobject(p)
    if not fail.is_empty(): raise RuntimeError('add component: %s' % fail)
    sds.rename_subobject(h, unreal.Text('ObsidianSet'))
    log.append('hero: added component ObsidianSet')
BEL.compile_blueprint(hero)
EAL.save_asset(HERO)
unreal.log('#96 BPC_ObsidianSet setup:\n' + '\n'.join(log) + '\nNext: paste BPC_ObsidianSet_graph.txt into its EventGraph (README step 2).')
