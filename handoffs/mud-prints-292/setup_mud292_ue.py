# #292 Muddy footprints, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/mud-prints-292/setup_mud292_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/mud-prints-292/setup_mud292_ue.py"               (--no-place: don't put the 3 test puddles in the level)
# Makes in /Game/CastleDefender/Environment/Mud (all new, no live material or decal is touched):
#   M_MudPuddle   deferred decal: wet mud patch with a water centre (procedural, Custom HLSL, no textures)
#   M_MudPrint    deferred decal: one boot print (sole + heel + cleats + squeezed rim), params Strength / Side / Swap
#   MI_MudPrint   its instance (the hero's BPC_MudPrints uses it). Prints sideways in Play? set Swap = 1 here.
#   BP_MudPad     actor (tag MudPad) with a 3 m decal "Mud" = M_MudPuddle. Place / scale it wherever the ground is muddy.
#   BPC_MudPrints ActorComponent, added to the hero as "MudPrints".
# Unless --no-place: 3 BP_MudPad in front of the PlayerStart (4, 8 and 12 m) for the test, only if the level has none yet.
import os, sys, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'mud-prints-292')
DRY = '--dry-run' in sys.argv
PLACE = '--no-place' not in sys.argv
DST = '/Game/CastleDefender/Environment/Mud'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, MEL, BEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#292 mud prints setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


def fresh(name, cls, factory):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path), False
    log.append('create ' + path)
    if DRY: return None, True
    return AT.create_asset(name, DST, cls, factory), True


def custom(m, code, inputs, otype, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code); e.set_editor_property('output_type', otype); e.set_editor_property('description', 'Mud292')
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    e.set_editor_property('inputs', ins); return e


def mask(m, src, rgba, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, x, y)
    for k, v in zip('rgba', rgba): e.set_editor_property(k, v)
    MEL.connect_material_expressions(src, '', e, ''); return e


