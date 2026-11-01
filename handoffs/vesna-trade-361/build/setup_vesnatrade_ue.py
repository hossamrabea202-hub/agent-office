# Vesna's Trade (#361, owner target 2026-10-31), step 1 (TGA). Editor script, safe to re-run. UE 5.3.
#   py "<repo>/handoffs/vesna-trade-361/build/setup_vesnatrade_ue.py"
# DRY_RUN = True (default): changes NOTHING, only checks every asset this needs and writes setup_vesnatrade.txt.
# DRY_RUN = False:
#   1. imports the 8 UI textures from assets/tga/VesnaTrade/textures into /Game/CastleDefender/UI/Trade/Vesna
#      (UI group, no mips, clamp, never stream)
#   2. RT_VTHero (512 x 768, RGBA16f, clear = transparent) + M_UI_VTHero (UI domain, translucent:
#      emissive = capture RGB x Exposure, opacity = 1 - capture alpha, because SceneColorHDR stores inverted opacity)
#   3. optional T_VT_Portrait: if a level actor has "Vesna" in its label, a one-off capture of her head and shoulders
#      (otherwise the frame's portrait corner stays dark; nothing else depends on it)
#   4. creates BPC_VesnaTrade (ActorComponent) + its variables + defaults (from trade_data.json)
#   5. hero: adds BPC_VesnaTrade as "VesnaTrade" and a SceneCaptureComponent2D "VTCapture" (tag VTCapture, show-only
#      list, manual capture, writes RT_VTHero)
# Nothing touches existing materials, textures, decals or the level (the portrait capture actor is deleted again).
import os, json, unreal

DRY_RUN = True

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'vesna-trade-361', 'build')
TEX_DIR = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'tga', 'VesnaTrade', 'textures'))
DEST = '/Game/CastleDefender/UI/Trade/Vesna'
COMP_DIR, COMP = '/Game/CastleDefender/Gameplay/Castle', 'BPC_VesnaTrade'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
NEEDS = ['/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet', '/Game/CastleDefender/Gameplay/Castle/BP_ArmoryHUD',
         '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD', '/Game/CastleDefender/UI/Fonts/Font_Cinzel',
         '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree', '/Game/CastleDefender/UI/Trade/SFX_TradeSwipe',
         '/Game/CastleDefender/UI/Trade/SFX_TradeBuy', '/Game/CastleDefender/UI/Trade/SFX_TradeFail', HERO]
TEXTURES = ['T_VT_Frame', 'T_VT_Atlas', 'T_VT_Icons', 'T_VT_Turn_Chest', 'T_VT_Turn_Shoulders', 'T_VT_Turn_Gauntlets', 'T_VT_Turn_Shins', 'T_VT_Turn_Boots']
EAL, BEL, MEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.MaterialEditingLibrary
D = json.load(open(os.path.join(HERE, 'trade_data.json')))
log = ['DRY_RUN = %s' % DRY_RUN]

# ---------------------------------------------------------------- 0. checks (both modes)
missing = [p for p in NEEDS if not EAL.does_asset_exist(p)]
for p in NEEDS: log.append('%-8s %s' % ('ok' if p not in missing else 'MISSING', p))
for n in TEXTURES:
    f = os.path.join(TEX_DIR, n + '.png'); log.append('%-8s %s' % ('ok' if os.path.exists(f) else 'MISSING', f))
setbp = unreal.load_asset(NEEDS[0]) if NEEDS[0] not in missing else None
if setbp:
    try:
        have = {str(v.get_editor_property('var_name')) for v in setbp.get_editor_property('new_variables')}
    except Exception:   # 5.3 Python has no 'new_variables': read the class defaults instead (Master patch 2026-11-01)
        _cdo = unreal.get_default_object(setbp.generated_class()); have = set()
        for _v in ('ObsOwned', 'WornEff', 'AvailMask', 'NextPrice', 'WornCount', 'Tier', 'ShieldLevel'):
            try: _cdo.get_editor_property(_v); have.add(_v)
            except Exception: pass
    for v in ('ObsOwned', 'WornEff', 'AvailMask', 'NextPrice', 'WornCount', 'Tier', 'ShieldLevel'):
        log.append('%-8s BPC_ObsidianSet.%s' % ('ok' if v in have else 'MISSING', v))
        if v not in have: missing.append('BPC_ObsidianSet.' + v)
log.append('existing BPC_VesnaTrade: %s' % EAL.does_asset_exist(COMP_DIR + '/' + COMP))
log.append('existing textures: %s' % [n for n in TEXTURES if EAL.does_asset_exist('%s/%s' % (DEST, n))])
vesna = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if 'vesna' in a.get_actor_label().lower()]
log.append('Vesna actors in the level (portrait): %s' % [a.get_actor_label() for a in vesna][:5])

