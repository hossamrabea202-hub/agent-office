# #410 rain makes the world wet (i5 core / adjustedfilm, 2026-11-01). UE 5.8 Python, safe to re-run.
#   py "<repo>/handoffs/rain-wet-410/wet410_ue.py" [--dry-run]           build *_Wet410 COPIES of the masters (live ones untouched)
#   py ".../wet410_ue.py" --swap [--dry-run]                             AFTER the owner's OK: re-parent the castle MIs to the copies
#   py ".../wet410_ue.py" --revert                                       put every swapped MI back (wet410_backup.json)
# Each copy reads MPC_Weather.Wet (0 dry .. 1 soaked, written by BPC_Weather). Scalar WetPreview (-1 = use the weather,
# 0..1 = force) is for lookdev: set it on a preview MI to shoot dry vs soaked without rain or the map.
# What wet does (RESEARCH.md): porous darkening of the albedo, roughness toward a water film, up-facing low spots
# (cavity/AO + world noise) collect puddles: mirror-smooth, flat normal, darker; walls stay wet-dark but shed water.
import json, os, sys, unreal

A = sys.argv[1:]
DRY, SWAP, REVERT = '--dry-run' in A, '--swap' in A, '--revert' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(os.path.expanduser('~'), 'agent-office', 'handoffs', 'rain-wet-410')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty
MPC = '/Game/CastleDefender/Environment/Weather/MPC_Weather'
C = '/Game/CastleDefender/Shared/Materials/Castle/'
# master -> (porosity 0..1, puddles on/off, the MIs that the swap re-parents)
TARGETS = {
    C + 'M_Castle_StoneWall_World': (0.5, True, [C + 'MI_Castle_StoneWall_World', C + 'MI_Castle_Trim_World',
                                                 C + 'MI_Castle_WalkFlag_World', C + 'MI_Castle_Planks_World']),
    '/Game/CastleDefender/Environment/WallTops/M_WallWorldAligned': (0.35, True,
                                                 ['/Game/CastleDefender/Environment/WallTops/MI_Castle_WalkFlag_World_WA']),
    C + 'M_Castle_Paving_POM': (0.25, True, [C + 'MI_Castle_Paving_POM', C + 'MI_Castle_Paving_Walk']),
    '/Game/CastleDefender/Shared/Materials/Imported/M_Landscape': (0.6, True, [C + 'MI_Castle_Ground']),
}
BACKUP = os.path.join(HERE, 'wet410_backup.json')
log = ['#410 rain wetness %s%s' % ('--swap' if SWAP else '--revert' if REVERT else 'build', ' (DRY RUN)' if DRY else '')]

# ---- HLSL (each Custom node recomputes the shared masks; the compiler folds the duplicates)
COMMON = r'''
float w = WetPreview >= 0 ? saturate(WetPreview) : saturate(Wet);
float up = saturate((NWS.z - 0.75) / 0.2);                       // only floors and tops pool water
float2 q = P.xy / 600.0;                                          // value noise, ~6 m blobs (RESEARCH: 4-8 m, no per-tile repeat)
float2 i0 = floor(q), f = frac(q); f = f * f * (3 - 2 * f);
float h00 = frac(sin(dot(i0, float2(127.1, 311.7))) * 43758.5);
float h10 = frac(sin(dot(i0 + float2(1, 0), float2(127.1, 311.7))) * 43758.5);
float h01 = frac(sin(dot(i0 + float2(0, 1), float2(127.1, 311.7))) * 43758.5);
float h11 = frac(sin(dot(i0 + float2(1, 1), float2(127.1, 311.7))) * 43758.5);
float n = lerp(lerp(h00, h10, f.x), lerp(h01, h11, f.x), f.y);
float height = lerp(AO, n, 0.3);                                  // low = cracks/cavities (dark AO) + 30 % world noise
float level = saturate((w - 0.55) / 0.45);                        // RESEARCH: puddles only once Wet > 0.55
float pud = Puddles * up * saturate((level - height) / 0.08);     // water depth band 0.08
float film = w * lerp(0.6, 1.0, up);                               // walls get 60 % (they shed water)
'''
CODE_BC = COMMON + r'''
float3 c = lerp(BC, BC * BC, saturate(Porosity * sqrt(film)));     // KB/Lagarde: lerp(base, base^2, porosity*wet); dark lingers (sqrt)
c = lerp(c, c * 0.8, pud);                                         // standing water: a touch darker
return max(c, 0.012);                                              // wet colour floor ~30 sRGB
'''
CODE_R = COMMON + r'''
float r = R * lerp(1.0, 0.5, film * saturate(Porosity * 1.6));     // porous: x0.5 at full wet (stone ~0.8 -> ~0.4)
r = lerp(r, min(r, 0.13), film * film);                            // thin water film 0.1-0.15, shine leaves first (w^2)
return lerp(r, 0.04, pud);                                         // standing water 0.04
'''
CODE_N = COMMON + r'''
float3 t = normalize(N);
float fl = max(0.25 * film, pud >= 0.98 ? 1.0 : pud * 0.8);      // film flattens 25 %, water fills the relief
return normalize(lerp(t, float3(0, 0, 1), fl));
'''


