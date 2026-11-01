"""WinterKeep #390: UE 5.3 editor script (Master runs it; Output Log > Python, or File > Execute Python Script).

  py "<repo>/handoffs/winter-map/ue/winterkeep_ue.py" --dry-run              read-only: API check + what each step would do
  py ".../winterkeep_ue.py" --list                                       read-only: winter-usable assets in the project
  py ".../winterkeep_ue.py" --step assets      textures + M_WK_Landscape + MF_WK_SnowCover + M_WK_SnowProp (+ MIs)
  py ".../winterkeep_ue.py" --step level       NEW level /Game/CastleDefender/Maps/WinterKeep (World Partition)
     (then the Landscape import clicks in README.md)
  py ".../winterkeep_ue.py" --step check       verifies the landscape (size, scale, location, material, layers)
  py ".../winterkeep_ue.py" --step dress       HISM dressing per 256 m cell (trees, rocks, shrubs, drifts)
  py ".../winterkeep_ue.py" --step light --preset overcast|lowsun|blizzard|night
  py ".../winterkeep_ue.py" --step remove      deletes ONLY actors tagged WK390 in the WinterKeep level

Never touches ThirdPersonMap, existing materials or decals: everything is new under /Game/CastleDefender/WinterKeep/.
5.3 notes: World Partition levels save with modify + save_dirty_packages (not save_current_level).
"""
import json, math, os, sys
import unreal

ARGS = sys.argv[1:]
DRY = '--dry-run' in ARGS
def arg(k, d=None): return ARGS[ARGS.index(k) + 1] if k in ARGS else d
STEP, PRESET = arg('--step'), arg('--preset', 'overcast')
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.normpath(os.path.join(HERE, '..', 'terrain', 'out'))
ROOT = '/Game/CastleDefender/WinterKeep'; LEVEL = '/Game/CastleDefender/Maps/WinterKeep'; TAG = 'WK390'
AT = unreal.AssetToolsHelpers.get_asset_tools(); EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
LAYOUT = json.load(open(os.path.join(OUT, 'layout.json')))
LOG = []
def say(*a):
    s = ' '.join(str(x) for x in a); LOG.append(s); unreal.log('[WK390] ' + s); print('[WK390] ' + s)

# calibrated layer values (linear albedo, roughness): RESEARCH.md / knowledge base. Never 1.0 white.
LAYERS = [  # name,          albedo (linear RGB),     rough, ripple normal
    ('Snow_Fresh',  (0.80, 0.82, 0.86), 0.68, 1.0),
    ('Snow_Packed', (0.66, 0.68, 0.72), 0.50, 0.6),
    ('Rock_Scoured', (0.065, 0.068, 0.072), 0.82, 0.0),
    ('Ice',         (0.012, 0.018, 0.024), 0.06, 0.0),
    ('FrozenMud',   (0.075, 0.062, 0.050), 0.55, 0.0),
    ('ForestFloor', (0.56, 0.58, 0.60), 0.70, 0.3),
    ('Road',        (0.36, 0.34, 0.32), 0.55, 0.0),
    ('RealmMelt',   (0.022, 0.020, 0.020), 0.12, 0.0),   # wet black ground: darker + glossy
]

def world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
def in_winterkeep():
    w = world(); return w and w.get_path_name().split('.')[0] == LEVEL
def save_level():
    w = world(); w.modify(); unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

# ------------------------------------------------------------------ API check (dry run)
def api_check():
    need = {'MaterialEditingLibrary.create_material_expression': hasattr(MEL, 'create_material_expression'),
            'MaterialEditingLibrary.create_material_expression_in_function': hasattr(MEL, 'create_material_expression_in_function'),
            'MaterialExpressionLandscapeLayerSample': hasattr(unreal, 'MaterialExpressionLandscapeLayerSample'),
            'LevelEditorSubsystem.new_level_from_template': hasattr(LES, 'new_level_from_template'),
            'HierarchicalInstancedStaticMeshComponent': hasattr(unreal, 'HierarchicalInstancedStaticMeshComponent'),
            'LandscapeProxy (find landscape)': hasattr(unreal, 'LandscapeProxy'),
            'files: layout.json / scatter.json': os.path.exists(os.path.join(OUT, 'scatter.json'))}
    for k, v in need.items(): say(('OK   ' if v else 'MISS ') + k)
    say('Landscape creation is NOT scriptable in 5.3 -> README clicks (Landscape mode > Import from File).')
    return all(need.values())

