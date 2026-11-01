# The Muster v2 (#420), step 1 (TGA). Editor script, safe to re-run. UE 5.8.
#   py "<repo>/handoffs/muster-v2-420/build/setup_muster2_ue.py"
# DRY_RUN = True (default): changes NOTHING, checks every asset and class this needs and writes setup_muster2.txt.
# DRY_RUN = False:
#   1. backup: duplicates BPC_Muster (v1, as installed) to BPC_Muster_v1_backup (only once)
#   2. imports T_MU2_Frame + T_MU2_Atlas (assets/tga/Muster/textures_v2) into /Game/CastleDefender/UI/Barracks/Muster
#   3. unit busts: T_MU_Bust_Sword / Xbow / Cmdr / Medic, one SceneCapture each of the real unit Blueprint (spawned for the
#      capture far above the barracks, show-only, two temporary lights, all destroyed again). RECAPTURE = True redoes them.
#      PREVIEW_PNG = True also exports them to <project>/Saved/MusterBusts/*.png for the shot on #420.
#   4. adds the v2 variables to BPC_Muster and sets every default (muster_data.json): the frame / atlas, BustTex, the tables.
# Nothing touches existing materials, textures, decals or the level (spawned capture actors are destroyed; don't save the
# level if the editor asks). The v1 variables stay (unused by v2), so the backup graph still compiles.
import os, json, unreal

DRY_RUN = True
RECAPTURE = False
PREVIEW_PNG = True

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'muster-v2-420', 'build')
TEX_DIR = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'tga', 'Muster', 'textures_v2'))
DEST = '/Game/CastleDefender/UI/Barracks/Muster'
COMP_DIR, COMP = '/Game/CastleDefender/Gameplay/Castle', 'BPC_Muster'
BACKUP = COMP_DIR + '/BPC_Muster_v1_backup'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
UNITS = {'BP_SoldierSword': ('/Game/CastleDefender/Characters/Knight/BP_SoldierSword', 'T_MU_Bust_Sword'),
         'BP_SoldierXbow': ('/Game/CastleDefender/Characters/Knight/BP_SoldierXbow', 'T_MU_Bust_Xbow'),
         'BP_SoldierCommander': ('/Game/CastleDefender/Characters/Knight/BP_SoldierCommander', 'T_MU_Bust_Cmdr'),
         'BP_Medic': ('/Game/CastleDefender/Gameplay/Medics/BP_Medic', 'T_MU_Bust_Medic')}
NEEDS = [COMP_DIR + '/' + COMP, HERO, '/Game/CastleDefender/UI/Barracks/MPC_Barracks', '/Game/CastleDefender/Gameplay/Castle/BP_BarracksHUD',
         '/Game/CastleDefender/Characters/NPC/Barracks/BP_NPC_Barracks']
TEXTURES = ['T_MU2_Frame', 'T_MU2_Atlas']
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
D = json.load(open(os.path.join(HERE, 'muster_data.json')))
log = ['DRY_RUN = %s' % DRY_RUN]

def var_names(bp, wanted):
    """Blueprint.new_variables is not readable from Python: compile, then probe the class default object."""
    BEL.compile_blueprint(bp); have = set()
    gc = bp.generated_class(); cdo = unreal.get_default_object(gc) if gc else None
    for n in wanted:
        try:
            cdo.get_editor_property(n); have.add(n)
        except Exception:
            pass
    return have

missing = [p for p in NEEDS if not EAL.does_asset_exist(p)]
for p in NEEDS: log.append('%-8s %s' % ('ok' if p not in missing else 'MISSING', p))
for n in TEXTURES:
    f = os.path.join(TEX_DIR, n + '.png'); ok = os.path.exists(f); log.append('%-8s %s' % ('ok' if ok else 'MISSING', f))
    if not ok: missing.append(f)
for k, (p, t) in UNITS.items():
    log.append('%-8s %s (bust %s)' % ('ok' if EAL.does_asset_exist(p) else 'no unit', p, 'exists' if EAL.does_asset_exist(DEST + '/' + t) else 'to capture'))
