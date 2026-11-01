# The Muster (#359), step 1 (TGA). Editor script, safe to re-run. UE 5.3.
#   py "<repo>/handoffs/barracks-hud-359/build/setup_muster_ue.py"
# DRY_RUN = True (default): changes NOTHING, only checks every asset this needs and writes setup_muster.txt.
# DRY_RUN = False:
#   1. imports T_MU_Frame + T_MU_Atlas from assets/tga/Muster/textures into /Game/CastleDefender/UI/Barracks/Muster
#   2. optional T_MU_Portrait: one capture of the level actor whose label has "Barracks" + "NPC" (else the corner stays dark)
#   3. creates BPC_Muster (ActorComponent) + variables + defaults (muster_data.json) and adds it to the hero as "Muster"
# Nothing touches existing materials, textures, decals or the level (the capture actor is deleted again).
import os, json, unreal

DRY_RUN = True

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'barracks-hud-359', 'build')
TEX_DIR = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'tga', 'Muster', 'textures'))
DEST = '/Game/CastleDefender/UI/Barracks/Muster'
COMP_DIR, COMP = '/Game/CastleDefender/Gameplay/Castle', 'BPC_Muster'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
P = {'npc': '/Game/CastleDefender/Gameplay/Castle/BP_NPC_Barracks', 'bhud': '/Game/CastleDefender/Gameplay/Castle/BP_BarracksHUD',
     'upg': '/Game/CastleDefender/Gameplay/Castle/BPC_CastleUpgrades', 'flares': '/Game/CastleDefender/Gameplay/Flares/BPC_Flares',
     'medics': '/Game/CastleDefender/Gameplay/Medics/BPC_Medics', 'yard': '/Game/CastleDefender/Gameplay/Castle/BP_CannonOrder'}
NEEDS = [P['npc'], P['bhud'], P['upg'], P['flares'], P['medics'], P['yard'], '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD',
         '/Game/CastleDefender/Gameplay/Castle/BP_ArmoryHUD', '/Game/CastleDefender/UI/Fonts/Font_Cinzel', '/Game/CastleDefender/UI/Barracks/MPC_Barracks',
         '/Game/CastleDefender/UI/SkillTree/MPC_SkillTree', '/Game/CastleDefender/UI/Trade/SFX_TradeSwipe', '/Game/CastleDefender/UI/Trade/SFX_TradeBuy',
         '/Game/CastleDefender/UI/Trade/SFX_TradeFail', HERO]
# the add-on events the Muster calls must exist (manifest_<BP>.json merged first, README step 2)
EVENTS = {P['upg']: ['HudBuyWalls', 'HudBuyTowers'], P['flares']: ['HudBuy'], P['medics']: ['HudBuy'], P['yard']: ['HudOrder'], P['bhud']: ['Enqueue']}
VARS_NEEDED = {P['upg']: ['Walls', 'Towers'], P['flares']: ['Owned', 'Price'], P['medics']: ['Count', 'MaxMedics', 'Price'], P['yard']: ['Price'], P['bhud']: ['RQ', 'RQStart', 'RQDur']}
TEXTURES = ['T_MU_Frame', 'T_MU_Atlas']
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
D = json.load(open(os.path.join(HERE, 'muster_data.json')))
def var_names(bp, wanted):
    """UE 5.3: Blueprint.new_variables is not readable from Python (#380). Compile, then probe the class default object."""
    BEL.compile_blueprint(bp); have = set()
    gc = bp.generated_class(); cdo = unreal.get_default_object(gc) if gc else None
    for n in wanted:
        try:
            cdo.get_editor_property(n); have.add(n)
        except Exception:
            pass
    return have
log = ['DRY_RUN = %s' % DRY_RUN]

missing = [p for p in NEEDS if not EAL.does_asset_exist(p)]
for p in NEEDS: log.append('%-8s %s' % ('ok' if p not in missing else 'MISSING', p))
for n in TEXTURES:
    f = os.path.join(TEX_DIR, n + '.png'); log.append('%-8s %s' % ('ok' if os.path.exists(f) else 'MISSING', f))
def bp_names(path):
    bp = unreal.load_asset(path)
    vars_ = var_names(bp, VARS_NEEDED.get(path, []))
    return vars_

for path, vs in VARS_NEEDED.items():
    if path in missing: continue
    have = bp_names(path)
    for v in vs:
        ok = v in have or path == P['bhud']          # BP_BarracksHUD's RQ vars are checked by the paste (#188)
        log.append('%-8s %s.%s' % ('ok' if ok else 'MISSING', path.split('/')[-1], v))
        if not ok: missing.append('%s.%s' % (path.split('/')[-1], v))
log.append('add-on events to merge first (README step 2): %s' % {k.split('/')[-1]: v for k, v in EVENTS.items() if k != P['bhud']})
npcs = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if 'barracks' in a.get_actor_label().lower() and 'npc' in a.get_actor_label().lower()]
log.append('barracks NPC actors in the level (portrait): %s' % [a.get_actor_label() for a in npcs][:5])
log.append('existing BPC_Muster: %s' % EAL.does_asset_exist(COMP_DIR + '/' + COMP))

def finish(msg):
    out = 'The Muster setup (#359)\n' + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'setup_muster.txt'), 'w').write(out); unreal.log(out)