def scalar(m, name, val, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', val); return e


def decal_material(name, code_col, code_rough, params):
    m, made = fresh(name, unreal.Material, unreal.MaterialFactoryNew())
    if not m: return None
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_DEFERRED_DECAL'))
    m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_TRANSLUCENT'))
    try: m.set_editor_property('decal_blend_mode', enum(unreal.DecalBlendMode, 'DBM_TRANSLUCENT'))
    except Exception: pass      # 5.3: the blend mode above already makes it a translucent decal
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    ins = ['UV'] + [p for p, _ in params]
    cc = custom(m, code_col, ins, unreal.CustomMaterialOutputType.CMOT_FLOAT4, -300, 0)
    cr = custom(m, code_rough, ins, unreal.CustomMaterialOutputType.CMOT_FLOAT1, -300, 300)
    for c in (cc, cr):
        MEL.connect_material_expressions(uv, '', c, 'UV')
        y = 150
        for p, v in params:
            MEL.connect_material_expressions(scalar(m, p, v, -900, y), '', c, p); y += 120
    MEL.connect_material_property(mask(m, cc, (True, True, True, False), 0, 0), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(mask(m, cc, (False, False, False, True), 0, 150), '', unreal.MaterialProperty.MP_OPACITY)
    MEL.connect_material_property(cr, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m); EAL.save_asset(DST + '/' + name); return m


# ---- shared HLSL: a hash for grain (no textures)
HASH = 'float h = frac(sin(dot(floor(UV * 56.0), float2(12.9898, 78.233))) * 43758.5453);\n'

# Boot print. p.y runs heel (-0.5) to toe (+0.5); Side mirrors left/right, Swap turns it 90 deg if the decal axes differ.
PRINT = '''float2 p = UV - 0.5;
if (Swap > 0.5) p = p.yx;
p.x *= (Side < 0.0 ? -1.0 : 1.0);
float2 q = float2(p.x - 0.05 * p.y, p.y);
float sole = length(float2(q.x / 0.15, (q.y - 0.10) / 0.30));
float heel = length(float2(q.x / 0.125, (q.y + 0.30) / 0.13));
float d = min(sole, heel);
''' + HASH + '''float body = 1.0 - smoothstep(0.80, 1.0, d);
float rim = smoothstep(0.68, 0.95, d) * body;
float cleat = step(0.45, frac(q.y * 20.0 + 0.3 * h));
'''
PRINT_COL = PRINT + '''float a = body * lerp(0.5, 1.0, 0.6 * cleat + 0.4 * h);
a = saturate(a + 0.35 * rim) * saturate(Strength);
float3 c = lerp(float3(0.060, 0.046, 0.032), float3(0.036, 0.028, 0.020), rim);
return float4(c, a);'''
PRINT_ROUGH = PRINT + 'return saturate(0.16 + 0.32 * (1.0 - Strength) + 0.06 * h - 0.06 * rim);'

# Puddle: an uneven mud patch, darker and glossy where the water stands in the middle.
PUD = '''float2 p = (UV - 0.5) * 2.0;
float r = length(p);
float an = atan2(p.y, p.x);
float n = 0.5 * sin(an * 3.0 + 1.3) + 0.3 * sin(an * 7.0 + 4.1) + 0.2 * sin(an * 13.0 + 2.2);
float edge = 0.80 + 0.08 * n;
''' + HASH + '''float water = 1.0 - smoothstep(edge * 0.42 - 0.08, edge * 0.42 + 0.06, r + 0.07 * n);
'''
PUD_COL = PUD + '''float a = (1.0 - smoothstep(edge - 0.20, edge, r)) * lerp(0.72, 1.0, h);
float3 c = lerp(float3(0.072, 0.056, 0.040), float3(0.030, 0.024, 0.018), water);
return float4(c * lerp(0.9, 1.1, h), saturate(a));'''
PUD_ROUGH = PUD + 'return lerp(0.38 + 0.08 * h, 0.03, water);'

decal_material('M_MudPuddle', PUD_COL, PUD_ROUGH, [])
pm = decal_material('M_MudPrint', PRINT_COL, PRINT_ROUGH, [('Strength', 1.0), ('Side', 1.0), ('Swap', 0.0)])
mi, made = fresh('MI_MudPrint', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
if mi and pm:
    mi.set_editor_property('parent', pm); EAL.save_asset(DST + '/MI_MudPrint')


# ---- Blueprints
def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return AT.create_asset(name, DST, unreal.Blueprint, f)


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add_comp(bp, cls, name):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(bp)[0], new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


pad = make_bp('BP_MudPad', unreal.Actor)
if pad:
    dc = add_comp(pad, unreal.DecalComponent, 'Mud')
    if EAL.does_asset_exist(DST + '/M_MudPuddle'): dc.set_editor_property('decal_material', unreal.load_asset(DST + '/M_MudPuddle'))
    dc.set_editor_property('decal_size', unreal.Vector(60, 150, 150))          # half-extents: 3 m wide, 1.2 m deep projection
    dc.set_editor_property('relative_rotation', unreal.Rotator(roll=0, pitch=-90, yaw=0))
    dc.set_editor_property('sort_order', 1)
    unreal.get_default_object(pad.generated_class()).set_editor_property('tags', [unreal.Name('MudPad')])
    BEL.compile_blueprint(pad); EAL.save_asset(DST + '/BP_MudPad')
comp = make_bp('BPC_MudPrints', unreal.ActorComponent)
if comp: BEL.compile_blueprint(comp); EAL.save_asset(DST + '/BPC_MudPrints')

hero = unreal.load_asset(HERO)
if 'MudPrints' in names(hero): log.append('hero already has MudPrints')
else:
    log.append('hero: + MudPrints (BPC_MudPrints)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0], new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add MudPrints: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('MudPrints')); BEL.compile_blueprint(hero); EAL.save_asset(HERO)

if PLACE:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    if any(a.actor_has_tag('MudPad') for a in actors): log.append('level already has MudPads: none placed')
    else:
        ps = [a for a in actors if isinstance(a, unreal.PlayerStart)]
        if not ps: log.append('no PlayerStart: place BP_MudPad by hand')
        else:
            s = ps[0]; loc, fwd = s.get_actor_location(), s.get_actor_forward_vector()
            for k, dist in enumerate((400, 800, 1200)):
                at = unreal.Vector(loc.x + fwd.x * dist, loc.y + fwd.y * dist, loc.z - 90)
                log.append('place BP_MudPad %d at %s' % (k + 1, at))
                if not DRY and pad: eas.spawn_actor_from_class(pad.generated_class(), at, unreal.Rotator(0, 0, 37 * k))
            if not DRY: unreal.EditorLevelLibrary.save_current_level()
out = '\n'.join(log) + '\nNext: README step 3 (5 BPVar lines + BPC_MudPrints_graph.txt).'
if not DRY: open(os.path.join(HERE, 'setup_mud292.txt'), 'w').write(out)
unreal.log(out)