def finish(msg):
    out = "Vesna's Trade setup (#361)\n" + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'setup_vesnatrade.txt'), 'w').write(out); unreal.log(out)

def apply():
    # ---------------------------------------------------------------- 1. textures
    tasks = []
    for n in TEXTURES:
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(TEX_DIR, n + '.png'))
        t.set_editor_property('destination_path', DEST); t.set_editor_property('destination_name', n)
        t.set_editor_property('replace_existing', True); t.set_editor_property('automated', True); t.set_editor_property('save', False)
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    tex = {}
    for n in TEXTURES:
        tx = unreal.load_asset('%s/%s' % (DEST, n)); tx.modify()
        tx.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tx.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tx.set_editor_property('never_stream', True); tx.set_editor_property('srgb', True)
        tx.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); tx.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
        tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)   # UserInterface2D: no block artefacts on text
        EAL.save_asset('%s/%s' % (DEST, n)); tex[n] = tx; log.append('texture %s %dx%d' % (n, tx.blueprint_get_size_x(), tx.blueprint_get_size_y()))

    # ---------------------------------------------------------------- 2. render target + hero material
    at = unreal.AssetToolsHelpers.get_asset_tools()
    rtp = DEST + '/RT_VTHero'
    if EAL.does_asset_exist(rtp):
        rt = unreal.load_asset(rtp)
    else:
        rt = at.create_asset('RT_VTHero', DEST, unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
    rt.set_editor_property('size_x', 512); rt.set_editor_property('size_y', 768)
    rt.set_editor_property('render_target_format', unreal.TextureRenderTargetFormat.RTF_RGBA16F)
    rt.set_editor_property('clear_color', unreal.LinearColor(0, 0, 0, 1))
    EAL.save_asset(rtp)
    mp = DEST + '/M_UI_VTHero'
    if EAL.does_asset_exist(mp):
        m = unreal.load_asset(mp); log.append('reusing M_UI_VTHero')
    else:
        m = at.create_asset('M_UI_VTHero', DEST, unreal.Material, unreal.MaterialFactoryNew())
        m.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
        m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
        ts = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSample, -700, 0)
        ts.set_editor_property('texture', rt); ts.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        ex = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 300)
        ex.set_editor_property('parameter_name', 'Exposure'); ex.set_editor_property('default_value', 1.0)
        mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, 0)
        MEL.connect_material_expressions(ts, 'RGB', mul, 'A'); MEL.connect_material_expressions(ex, '', mul, 'B')
        om = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -350, 200)
        MEL.connect_material_expressions(ts, 'A', om, '')
        MEL.connect_material_property(mul, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.connect_material_property(om, '', unreal.MaterialProperty.MP_OPACITY)
        MEL.recompile_material(m); log.append('created M_UI_VTHero')
    EAL.save_asset(mp)

    # ---------------------------------------------------------------- 3. optional portrait (one capture of the Vesna actor)
    portrait = None
    pp = DEST + '/T_VT_Portrait'
    if EAL.does_asset_exist(pp):
        portrait = unreal.load_asset(pp); log.append('reusing T_VT_Portrait')
    elif vesna:
        try:
            v = vesna[0]; o, ext = v.get_actor_bounds(True)
            head = unreal.Vector(o.x, o.y, o.z + ext.z * 0.62)
            fwd = v.get_actor_forward_vector()
            cam_loc = head + fwd * 120.0 + unreal.Vector(0, 0, 6)
            rot = unreal.MathLibrary.find_look_at_rotation(cam_loc, head)
            prt = at.create_asset('RT_VTPortrait', DEST, unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
            prt.set_editor_property('size_x', 690); prt.set_editor_property('size_y', 304)
            prt.set_editor_property('render_target_format', unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
            cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, rot)
            cc = cap.get_editor_property('capture_component2d')
            cc.set_editor_property('texture_target', prt); cc.set_editor_property('fov_angle', 40.0)
            cc.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
            cc.capture_scene()
            portrait = unreal.RenderingLibrary.render_target_create_static_texture2d_editor_only(prt, 'T_VT_Portrait')
            unreal.EditorLevelLibrary.destroy_actor(cap)
            if portrait:
                EAL.save_loaded_asset(portrait); log.append('portrait captured from %s -> %s' % (v.get_actor_label(), portrait.get_path_name()))
        except Exception as e:
            log.append('portrait skipped: %s' % e)
    else:
        log.append('portrait skipped: no actor named *Vesna* in this level (the corner stays dark)')

    # ---------------------------------------------------------------- 4. component, variables, defaults
    path = COMP_DIR + '/' + COMP
    if EAL.does_asset_exist(path):
        bp = unreal.load_asset(path); log.append('reusing ' + path)
    else:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
        bp = at.create_asset(COMP, COMP_DIR, unreal.Blueprint, f); log.append('created ' + path)
    I, Dd, Bo = BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('real'), BEL.get_basic_type_by_name('bool')
    Dd.set_editor_property('pin_sub_category', 'double')
    LCT = BEL.get_struct_type(unreal.LinearColor.static_struct())
    OBJ = BEL.get_object_reference_type
    ARR = BEL.get_array_type
    TYPES = {'int': I, 'double': Dd, 'bool': Bo}
    VARS = {n: TYPES[t] for n, (t, _) in D['vars'].items()}
    VARS.update({'Set': OBJ(setbp.generated_class()), 'Cap': OBJ(unreal.SceneCaptureComponent2D),
                 'FrameTex': OBJ(unreal.Texture2D), 'AtlasTex': OBJ(unreal.Texture2D), 'IconsTex': OBJ(unreal.Texture2D), 'PortraitTex': OBJ(unreal.Texture2D),
                 'HeroMat': OBJ(unreal.MaterialInterface), 'TurnTex': ARR(OBJ(unreal.Texture2D)),
                 'PieceIds': ARR(I), 'PieceDef': ARR(I), 'SlotIds': ARR(I), 'SlotRow': ARR(I), 'IconFromAtlas': ARR(Bo),
                 'NameUV': ARR(LCT), 'DefUV': ARR(LCT), 'TitleUV': ARR(LCT), 'TagUV': ARR(LCT), 'IconUV': ARR(LCT), 'ShieldUV': LCT})
    try:
        have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
    except Exception:   # 5.3 Python: no 'new_variables'; probe the class defaults instead (Master patch 2026-11-01)
        _cdo0 = unreal.get_default_object(bp.generated_class()); have = set()
        for _n in VARS:
            try: _cdo0.get_editor_property(_n); have.add(_n)
            except Exception: pass
    for n, t in VARS.items():
        if n not in have:
            if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add ' + n)
            log.append('  + %s.%s' % (COMP, n))
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    lc = lambda q: unreal.LinearColor(*q)
    for n, (t, v) in D['vars'].items(): cdo.set_editor_property(n, v)
    dd = D['data']
    for n in ('PieceIds', 'PieceDef', 'SlotIds', 'SlotRow', 'IconFromAtlas'): cdo.set_editor_property(n, dd[n])
    for n in ('NameUV', 'DefUV', 'TitleUV', 'TagUV', 'IconUV'): cdo.set_editor_property(n, [lc(q) for q in dd[n]])
    cdo.set_editor_property('ShieldUV', lc(dd['ShieldUV']))
    cdo.set_editor_property('TurnTex', [tex[q] if q else None for q in dd['TurnTex']])
    cdo.set_editor_property('FrameTex', tex['T_VT_Frame']); cdo.set_editor_property('AtlasTex', tex['T_VT_Atlas']); cdo.set_editor_property('IconsTex', tex['T_VT_Icons'])
    cdo.set_editor_property('PortraitTex', portrait); cdo.set_editor_property('HeroMat', m)
    EAL.save_asset(path)
    log.append('BPC_VesnaTrade defaults: %d pieces, %d slots, turntables %s' % (len(dd['PieceIds']), len(dd['SlotIds']), [q for q in dd['TurnTex'] if q]))

    # ---------------------------------------------------------------- 5. hero: the component + the capture camera
    hero = unreal.load_asset(HERO)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(hero)
    byname = {str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))): h for h in handles}
    def add(name, cls):
        if name in byname: log.append('hero already has ' + name); return byname[name]
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=cls, blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add %s: %s' % (name, fail))
        sds.rename_subobject(h, unreal.Text(name)); log.append('hero: added ' + name); return h
    add('VesnaTrade', bp.generated_class())
    hc = add('VTCapture', unreal.SceneCaptureComponent2D)
    c = SDL.get_object(sds.k2_find_subobject_data_from_handle(hc))
    c.set_editor_property('component_tags', [unreal.Name('VTCapture')])
    c.set_editor_property('texture_target', rt)
    c.set_editor_property('capture_every_frame', False); c.set_editor_property('capture_on_movement', False)
    c.set_editor_property('primitive_render_mode', unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
    c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_SCENE_COLOR_HDR)
    c.set_editor_property('fov_angle', 30.0)
    c.set_editor_property('relative_location', unreal.Vector(330, 0, 20)); c.set_editor_property('relative_rotation', unreal.Rotator(0, -4, 180))
    BEL.compile_blueprint(hero); EAL.save_asset(HERO)
    finish('Next: README step 2 (paste BPC_VesnaTrade_graph.txt into BPC_VesnaTrade, Compile, Save).')

if DRY_RUN:
    finish('DRY RUN only. Decision: if nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else
           'STOP: something above is MISSING (BPC_ObsidianSet v2 / #222 must be in first). Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()