# ------------------------------------------------------------------ list project assets useful for winter
KEYS = {'conifer': ('pine', 'spruce', 'fir', 'conifer'), 'birch': ('birch',), 'rock': ('rock', 'boulder', 'cliff', 'stone_'),
        'shrub': ('shrub', 'bush', 'dead'), 'snow': ('snow', 'ice', 'frost', 'icicle'), 'niagara': ('snow', 'rain', 'weather', 'blizzard')}
def find_assets():
    ar = unreal.AssetRegistryHelpers.get_asset_registry(); found = {k: [] for k in KEYS}
    for cls, kinds in ((('/Script/Engine', 'StaticMesh'), ('conifer', 'birch', 'rock', 'shrub', 'snow')), (('/Script/Niagara', 'NiagaraSystem'), ('niagara',))):
        flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath(*cls)], package_paths=['/Game'], recursive_paths=True)
        for a in ar.get_assets(flt):
            p = str(a.package_name); low = p.lower()
            if '/winterkeep/' in low: continue
            for k in kinds:
                if any(w in low.split('/')[-1] for w in KEYS[k]): found[k].append(p)
    return {k: sorted(v) for k, v in found.items()}
def pick(found, kind, prefer=()):
    lst = found.get(kind, [])
    for p in prefer:
        for a in lst:
            if p in a.lower(): return a
    return lst[0] if lst else None

# ------------------------------------------------------------------ assets: textures, landscape material, snow-cover MF
def import_tex(png, name, kind='gray'):
    dst = ROOT + '/Textures'; full = dst + '/' + name
    if EAL.does_asset_exist(full): return unreal.load_asset(full)
    t = unreal.AssetImportTask(); t.filename = os.path.join(OUT, png); t.destination_path = dst; t.destination_name = name
    t.automated = True; t.save = True; t.replace_existing = False; AT.import_asset_tasks([t])
    tex = unreal.load_asset(full)
    comp = {'normal': unreal.TextureCompressionSettings.TC_NORMALMAP, 'masks': unreal.TextureCompressionSettings.TC_MASKS,
            'gray': unreal.TextureCompressionSettings.TC_GRAYSCALE}[kind]
    tex.set_editor_property('srgb', False); tex.set_editor_property('compression_settings', comp)
    EAL.save_loaded_asset(tex); return tex

def new_material(name):
    full = ROOT + '/Materials/' + name
    if EAL.does_asset_exist(full): EAL.delete_asset(full)          # only ever our own WK assets
    return AT.create_asset(name, ROOT + '/Materials', unreal.Material, unreal.MaterialFactoryNew())