log.append('backup %s: %s' % (BACKUP, 'exists' if EAL.does_asset_exist(BACKUP) else 'will be made'))
npcs = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if 'barracks' in a.get_actor_label().lower() and 'npc' in a.get_actor_label().lower()]
log.append('capture spot: above %s' % (npcs[0].get_actor_label() if npcs else 'the world origin'))

def finish(msg):
    out = 'The Muster v2 setup (#420)\n' + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'setup_muster2.txt'), 'w').write(out); unreal.log(out)

def find_bone(skel):
    for n in ('head', 'Head', 'head_01', 'Bip001-Head', 'Bip01-Head', 'neck_01', 'neck'):
        try:
            if skel.does_socket_exist(n): return skel.get_socket_location(n)
        except Exception:
            pass
    return None

def capture_bust(at, cls_path, tex_name, spot):
    cls = EAL.load_blueprint_class(cls_path)
    ELL = unreal.EditorLevelLibrary
    a = ELL.spawn_actor_from_class(cls, spot, unreal.Rotator(0, 0, 0))
    made = [a]
    try:
        skel = a.get_component_by_class(unreal.SkeletalMeshComponent)
        if skel:
            try:   # let the unit's own anim Blueprint settle into its idle pose (T-pose otherwise)
                skel.set_update_animation_in_editor(True)
                for _ in range(12): skel.tick_animation(0.05, False)
                skel.refresh_bone_transforms()
            except Exception as e:
                log.append('  (idle pose not applied: %s)' % e)
        o, ext = a.get_actor_bounds(False)
        head = find_bone(skel) if skel else None
        if head is None: head = unreal.Vector(o.x, o.y, o.z + ext.z * 0.78)
        fwd, right = a.get_actor_forward_vector(), a.get_actor_right_vector()
        aim = head + unreal.Vector(0, 0, -16)
        cam = aim + fwd * 150.0 + right * 38.0 + unreal.Vector(0, 0, 6)
        rot = unreal.MathLibrary.find_look_at_rotation(cam, aim)
        key = ELL.spawn_actor_from_class(unreal.PointLight, aim + fwd * 120 - right * 90 + unreal.Vector(0, 0, 60), unreal.Rotator(0, 0, 0)); made.append(key)
        rim = ELL.spawn_actor_from_class(unreal.PointLight, aim - fwd * 110 + right * 70 + unreal.Vector(0, 0, 40), unreal.Rotator(0, 0, 0)); made.append(rim)
        for l, inten, colr in ((key, 9000.0, unreal.LinearColor(1.0, 0.86, 0.68, 1)), (rim, 7000.0, unreal.LinearColor(0.62, 0.74, 1.0, 1))):
            lc = l.get_component_by_class(unreal.PointLightComponent)
            lc.set_intensity(inten); lc.set_light_color(colr); lc.set_attenuation_radius(600.0)
        rt = at.create_asset('RT_MUBust', DEST, unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew()) if not EAL.does_asset_exist(DEST + '/RT_MUBust') else unreal.load_asset(DEST + '/RT_MUBust')
        rt.set_editor_property('size_x', 532); rt.set_editor_property('size_y', 524)
        rt.set_editor_property('render_target_format', unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
        cap = ELL.spawn_actor_from_class(unreal.SceneCapture2D, cam, rot); made.append(cap)
        cc = cap.get_editor_property('capture_component2d')
        cc.set_editor_property('texture_target', rt); cc.set_editor_property('fov_angle', 28.0)
        cc.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        cc.set_editor_property('primitive_render_mode', unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
        cc.set_editor_property('show_only_actors', [a])
        try:
            cc.set_editor_property('show_flag_settings', [unreal.EngineShowFlagsSetting(show_flag_name=n, enabled=False) for n in ('Fog', 'Atmosphere', 'VolumetricFog')])
        except Exception:
            pass
        cc.capture_scene()
        if EAL.does_asset_exist(DEST + '/' + tex_name): EAL.delete_asset(DEST + '/' + tex_name)
        tex = unreal.RenderingLibrary.render_target_create_static_texture2d_editor_only(rt, tex_name)
        if tex:
            tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI); tex.set_editor_property('never_stream', True)
            EAL.save_loaded_asset(tex)
            if PREVIEW_PNG:
                d = os.path.join(unreal.Paths.project_saved_dir(), 'MusterBusts'); os.makedirs(d, exist_ok=True)
                unreal.RenderingLibrary.export_render_target(None, rt, d, tex_name + '.png')
        return tex
    finally:
        for x in made:
            try: ELL.destroy_actor(x)
            except Exception: pass

def apply():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = COMP_DIR + '/' + COMP
    if not EAL.does_asset_exist(BACKUP):
        EAL.duplicate_asset(path, BACKUP); EAL.save_asset(BACKUP); log.append('backup: ' + BACKUP)
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
    base = npcs[0].get_actor_location() if npcs else unreal.Vector(0, 0, 0)
    busts = {}
    for k, (p, tname) in UNITS.items():
        tp = DEST + '/' + tname
        if EAL.does_asset_exist(tp) and not RECAPTURE:
            busts[k] = unreal.load_asset(tp); log.append('bust %s: kept' % tname); continue
        if not EAL.does_asset_exist(p):
            log.append('bust %s: no unit Blueprint, the card shows its medallion' % tname); continue
        try:
            busts[k] = capture_bust(at, p, tname, base + unreal.Vector(0, 0, 20000 + 400 * len(busts)))
            log.append('bust %s: captured' % tname)
        except Exception as e:
            log.append('bust %s: skipped (%s), the card shows its medallion' % (tname, e))
    bp = unreal.load_asset(path)
    I, Dd, Bo, Str = (BEL.get_basic_type_by_name(n) for n in ('int', 'real', 'bool', 'string'))
    assert 'PinSubCategory="double"' in Dd.export_text(), 'real is not double: ' + Dd.export_text()
    LCT = BEL.get_struct_type(unreal.LinearColor.static_struct())
    OBJ, ARR = BEL.get_object_reference_type, BEL.get_array_type
    VARS = {n: {'int': I, 'double': Dd, 'bool': Bo}[t] for n, (t, _) in D['vars'].items()}
    VARS.update({'FrameTex': OBJ(unreal.Texture2D), 'AtlasTex': OBJ(unreal.Texture2D), 'BustTex': ARR(OBJ(unreal.Texture2D)),
                 'TabStart': ARR(I), 'TabCount': ARR(I), 'CardX0': ARR(I), 'IPrice': ARR(I), 'IOreA': ARR(I), 'IOreAN': ARR(I), 'IOreB': ARR(I), 'IOreBN': ARR(I),
                 'IState': ARR(I), 'INote': ARR(Str), 'ISub': ARR(Str), 'IVerb': ARR(Str), 'IBlock': ARR(Str), 'OreNames': ARR(Str),
                 'NameUV': ARR(LCT), 'TagUV': ARR(LCT), 'D1UV': ARR(LCT), 'D2UV': ARR(LCT), 'MedUV': ARR(LCT), 'KindUV': ARR(LCT)})
    have = var_names(bp, list(VARS))
    for n, t in VARS.items():
        if n not in have:
            if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add ' + n)
            log.append('  + %s.%s' % (COMP, n))
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    for n, (t, v) in D['vars'].items(): cdo.set_editor_property(n, v)
    dd = D['data']
    for n in ('TabStart', 'TabCount', 'CardX0', 'IPrice', 'IOreA', 'IOreAN', 'IOreB', 'IOreBN', 'IState', 'INote', 'ISub', 'IVerb', 'IBlock', 'OreNames'): cdo.set_editor_property(n, dd[n])
    for n in ('NameUV', 'TagUV', 'D1UV', 'D2UV', 'MedUV', 'KindUV'): cdo.set_editor_property(n, [unreal.LinearColor(*q) for q in dd[n]])
    cdo.set_editor_property('FrameTex', tex['T_MU2_Frame']); cdo.set_editor_property('AtlasTex', tex['T_MU2_Atlas'])
    cdo.set_editor_property('BustTex', [busts.get(u) for u in dd['Busts']])
    EAL.save_asset(path)
    finish('Next: README step 3 (replace the BPC_Muster EventGraph with BPC_Muster_graph.txt, Compile, Save), then Play.')

if DRY_RUN:
    finish('DRY RUN only. Decision: if nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else
           'STOP: something above is MISSING. Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()