def custom(m, code, ins, otype, x, y, desc):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code); e.set_editor_property('output_type', otype); e.set_editor_property('description', desc)
    lst = []
    for n in ins:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); lst.append(ci)
    e.set_editor_property('inputs', lst)
    return e


def src(m, prop):
    """(node, output name) feeding a material output, or (None, '')."""
    try: n = MEL.get_material_property_input_node(m, prop)
    except Exception: n = None
    if n is None: return None, ''
    try: o = MEL.get_material_property_input_node_output_name(m, prop)
    except Exception: o = ''
    return n, o


def scalar(m, name, val, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', val); return e


def const(m, val, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, x, y); e.set_editor_property('r', val); return e


def wetify(src_path, porosity, puddles):
    dst = src_path + '_Wet410'
    log.append('%s -> %s (porosity %.2f, puddles %s)' % (src_path.split('/')[-1], dst.split('/')[-1], porosity, puddles))
    if DRY:
        m = unreal.load_asset(src_path)
        for nm, p in (('BaseColor', MP.MP_BASE_COLOR), ('Roughness', MP.MP_ROUGHNESS), ('Normal', MP.MP_NORMAL), ('AO', MP.MP_AMBIENT_OCCLUSION)):
            n, o = src(m, p); log.append('    %-9s <- %s %s' % (nm, n.get_name() if n else '(not connected)', o))
        return
    if EAL.does_asset_exist(dst): EAL.delete_asset(dst)            # our own copy: rebuilt from the live master every run
    m = EAL.duplicate_asset(src_path, dst)
    x0, y0 = -900, 0
    attrs = m.get_editor_property('use_material_attributes')
    if attrs:   # landscape-style master: Break -> wet -> Make, every other attribute passed through
        an, ao_ = src(m, MP.MP_MATERIAL_ATTRIBUTES)
        if an is None: log.append('    SKIP: Material Attributes not connected'); return
        brk = MEL.create_material_expression(m, unreal.MaterialExpressionBreakMaterialAttributes, x0 - 900, y0)
        mk = MEL.create_material_expression(m, unreal.MaterialExpressionMakeMaterialAttributes, x0 + 500, y0)
        MEL.connect_material_expressions(an, ao_, brk, '')
        passed = []
        for pin in ('Metallic', 'Specular', 'EmissiveColor', 'Opacity', 'OpacityMask', 'Tangent', 'WorldPositionOffset',
                    'SubsurfaceColor', 'ClearCoat', 'ClearCoatRoughness', 'AmbientOcclusion', 'Refraction', 'PixelDepthOffset',
                    'ShadingModel', 'Displacement', 'Anisotropy'):
            try:
                if MEL.connect_material_expressions(brk, pin, mk, pin): passed.append(pin)
            except Exception: pass
        log.append('    material attributes: passed through %s' % passed)
        MEL.connect_material_property(mk, '', MP.MP_MATERIAL_ATTRIBUTES)
        bc, bco, r, ro, nn, no, ao, aoo = brk, 'BaseColor', brk, 'Roughness', brk, 'Normal', brk, 'AmbientOcclusion'
    else:
        bc, bco = src(m, MP.MP_BASE_COLOR)
        if bc is None: log.append('    SKIP: Base Color not connected'); return
        r, ro = src(m, MP.MP_ROUGHNESS); nn, no = src(m, MP.MP_NORMAL); ao, aoo = src(m, MP.MP_AMBIENT_OCCLUSION)
    wet = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, x0 - 500, y0)
    wet.set_editor_property('collection', unreal.load_asset(MPC)); wet.set_editor_property('parameter_name', 'Wet')
    prev = scalar(m, 'WetPreview', -1.0, x0 - 500, y0 + 120)
    por = scalar(m, 'Porosity', porosity, x0 - 500, y0 + 240)
    pud = scalar(m, 'Puddles', 1.0 if puddles else 0.0, x0 - 500, y0 + 360)
    nws = MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, x0 - 500, y0 + 480)
    pos = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, x0 - 500, y0 + 600)
    ins = ['Wet', 'WetPreview', 'Porosity', 'Puddles', 'NWS', 'P', 'AO']
    F1, F3 = unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.CustomMaterialOutputType.CMOT_FLOAT3
    nodes = {'BC': custom(m, CODE_BC, ins + ['BC'], F3, x0, y0, 'Wet410 BaseColor'),
             'R': custom(m, CODE_R, ins + ['R'], F1, x0, y0 + 300, 'Wet410 Roughness'),
             'N': custom(m, CODE_N, ins + ['N'], F3, x0, y0 + 600, 'Wet410 Normal')}
    for e in nodes.values():
        for s, o, name in ((wet, '', 'Wet'), (prev, '', 'WetPreview'), (por, '', 'Porosity'), (pud, '', 'Puddles'), (nws, '', 'NWS'), (pos, '', 'P')):
            MEL.connect_material_expressions(s, o, e, name)
        if ao is not None: MEL.connect_material_expressions(ao, aoo, e, 'AO')
        else: MEL.connect_material_expressions(const(m, 1.0, x0 - 300, y0 + 720), '', e, 'AO')
    out = (lambda e, prop, pin: MEL.connect_material_expressions(e, '', mk, pin)) if attrs else \
          (lambda e, prop, pin: MEL.connect_material_property(e, '', prop))
    MEL.connect_material_expressions(bc, bco, nodes['BC'], 'BC'); out(nodes['BC'], MP.MP_BASE_COLOR, 'BaseColor')
    if r is not None: MEL.connect_material_expressions(r, ro, nodes['R'], 'R')
    else: MEL.connect_material_expressions(const(m, 0.7, x0 - 300, y0 + 300), '', nodes['R'], 'R')
    out(nodes['R'], MP.MP_ROUGHNESS, 'Roughness')
    if nn is not None:
        MEL.connect_material_expressions(nn, no, nodes['N'], 'N'); out(nodes['N'], MP.MP_NORMAL, 'Normal')
    else:
        log.append('    (no Normal input: puddles keep the base relief)')
    MEL.recompile_material(m); EAL.save_asset(dst)
    log.append('    built, inputs: BC %s, R %s, N %s, AO %s' % (bc.get_name(), r.get_name() if r else 'const', nn.get_name() if nn else '-', ao.get_name() if ao else 'const 1'))