def X(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e
def C(a, ao, b, bi): MEL.connect_material_expressions(a, ao, b, bi)

def build_landscape_material(macro, ripple):
    m = new_material('M_WK_Landscape')
    uvw = X(m, unreal.MaterialExpressionWorldPosition, -2200, 0)
    # macro variation: world-space, 2 scales, +-12 % on albedo only (kills tiling, keeps calibration)
    mac = []
    for i, size in enumerate((9000.0, 1700.0)):
        msk = X(m, unreal.MaterialExpressionComponentMask, -2000, i * 160, r=True, g=True, b=False, a=False); C(uvw, '', msk, '')
        div = X(m, unreal.MaterialExpressionDivide, -1850, i * 160, const_b=size); C(msk, '', div, 'A')
        smp = X(m, unreal.MaterialExpressionTextureSample, -1700, i * 160, texture=macro, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE); C(div, '', smp, 'UVs')
        mac.append(smp)
    mm = X(m, unreal.MaterialExpressionMultiply, -1500, 80); C(mac[0], 'R', mm, 'A'); C(mac[1], 'R', mm, 'B')
    var = X(m, unreal.MaterialExpressionLinearInterpolate, -1350, 80, const_a=0.88, const_b=1.12); C(mm, '', var, 'Alpha')
    # wind-ripple normal, world aligned (ripples run across the NW wind everywhere)
    rmsk = X(m, unreal.MaterialExpressionComponentMask, -2000, 400, r=True, g=True, b=False, a=False); C(uvw, '', rmsk, '')
    rdiv = X(m, unreal.MaterialExpressionDivide, -1850, 400, const_b=180.0); C(rmsk, '', rdiv, 'A')
    rn = X(m, unreal.MaterialExpressionTextureSample, -1700, 400, texture=ripple, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL); C(rdiv, '', rn, 'UVs')
    flat = X(m, unreal.MaterialExpressionConstant3Vector, -1700, 600, constant=unreal.LinearColor(0, 0, 1, 0))
    # weighted sums: every layer = one LandscapeLayerSample (this also registers the paint layer)
    col = rough = nstr = None
    for i, (name, alb, r, rip) in enumerate(LAYERS):
        y = 800 + i * 220
        w = X(m, unreal.MaterialExpressionLandscapeLayerSample, -1200, y, parameter_name=name, preview_weight=1.0 if i == 0 else 0.0)
        c3 = X(m, unreal.MaterialExpressionConstant3Vector, -1200, y + 100, constant=unreal.LinearColor(*alb, 1))
        mc = X(m, unreal.MaterialExpressionMultiply, -950, y); C(w, '', mc, 'A'); C(c3, '', mc, 'B')
        mr = X(m, unreal.MaterialExpressionMultiply, -950, y + 100, const_b=r); C(w, '', mr, 'A')
        if col is None: col, rough = mc, mr
        else:
            a1 = X(m, unreal.MaterialExpressionAdd, -750, y); C(col, '', a1, 'A'); C(mc, '', a1, 'B'); col = a1
            a2 = X(m, unreal.MaterialExpressionAdd, -750, y + 100); C(rough, '', a2, 'A'); C(mr, '', a2, 'B'); rough = a2
        if rip > 0:
            mn = X(m, unreal.MaterialExpressionMultiply, -950, y + 160, const_b=rip); C(w, '', mn, 'A')
            if nstr is None: nstr = mn
            else: a3 = X(m, unreal.MaterialExpressionAdd, -750, y + 160); C(nstr, '', a3, 'A'); C(mn, '', a3, 'B'); nstr = a3
    bc = X(m, unreal.MaterialExpressionMultiply, -500, 300); C(col, '', bc, 'A'); C(var, '', bc, 'B')
    nl = X(m, unreal.MaterialExpressionLinearInterpolate, -500, 500); C(flat, '', nl, 'A'); C(rn, 'RGB', nl, 'B'); C(nstr, '', nl, 'Alpha')
    MEL.connect_material_property(bc, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(nl, '', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_loaded_asset(m); return m

def build_snow_cover_function():
    """MF_WK_SnowCover: world-aligned top mask (snow on up-facing surfaces only) + windward rime. For props."""
    full = ROOT + '/Materials/MF_WK_SnowCover'
    if EAL.does_asset_exist(full): EAL.delete_asset(full)
    f = AT.create_asset('MF_WK_SnowCover', ROOT + '/Materials', unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    def F(cls, x, y, **p):
        e = MEL.create_material_expression_in_function(f, cls, x, y)
        for k, v in p.items(): e.set_editor_property(k, v)
        return e
    i_bc = F(unreal.MaterialExpressionFunctionInput, -1400, 0, input_name='BaseColor', input_type=unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, sort_priority=0)
    i_r = F(unreal.MaterialExpressionFunctionInput, -1400, 120, input_name='Roughness', input_type=unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, sort_priority=1)
    i_amt = F(unreal.MaterialExpressionFunctionInput, -1400, 240, input_name='SnowAmount', input_type=unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, sort_priority=2, use_preview_value_as_default=True, preview_value=unreal.Vector4(0.6, 0, 0, 0))
    nws = F(unreal.MaterialExpressionVertexNormalWS, -1400, 400)
    up = F(unreal.MaterialExpressionComponentMask, -1200, 400, r=False, g=False, b=True, a=False); C(nws, '', up, '')
    # threshold falls as SnowAmount rises: 0 -> only flat tops, 1 -> down to ~45 deg
    th = F(unreal.MaterialExpressionOneMinus, -1200, 260); C(i_amt, '', th, '')
    sub = F(unreal.MaterialExpressionSubtract, -1000, 400); C(up, '', sub, 'A'); C(th, '', sub, 'B')
    sh = F(unreal.MaterialExpressionMultiply, -850, 400, const_b=6.0); C(sub, '', sh, 'A')
    top = F(unreal.MaterialExpressionSaturate, -700, 400); C(sh, '', top, '')
    # rime: faces turned INTO the NW wind (wind blows toward +X,+Y in UE: from the north-west); light frost, not snow
    wind = F(unreal.MaterialExpressionConstant3Vector, -1400, 600, constant=unreal.LinearColor(-0.707, -0.707, 0, 0))
    dp = F(unreal.MaterialExpressionDotProduct, -1200, 600); C(nws, '', dp, 'A'); C(wind, '', dp, 'B')
    rm = F(unreal.MaterialExpressionMultiply, -1000, 600, const_b=0.35); C(dp, '', rm, 'A')
    rime = F(unreal.MaterialExpressionSaturate, -850, 600); C(rm, '', rime, '')
    snow = F(unreal.MaterialExpressionConstant3Vector, -1000, 160, constant=unreal.LinearColor(0.80, 0.82, 0.86, 1))
    frost = F(unreal.MaterialExpressionConstant3Vector, -1000, 760, constant=unreal.LinearColor(0.62, 0.65, 0.70, 1))
    l1 = F(unreal.MaterialExpressionLinearInterpolate, -500, 500); C(i_bc, '', l1, 'A'); C(frost, '', l1, 'B'); C(rime, '', l1, 'Alpha')
    l2 = F(unreal.MaterialExpressionLinearInterpolate, -300, 300); C(l1, '', l2, 'A'); C(snow, '', l2, 'B'); C(top, '', l2, 'Alpha')
    lr = F(unreal.MaterialExpressionLinearInterpolate, -300, 450, const_b=0.68); C(i_r, '', lr, 'A'); C(top, '', lr, 'Alpha')
    o_bc = F(unreal.MaterialExpressionFunctionOutput, -50, 300, output_name='BaseColor', sort_priority=0); C(l2, '', o_bc, '')
    o_r = F(unreal.MaterialExpressionFunctionOutput, -50, 450, output_name='Roughness', sort_priority=1); C(lr, '', o_r, '')
    o_m = F(unreal.MaterialExpressionFunctionOutput, -50, 600, output_name='SnowMask', sort_priority=2); C(top, '', o_m, '')
    MEL.update_material_function(f); EAL.save_loaded_asset(f); return f

def build_snow_prop_material(mf):
    """M_WK_SnowProp: parent for snowy prop instances (BaseColor/ORM/Normal params) through MF_WK_SnowCover."""
    m = new_material('M_WK_SnowProp')
    bc = X(m, unreal.MaterialExpressionTextureSampleParameter2D, -900, 0, parameter_name='BaseColor', texture=unreal.load_asset('/Engine/EngineMaterials/DefaultDiffuse'))
    orm = X(m, unreal.MaterialExpressionTextureSampleParameter2D, -900, 260, parameter_name='ORM', sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, texture=unreal.load_asset(ROOT + '/Textures/T_WK_DefaultORM'))
    nm = X(m, unreal.MaterialExpressionTextureSampleParameter2D, -900, 520, parameter_name='Normal', sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, texture=unreal.load_asset('/Engine/EngineMaterials/DefaultNormal'))
    amt = X(m, unreal.MaterialExpressionScalarParameter, -900, 760, parameter_name='SnowAmount', default_value=0.6)
    call = X(m, unreal.MaterialExpressionMaterialFunctionCall, -500, 200); call.set_material_function(mf)
    C(bc, 'RGB', call, 'BaseColor'); C(orm, 'G', call, 'Roughness'); C(amt, '', call, 'SnowAmount')
    MEL.connect_material_property(call, 'BaseColor', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(call, 'Roughness', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_loaded_asset(m); return m

def step_assets():
    if DRY:
        say('would import T_WK_MacroNoise, T_WK_SnowRipple_N to', ROOT + '/Textures')
        say('would build M_WK_Landscape (8 layers: %s), MF_WK_SnowCover, M_WK_SnowProp' % ', '.join(l[0] for l in LAYERS)); return
    macro = import_tex('T_WK_MacroNoise.png', 'T_WK_MacroNoise'); ripple = import_tex('T_WK_SnowRipple_N.png', 'T_WK_SnowRipple_N', 'normal')
    import_tex('T_WK_DefaultORM.png', 'T_WK_DefaultORM', 'masks')
    build_landscape_material(macro, ripple); mf = build_snow_cover_function(); pm = build_snow_prop_material(mf)
    full = ROOT + '/Materials/MI_WK_DriftSnow'
    if EAL.does_asset_exist(full): EAL.delete_asset(full)
    mi = AT.create_asset('MI_WK_DriftSnow', ROOT + '/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, pm); MEL.set_material_instance_scalar_parameter_value(mi, 'SnowAmount', 1.0); EAL.save_loaded_asset(mi)
    say('assets built under', ROOT)

# ------------------------------------------------------------------ level
def step_level():
    if EAL.does_asset_exist(LEVEL): say('level exists already:', LEVEL, '(not touched; open it)'); return
    if DRY: say('would create', LEVEL, 'from the Empty Open World template (World Partition)'); return
    ok = False
    for tpl in ('/Engine/Maps/Templates/OpenWorld', '/Engine/Maps/Templates/Template_Default'):
        if EAL.does_asset_exist(tpl):
            ok = LES.new_level_from_template(LEVEL, tpl); say('new level from', tpl, ok); break
    if not ok: ok = LES.new_level(LEVEL); say('new_level', ok)
    # the OpenWorld template brings its own small landscape: remove it (our own new level only)
    for a in EAS.get_all_level_actors():
        if a.get_class().get_name() in ('Landscape', 'LandscapeStreamingProxy'): say('removing template landscape', a.get_name()); EAS.destroy_actor(a)
    save_level()

# ------------------------------------------------------------------ check landscape after the import clicks
def step_check():
    if not in_winterkeep(): say('open', LEVEL, 'first'); return
    lands = [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == 'Landscape']
    if not lands: say('FAIL no Landscape: do the README import clicks'); return
    ls = lands[0]; loc = ls.get_actor_location(); sc = ls.get_actor_scale3d(); imp = LAYOUT['import']
    say('Landscape', ls.get_name(), 'loc', loc, 'scale', sc)
    ok_loc = abs(loc.x - imp['location_cm'][0]) < 1 and abs(loc.y - imp['location_cm'][1]) < 1 and abs(loc.z - imp['location_cm'][2]) < 1
    ok_sc = abs(sc.x - 100) < 0.01 and abs(sc.z - imp['scale'][2]) < 0.01
    say(('OK  ' if ok_loc else 'FIX ') + 'location should be', imp['location_cm']); say(('OK  ' if ok_sc else 'FIX ') + 'scale should be', imp['scale'])
    if not DRY and (not ok_loc or not ok_sc):
        ls.set_actor_location(unreal.Vector(*imp['location_cm']), False, False); ls.set_actor_scale3d(unreal.Vector(*imp['scale'])); say('fixed location/scale')
    mat = unreal.load_asset(ROOT + '/Materials/M_WK_Landscape')
    if ls.get_editor_property('landscape_material') != mat:
        say('landscape material ->', 'M_WK_Landscape' if not DRY else '(dry) would set M_WK_Landscape')
        if not DRY: ls.set_editor_property('landscape_material', mat)
    # spot heights: the landscape must match our heightmap at known points (castle 62 m, lake ice 3.65 m)
    for name, p in (('castle', LAYOUT['castle_centre']), ('lake', LAYOUT['lake']['centre']), ('bridge', LAYOUT['bridge'])):
        hit = unreal.SystemLibrary.line_trace_single(world(), unreal.Vector(p[0], p[1], 60000), unreal.Vector(p[0], p[1], -10000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        z = hit.to_tuple()[4].z if hit else None
        say('height', name, 'expected ~%.0f cm' % p[2], 'got', z)
    if not DRY: save_level()

# ------------------------------------------------------------------ dressing (HISM per 256 m World Partition cell)
DRESS = {  # kind: (asset kind, prefer words, base scale, cull start/end cm, shadows)
    'Spruce': ('conifer', ('spruce', 'fir', 'pine'), 1.0, 25000, 60000, True),
    'Spruce_Young': ('conifer', ('young', 'small', 'spruce'), 0.55, 12000, 30000, True),
    'Birch': ('birch', (), 1.0, 15000, 40000, True),
    'Rock_Large': ('rock', ('boulder', 'large', 'cliff'), 1.0, 30000, 80000, True),
    'Rock_Small': ('rock', ('small', 'rubble', 'stone'), 0.5, 6000, 12000, False),
    'DeadShrub': ('shrub', ('dead',), 1.0, 4000, 9000, False),
    'Drift_Mound': (None, (), 1.0, 20000, 50000, True),   # engine sphere squashed along the wind, MI_WK_DriftSnow (all snow)
}
def step_dress():
    if not in_winterkeep(): say('open', LEVEL, 'first'); return
    data = json.load(open(os.path.join(OUT, 'scatter.json'))); found = find_assets()
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    total = 0
    for kind, (akind, prefer, base, c0, c1, shadow) in DRESS.items():
        mesh = '/Engine/BasicShapes/Sphere' if akind is None else pick(found, akind, prefer)
        cells = data['kinds'].get(kind, {}); n = sum(len(v) for v in cells.values())
        say('%-12s %6d instances in %3d cells  mesh=%s' % (kind, n, len(cells), mesh)); total += n
        if DRY or not mesh: continue
        sm = unreal.load_asset(mesh)
        for cell, pts in cells.items():
            x0 = sum(p[0] for p in pts) / len(pts); y0 = sum(p[1] for p in pts) / len(pts)
            act = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x0, y0, 0), unreal.Rotator(0, 0, 0))
            act.set_actor_label('WK_%s_%s' % (kind, cell)); act.tags = [unreal.Name(TAG)]
            h, _ = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=sds.k2_gather_subobject_data_for_instance(act)[0], new_class=unreal.HierarchicalInstancedStaticMeshComponent, blueprint_context=None))
            comp = [c for c in act.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)][0]
            comp.set_static_mesh(sm); comp.set_collision_profile_name('NoCollision' if kind not in ('Spruce', 'Rock_Large') else 'BlockAll')
            comp.set_editor_property('cast_shadow', shadow); comp.set_cull_distances(c0, c1)
            if kind == 'Drift_Mound': comp.set_material(0, unreal.load_asset(ROOT + '/Materials/MI_WK_DriftSnow'))
            for x, y, z, yaw, s in pts:
                sc = (s * base * 9, s * base * 4.5, s * base * 1.2) if kind == 'Drift_Mound' else (s * base,) * 3
                yaw = 315 - 90 if kind == 'Drift_Mound' else yaw          # drifts lie along the wind
                comp.add_instance(unreal.Transform(unreal.Vector(x - x0, y - y0, z), unreal.Rotator(0, 0, yaw), unreal.Vector(*sc)), False)
    say('dress total', total, '(dry run)' if DRY else '')
    if not DRY: save_level()
    missing = [k for k, (a, *_r) in DRESS.items() if a and not pick(found, a)]
    if missing: say('NO project mesh for', missing, '-> skipped; see README "missing assets"')

# ------------------------------------------------------------------ lighting presets (locked exposure)
PRESETS = {  # sun pitch, yaw (UE: direction the light TRAVELS; X east, Y south), lux, Kelvin, skylight, fog, EV100 locked, note
    'overcast': (-50, -135, 15000, 6500, 1.0, 0.035, 12.0, 'from the NW-ish high, soft (source angle 8), 2:1 key-to-shade'),
    'lowsun':   (-9, -45, 100000, 3600, 1.0, 0.012, 14.5, 'sun from the SW at 9 deg (atmosphere reddens it), long blue shadows'),
    'blizzard': (-45, -135, 6000, 7000, 0.9, 0.22, 11.0, 'sight lines cut to ~80-150 m'),
    'night':    (-35, -110, 0.26, 4000, 0.15, 0.03, -2.5, 'moon 0.26 lux from the SSE; blue by Purkinje, on purpose'),
}
def step_light():
    if not in_winterkeep(): say('open', LEVEL, 'first'); return
    p = PRESETS[PRESET]; say('preset', PRESET, p)
    if DRY: return
    def get(cls, label):
        for a in EAS.get_all_level_actors():
            if a.get_actor_label() == label: return a
        a = EAS.spawn_actor_from_class(cls, unreal.Vector(0, 0, 50000), unreal.Rotator(0, 0, 0)); a.set_actor_label(label); a.tags = [unreal.Name(TAG)]; return a
    sun = get(unreal.DirectionalLight, 'WK_Sun'); sun.set_actor_rotation(unreal.Rotator(0, p[0], p[1]), False)
    lc = sun.light_component; lc.set_intensity(p[2]); lc.set_editor_property('use_temperature', True); lc.set_editor_property('temperature', p[3])
    lc.set_editor_property('atmosphere_sun_light', True); lc.set_editor_property('source_angle', 0.5357 if PRESET != 'overcast' else 8.0)
    get(unreal.SkyAtmosphere, 'WK_SkyAtmosphere')
    sky = get(unreal.SkyLight, 'WK_SkyLight'); sky.light_component.set_editor_property('real_time_capture', True); sky.light_component.set_intensity(p[4])
    fog = get(unreal.ExponentialHeightFog, 'WK_Fog'); fc = fog.component
    fc.set_editor_property('fog_density', p[5]); fc.set_editor_property('enable_volumetric_fog', True); fc.set_editor_property('volumetric_fog_scattering_distribution', 0.9)
    pp = get(unreal.PostProcessVolume, 'WK_PostProcess'); pp.set_editor_property('unbound', True); s = pp.settings
    # knowledge base: locked exposure = Histogram with Min EV100 = Max EV100 (UE5 extended luminance range: values are EV100)
    for k, v in (('override_auto_exposure_method', True), ('auto_exposure_method', unreal.AutoExposureMethod.AEM_HISTOGRAM),
                 ('override_auto_exposure_bias', True), ('auto_exposure_bias', 0.0), ('override_auto_exposure_min_brightness', True), ('auto_exposure_min_brightness', p[6]),
                 ('override_auto_exposure_max_brightness', True), ('auto_exposure_max_brightness', p[6]),
                 ('override_local_exposure_highlight_contrast_scale', True), ('local_exposure_highlight_contrast_scale', 0.8),
                 ('override_local_exposure_shadow_contrast_scale', True), ('local_exposure_shadow_contrast_scale', 0.8),
                 ('override_film_toe', True), ('film_toe', 0.45)):
        try: s.set_editor_property(k, v)
        except Exception as e: say('skip', k, e)
    pp.set_editor_property('settings', s)
    say('locked EV100 =', p[6], '|', p[7]); save_level()

def step_remove():
    if not in_winterkeep(): say('open', LEVEL, 'first (remove only works inside WinterKeep)'); return
    acts = [a for a in EAS.get_all_level_actors() if unreal.Name(TAG) in a.tags]
    say('remove', len(acts), 'WK390 actors', '(dry run)' if DRY else '')
    if not DRY:
        for a in acts: EAS.destroy_actor(a)
        save_level()

# ------------------------------------------------------------------ main
if '--list' in ARGS:
    for k, v in find_assets().items(): say(k, len(v), v[:12])
elif DRY and not STEP:
    api_check()
    for s in (step_assets, step_level): s()
    say('scatter kinds:', {k: sum(len(v) for v in c.values()) for k, c in json.load(open(os.path.join(OUT, 'scatter.json')))['kinds'].items()})
    say('presets:', list(PRESETS))
else:
    {'assets': step_assets, 'level': step_level, 'check': step_check, 'dress': step_dress, 'light': step_light, 'remove': step_remove}[STEP]()
out = os.path.join(HERE, 'wk390_log.txt'); open(out, 'w').write('\n'.join(LOG)); say('log ->', out)
