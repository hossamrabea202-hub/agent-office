# #80 step 1 (laptop2, 2026-10-29): creates the actor Blueprint BP_ArmySplit with its variables and defaults,
# sets Tick Interval 0.5 and places one BP_ArmySplit in the open level. Safe to re-run (reuses what exists).
# Run in the editor (Output Log, Python):  py "<repo>/handoffs/tentacle-split-80/bp/create_bp_armysplit.py"
# Then paste BP_ArmySplit_graph.txt into its EventGraph, compile, save (README.md).
import unreal

FOLDER = '/Game/CastleDefender/Gameplay/Army'
NAME = 'BP_ArmySplit'
PATH = FOLDER + '/' + NAME
SOLDIER = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'
VITALS = '/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals'
PLACE_IN_LEVEL = True
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
log = []

# ---- the asset ----
if EAL.does_asset_exist(PATH):
    bp = unreal.load_asset(PATH); log.append('reusing ' + PATH)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, FOLDER, unreal.Blueprint, f)
    log.append('created ' + PATH)

# ---- variable types ----
def basic(n):
    t = BEL.get_basic_type_by_name(n)
    if n == 'real': t.set_editor_property('pin_sub_category', 'double')
    return t
def obj(cls): return BEL.get_object_reference_type(cls)
def arr(t): return BEL.get_array_type(t)
def vec(): return BEL.get_struct_type(unreal.Vector.static_struct())

def bp_class(path):
    c = EAL.load_blueprint_class(path)
    if c is None: raise RuntimeError('class not found: ' + path)
    return c

# name -> (type factory, default or None). Same table as README "Variables".
VARS = [
    ('Tentacle',       lambda: obj(unreal.Actor), None),
    ('HitPart',        lambda: obj(unreal.Actor), None),
    ('TentVitals',     lambda: obj(bp_class(VITALS)), None),
    ('HoldPoint',      vec, None),
    ('Members',        lambda: arr(obj(bp_class(SOLDIER))), None),
    ('Strike',         lambda: arr(obj(bp_class(SOLDIER))), None),
    ('Guard',          lambda: arr(obj(bp_class(SOLDIER))), None),
    ('PrevOrder',      lambda: arr(vec()), None),
    ('PrevGoal',       lambda: arr(vec()), None),
    ('Active',         lambda: basic('bool'), False),
    ('LastHitAt',      lambda: basic('real'), 0.0),
    ('PickN',          lambda: basic('int'), 0),
    ('StrikeRadius',   lambda: basic('real'), 250.0),
    ('StepBackRadius', lambda: basic('real'), 500.0),
    ('GuardRadius',    lambda: basic('real'), 400.0),
    ('XbowStandoff',   lambda: basic('real'), 1300.0),
    ('SwordDamage',    lambda: basic('real'), 20.0),
    ('XbowDamage',     lambda: basic('real'), 15.0),
    ('SwordHitChance', lambda: basic('real'), 0.45),
    ('XbowShotChance', lambda: basic('real'), 0.3),
    ('EndNoHitTime',   lambda: basic('real'), 6.0),
    ('EndDistance',    lambda: basic('real'), 2500.0),
]

have = set()
try:
    have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
except Exception:
    pass
missing = []
for n, tf, _ in VARS:
    if n in have: continue
    try:
        if not BEL.add_member_variable(bp, n, tf()):
            raise RuntimeError('add_member_variable returned False')
        log.append('  + ' + n)
    except Exception as e:
        missing.append(n); log.append('  ! %s not added (%s): add it by hand, README table' % (n, e))

try:
    BEL.compile_blueprint(bp)
except Exception as e:
    log.append('compile failed: %s' % e)

# ---- class defaults: variable defaults and Tick Interval ----
cdo = None
try:
    cdo = unreal.get_default_object(bp.generated_class())
except Exception as e:
    log.append('no class default object: %s' % e)
if cdo is not None:
    for n, _, v in VARS:
        if v is None or n in missing: continue
        try: cdo.set_editor_property(n, v)
        except Exception as e: log.append('  default %s = %s not set (%s): set it in Class Defaults' % (n, v, e))
    try:
        t = cdo.get_editor_property('primary_actor_tick')
        t.set_editor_property('tick_interval', 0.5)
        cdo.set_editor_property('primary_actor_tick', t)
        log.append('Tick Interval = 0.5')
    except Exception as e:
        log.append('Tick Interval not set (%s): BeginPlay sets it anyway (Set Actor Tick Interval 0.5)' % e)
EAL.save_asset(PATH)

# ---- one instance in the open level ----
if PLACE_IN_LEVEL:
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        cls = bp.generated_class()
        placed = [a for a in eas.get_all_level_actors() if a.get_class() == cls]
        if placed:
            log.append('level already has %s (%s)' % (NAME, placed[0].get_actor_label()))
        else:
            a = eas.spawn_actor_from_class(cls, unreal.Vector(0, 0, 0))
            log.append('placed %s at the origin: save the level' % (a.get_actor_label() if a else 'nothing (spawn failed)'))
    except Exception as e:
        log.append('not placed (%s): drag BP_ArmySplit into the level' % e)

unreal.log('#80 BP_ArmySplit setup:\n' + '\n'.join(log) +
           '\nNext: open BP_ArmySplit, paste BP_ArmySplit_graph.txt into the EventGraph, Compile, Save (README.md).')