if not (SWAP or REVERT):
    # Force-deleting a wet copy that a loaded MI still points at crashes 5.8 (16:18 i5). Our lookdev MIs are the only
    # users before the swap: delete them first (preview410_ue.py remakes them). After a --swap, --revert before rebuilding.
    swapped = [m for _p, (_a, _b, mis) in TARGETS.items() for m in mis if EAL.does_asset_exist(m)
               and unreal.load_asset(m).get_editor_property('parent').get_path_name().split('.')[0].endswith('_Wet410')]
    if swapped: raise RuntimeError('swapped MIs use the wet copies (%s): run --revert before rebuilding' % swapped)
    if not DRY:
        for a in EAL.list_assets('/Game/CastleDefender/Dev/Wet410', recursive=True):
            EAL.delete_asset(a.split('.')[0]); log.append('removed lookdev ' + a.split('/')[-1].split('.')[0])
        unreal.SystemLibrary.collect_garbage()
    for path, (p, puddles, _mis) in TARGETS.items():
        if not EAL.does_asset_exist(path): log.append('MISSING ' + path); continue
        wetify(path, p, puddles)
    log.append('Next: lookdev (WetPreview 0 vs 1 on a preview MI), owner OK, then --swap --dry-run / --swap.')
else:
    back = json.load(open(BACKUP)) if os.path.exists(BACKUP) else {}
    for path, (_p, _pd, mis) in TARGETS.items():
        for mi_path in mis:
            if not EAL.does_asset_exist(mi_path): log.append('MISSING ' + mi_path); continue
            mi = unreal.load_asset(mi_path); cur = mi.get_editor_property('parent').get_path_name().split('.')[0]
            if SWAP:
                if cur.endswith('_Wet410'): log.append('%s already wet' % mi_path.split('/')[-1]); continue
                if not EAL.does_asset_exist(path + '_Wet410'): log.append('build first: %s_Wet410 missing' % path); continue
                log.append('%s: %s -> %s_Wet410' % (mi_path.split('/')[-1], cur.split('/')[-1], path.split('/')[-1]))
                if not DRY:
                    back[mi_path] = cur; MEL.set_material_instance_parent(mi, unreal.load_asset(path + '_Wet410')); EAL.save_asset(mi_path)
            elif mi_path in back:
                log.append('%s back to %s' % (mi_path.split('/')[-1], back[mi_path].split('/')[-1]))
                if not DRY:
                    MEL.set_material_instance_parent(mi, unreal.load_asset(back[mi_path])); EAL.save_asset(mi_path); back.pop(mi_path)
    if not DRY: json.dump(back, open(BACKUP, 'w'), indent=1)

out = '\n'.join(log)
open(os.path.join(HERE, 'wet410_%s%s.txt' % ('swap' if SWAP else 'revert' if REVERT else 'build', '_dry' if DRY else '')), 'w').write(out)
unreal.log(out); print(out)