def apply():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    tasks = []
    for n in TEXTURES:
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(TEX_DIR, n + '.png'))
        t.set_editor_property('destination_path', DEST); t.set_editor_property('destination_name', n)
        t.set_editor_property('replace_existing', True); t.set_editor_property('automated', True); t.set_editor_property('save', False)
        tasks.append(t)
    at.import_asset_tasks(tasks)
    tex = {}
    for n in TEXTURES:
        tx = unreal.load_asset('%s/%s' % (DEST, n)); tx.modify()
        tx.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tx.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tx.set_editor_property('never_stream', True); tx.set_editor_property('srgb', True)
        tx.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); tx.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
        tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        EAL.save_asset('%s/%s' % (DEST, n)); tex[n] = tx; log.append('texture %s' % n)
    portrait = None
    pp = DEST + '/T_MU_Portrait'
    if EAL.does_asset_exist(pp):
        portrait = unreal.load_asset(pp)
    elif npcs:
        try:
            v = npcs[0]; o, ext = v.get_actor_bounds(True)
            head = unreal.Vector(o.x, o.y, o.z + ext.z * 0.62)
            cam_loc = head + v.get_actor_forward_vector() * 120.0 + unreal.Vector(0, 0, 6)
            rot = unreal.MathLibrary.find_look_at_rotation(cam_loc, head)
            prt = at.create_asset('RT_MUPortrait', DEST, unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
            prt.set_editor_property('size_x', 690); prt.set_editor_property('size_y', 304)
            prt.set_editor_property('render_target_format', unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
            cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, rot)
            cc = cap.get_editor_property('capture_component2d')
            cc.set_editor_property('texture_target', prt); cc.set_editor_property('fov_angle', 40.0)
            cc.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
            cc.capture_scene()
            portrait = unreal.RenderingLibrary.render_target_create_static_texture2d_editor_only(prt, 'T_MU_Portrait')
            unreal.EditorLevelLibrary.destroy_actor(cap)
            if portrait: EAL.save_loaded_asset(portrait); log.append('portrait captured from ' + v.get_actor_label())
        except Exception as e:
            log.append('portrait skipped: %s' % e)
    path = COMP_DIR + '/' + COMP
    if EAL.does_asset_exist(path):
        bp = unreal.load_asset(path); log.append('reusing ' + path)
    else:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
        bp = at.create_asset(COMP, COMP_DIR, unreal.Blueprint, f); log.append('created ' + path)
    I, Dd, Bo, Str = (BEL.get_basic_type_by_name(n) for n in ('int', 'real', 'bool', 'string'))
    # UE 5.8: 'real' already comes back as real/double ('double'/'float' silently give int), and EdGraphPinType
    # fields are not exposed to Python, so set_editor_property('pin_sub_category') throws (Master, 2026-11-01)
    assert 'PinSubCategory="double"' in Dd.export_text(), 'real is not double: ' + Dd.export_text()
    LCT = BEL.get_struct_type(unreal.LinearColor.static_struct())
    OBJ, ARR = BEL.get_object_reference_type, BEL.get_array_type
    gen = lambda p: unreal.load_asset(p).generated_class()
    VARS = {n: {'int': I, 'double': Dd, 'bool': Bo}[t] for n, (t, _) in D['vars'].items()}
    VARS.update({'NPC': OBJ(gen(P['npc'])), 'Yard': OBJ(gen(P['yard'])), 'Upg': OBJ(gen(P['upg'])), 'Flares': OBJ(gen(P['flares'])), 'Medics': OBJ(gen(P['medics'])),
                 'FrameTex': OBJ(unreal.Texture2D), 'AtlasTex': OBJ(unreal.Texture2D), 'PortraitTex': OBJ(unreal.Texture2D),
                 'TabStart': ARR(I), 'TabCount': ARR(I), 'IPrice': ARR(I), 'IOreA': ARR(I), 'IOreAN': ARR(I), 'IOreB': ARR(I), 'IOreBN': ARR(I), 'IState': ARR(I),
                 'INote': ARR(Str), 'ISub': ARR(Str), 'IVerb': ARR(Str), 'OreNames': ARR(Str),
                 'NameUV': ARR(LCT), 'TitleUV': ARR(LCT), 'TagUV': ARR(LCT), 'D1UV': ARR(LCT), 'D2UV': ARR(LCT), 'GlyphUV': ARR(LCT), 'KindUV': ARR(LCT)})
    have = var_names(bp, list(VARS))
    for n, t in VARS.items():
        if n not in have:
            if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add ' + n)
            log.append('  + %s.%s' % (COMP, n))
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    for n, (t, v) in D['vars'].items(): cdo.set_editor_property(n, v)
    dd = D['data']
    for n in ('TabStart', 'TabCount', 'IPrice', 'IOreA', 'IOreAN', 'IOreB', 'IOreBN', 'IState', 'INote', 'ISub', 'IVerb', 'OreNames'): cdo.set_editor_property(n, dd[n])
    for n in ('NameUV', 'TitleUV', 'TagUV', 'D1UV', 'D2UV', 'GlyphUV', 'KindUV'): cdo.set_editor_property(n, [unreal.LinearColor(*q) for q in dd[n]])
    cdo.set_editor_property('FrameTex', tex['T_MU_Frame']); cdo.set_editor_property('AtlasTex', tex['T_MU_Atlas']); cdo.set_editor_property('PortraitTex', portrait)
    EAL.save_asset(path)
    hero = unreal.load_asset(HERO)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(hero)
    names = [str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) for h in handles]
    if 'Muster' in names:
        log.append('hero already has Muster')
    else:
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=bp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add component: %s' % fail)
        sds.rename_subobject(h, unreal.Text('Muster')); log.append('hero: added Muster')
    BEL.compile_blueprint(hero); EAL.save_asset(HERO)
    finish('Next: README step 4 (paste BPC_Muster_graph.txt into BPC_Muster, Compile, Save).')

if DRY_RUN:
    finish('DRY RUN only. Decision: if nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else
           'STOP: something above is MISSING. Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()
