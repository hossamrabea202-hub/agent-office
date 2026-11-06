# #539 Tentacle spore base: import, material, placement (adjustedfilm, 2026-11-06). Editor idle, not in Play, the main level open. New assets only; no live material touched.
#   py sporebase_ue.py --dry-run             report every tentacle's ground, size and spot; changes nothing
#   py sporebase_ue.py                       import, build the material, place one base per tentacle. Then save the level
#   py sporebase_ue.py --only Env_CorruptedTentacle_02,Env_CorruptedTentacle_05     try on some first
#   py sporebase_ue.py --revert              remove the placed bases (the assets stay). Then save the level
# Placement: a trace finds the ground under each tentacle; the arm's real thickness at that height (table below, rig metres) sizes the base, so the throat hugs the arm, mirrored actors included.
# Two shapes, A and B: each tentacle always gets the same one. Big slabs and the mound block the player and soldiers through an invisible low-poly collision mesh placed with each base; rubble, roots and pods do not. Bases do not affect navigation.
import bisect, os, sys, zlib, unreal
HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
DRY, REV = '--dry-run' in A, '--revert' in A; ONLY = A[A.index('--only') + 1].split(',') if '--only' in A else None
D_ = '/Game/CastleDefender/Environment/Tentacles/SporeBase'; SMS = [D_ + '/SM_TentacleSporeBase_A', D_ + '/SM_TentacleSporeBase_B']; MAT = D_ + '/M_TentacleSporeBase'
TD, TN = '/Game/CastleDefender/AssetPacks/StarterContent/Textures/T_Rock_Slate_D', '/Game/CastleDefender/AssetPacks/StarterContent/Textures/T_Rock_Slate_N'
PREFIX = 'TentacleSporeBase_'; NOMINAL_R = 30.0; SINK_CM = 60.0
# height above the rig's base, centre x, y, trunk radius: rig metres, measured from SK_CorruptedTentacle_01 (70th percentile of the ring, so spikes do not count). The top curl starts above 63.
TAB = [(0, -2.06, 2.12, 12.17), (3, -0.13, 0.1, 10.66), (6, 1.51, -0.79, 11.34), (9, -2.58, 2.24, 10.96), (12, -0.86, 0.39, 9.87), (15, -0.95, 2.29, 10.65), (18, -1.21, 0.57, 9.33), (21, -1.41, 0.69, 9.02), (24, -1.56, 0.77, 8.78), (27, -1.75, 0.89, 8.52), (30, -1.86, 0.91, 8.18), (33, -2.07, 1.01, 7.9), (36, -2.52, 1.08, 7.63), (39, -2.92, 1.08, 7.35), (42, -3.17, 1.07, 7.01), (45, -3.99, 1.02, 6.71), (48, -4.63, 0.98, 6.51), (51, -5.64, 0.9, 6.26), (54, -7.36, 0.76, 6.27), (57, -8.13, 0.39, 6.0), (60, -9.56, 0.52, 5.82), (63, -12.26, 0.41, 5.75)]
EAL, AT, MEL = unreal.EditorAssetLibrary, unreal.AssetToolsHelpers.get_asset_tools(), unreal.MaterialEditingLibrary
ES = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
def say(*a): print('SPORE539', ' '.join(str(x) for x in a))
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): raise SystemExit('SPORE539 stop Play first')
actors = ES.get_all_level_actors()
placed = [a for a in actors if a.get_actor_label().startswith(PREFIX)]
if REV:
    for a in placed:
        if not DRY: ES.destroy_actor(a)
    say('removed' if not DRY else 'would remove', len(placed), 'bases; save the level'); raise SystemExit(0)
def interp(h):
    hs = [r[0] for r in TAB]; i = min(max(bisect.bisect_right(hs, h), 1), len(TAB) - 1); a, b = TAB[i - 1], TAB[i]; t = min(max((h - a[0]) / float(b[0] - a[0]), 0.0), 1.0)
    return [a[k] + (b[k] - a[k]) * t for k in (1, 2, 3)]
def ground(actor):
    p = actor.get_actor_location(); hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(p.x, p.y, p.z + 150000.0), unreal.Vector(p.x, p.y, p.z - 20000.0), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    best = None
    for h in hits:
        t = h.to_tuple(); hit_actor = next((v for v in t if isinstance(v, unreal.Actor)), None); vecs = [v for v in t if isinstance(v, unreal.Vector)]
        if hit_actor is None or len(vecs) < 3: continue
        name = type(hit_actor).__name__; loc, nrm = vecs[0], vecs[2]
        if 'Landscape' in name: return loc, nrm, hit_actor.get_actor_label()
        if isinstance(hit_actor, unreal.StaticMeshActor) and best is None and not hit_actor.get_actor_label().startswith(PREFIX): best = (loc, nrm, hit_actor.get_actor_label())
    return best
tents = []
for a in actors:
    if not a.get_actor_label().startswith('Env_CorruptedTentacle') or not isinstance(a, unreal.SkeletalMeshActor): continue
    if ONLY and a.get_actor_label() not in ONLY: continue
    tents.append(a)
say('tentacles', len(tents), 'already placed', len(placed))
if not DRY:
    for SM in SMS:
        nm = SM.rsplit('/', 1)[1]
        if not EAL.does_asset_exist(SM):
            f = os.path.join(HERE, 'fbx', nm + '.fbx')
            if not os.path.exists(f): raise SystemExit('SPORE539 missing FBX (git pull?): ' + f)
            ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_animations', False); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
            d = ui.get_editor_property('static_mesh_import_data'); d.set_editor_property('import_uniform_scale', 0.01); d.set_editor_property('vertex_color_import_option', unreal.VertexColorImportOption.REPLACE); d.set_editor_property('auto_generate_collision', False); d.set_editor_property('generate_lightmap_u_vs', False); d.set_editor_property('combine_meshes', True); d.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
            try: d.set_editor_property('build_nanite', True)
            except Exception as e: say('note: no build_nanite option', e)
            t = unreal.AssetImportTask(); t.filename = f; t.destination_path = D_; t.destination_name = nm; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; AT.import_asset_tasks([t])
            if not EAL.does_asset_exist(SM): raise SystemExit('SPORE539 import failed; nothing placed')
        mesh = unreal.load_asset(SM); ns = mesh.get_editor_property('nanite_settings')
        if not ns.enabled: ns.enabled = True; mesh.set_editor_property('nanite_settings', ns); EAL.save_loaded_asset(mesh)
        b = mesh.get_bounds(); say(nm, 'extent cm', round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z), 'nanite', mesh.get_editor_property('nanite_settings').enabled)
    for SM in SMS:
        CM = SM + '_Col'; nm = CM.rsplit('/', 1)[1]
        if not EAL.does_asset_exist(CM):
            ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_animations', False); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
            d = ui.get_editor_property('static_mesh_import_data'); d.set_editor_property('import_uniform_scale', 0.01); d.set_editor_property('auto_generate_collision', False); d.set_editor_property('generate_lightmap_u_vs', False); d.set_editor_property('combine_meshes', True)
            t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', nm + '.fbx'); t.destination_path = D_; t.destination_name = nm; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; AT.import_asset_tasks([t])
            if not EAL.does_asset_exist(CM): raise SystemExit('SPORE539 collision import failed; nothing placed')
        cmesh = unreal.load_asset(CM); cmesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE); EAL.save_loaded_asset(cmesh)
    if not EAL.does_asset_exist(MAT):
        m = AT.create_asset('M_TentacleSporeBase', D_, unreal.Material, unreal.MaterialFactoryNew()); E = MEL.create_material_expression
        vc = E(m, unreal.MaterialExpressionVertexColor, -1000, -100); pw = E(m, unreal.MaterialExpressionPower, -800, -100); ce = E(m, unreal.MaterialExpressionConstant, -1000, 40); ce.set_editor_property('r', 2.2); MEL.connect_material_expressions(vc, '', pw, 'Base'); MEL.connect_material_expressions(ce, '', pw, 'Exponent')   # the vertex bytes are sRGB
        tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1400, 300); tile = E(m, unreal.MaterialExpressionScalarParameter, -1400, 420); tile.set_editor_property('parameter_name', 'DetailTile'); tile.set_editor_property('default_value', 1.0); mu = E(m, unreal.MaterialExpressionMultiply, -1200, 300); MEL.connect_material_expressions(tc, '', mu, 'A'); MEL.connect_material_expressions(tile, '', mu, 'B')
        td = E(m, unreal.MaterialExpressionTextureSample, -1000, 240); td.set_editor_property('texture', unreal.load_asset(TD)); MEL.connect_material_expressions(mu, '', td, 'UVs')
        ds = E(m, unreal.MaterialExpressionDesaturation, -800, 240); MEL.connect_material_expressions(td, 'RGB', ds, '')
        mean = E(m, unreal.MaterialExpressionScalarParameter, -800, 400); mean.set_editor_property('parameter_name', 'DetailMean'); mean.set_editor_property('default_value', 0.3); dv = E(m, unreal.MaterialExpressionDivide, -600, 240); MEL.connect_material_expressions(ds, '', dv, 'A'); MEL.connect_material_expressions(mean, '', dv, 'B')
        amt = E(m, unreal.MaterialExpressionScalarParameter, -600, 400); amt.set_editor_property('parameter_name', 'DetailAmount'); amt.set_editor_property('default_value', 0.6); one = E(m, unreal.MaterialExpressionConstant, -600, 130); one.set_editor_property('r', 1.0)
        lp = E(m, unreal.MaterialExpressionLinearInterpolate, -400, 200); MEL.connect_material_expressions(one, '', lp, 'A'); MEL.connect_material_expressions(dv, '', lp, 'B'); MEL.connect_material_expressions(amt, '', lp, 'Alpha')
        bc = E(m, unreal.MaterialExpressionMultiply, -250, -50); MEL.connect_material_expressions(pw, '', bc, 'A'); MEL.connect_material_expressions(lp, '', bc, 'B'); MEL.connect_material_property(bc, '', unreal.MaterialProperty.MP_BASE_COLOR)
        MEL.connect_material_property(vc, 'A', unreal.MaterialProperty.MP_ROUGHNESS)
        tn = E(m, unreal.MaterialExpressionTextureSample, -500, 500); tn.set_editor_property('texture', unreal.load_asset(TN)); tn.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL); MEL.connect_material_expressions(mu, '', tn, 'UVs'); MEL.connect_material_property(tn, 'RGB', unreal.MaterialProperty.MP_NORMAL)
        MEL.recompile_material(m); EAL.save_loaded_asset(m); say('material built')
    for SM in SMS: mesh = unreal.load_asset(SM); mesh.set_material(0, unreal.load_asset(MAT)); EAL.save_loaded_asset(mesh)
n_done = 0
for a in tents:
    lab = a.get_actor_label(); g = ground(a); s = abs(a.get_actor_scale3d().z); z = a.get_actor_location().z
    if not g: say('SKIP', lab, 'no ground under it'); continue
    loc, nrm, what = g; h = (loc.z - z) / s / 100.0
    if h < -1 or h > 63: say('SKIP', lab, 'ground is %.0f rig m up the arm, outside the table' % h); continue
    cx, cy, r = interp(h); c = a.get_actor_transform().transform_location(unreal.Vector(cx * 100.0, cy * 100.0, h * 100.0)) if hasattr(a.get_actor_transform(), 'transform_location') else unreal.MathLibrary.transform_location(a.get_actor_transform(), unreal.Vector(cx * 100.0, cy * 100.0, h * 100.0))
    size = r * s / NOMINAL_R; yaw = zlib.crc32(lab.encode()) % 360; SM = SMS[zlib.crc32(lab.encode()) // 7 % 2]
    say(lab, 'on', what, 'ground z', round(loc.z), 'height', round(h, 1), 'trunk radius m', round(r * s, 1), 'base scale', round(size, 2), 'width m', round(190 * size), 'shape', SM[-1], 'centre', round(c.x), round(c.y), "slope normal z", round(nrm.z, 2))
    if DRY: continue
    for old in [p for p in placed if p.get_actor_label() in (PREFIX + lab, PREFIX + 'Col_' + lab)]: ES.destroy_actor(old)
    b = ES.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(c.x, c.y, loc.z - SINK_CM), unreal.Rotator(0, 0, yaw)); b.set_actor_label(PREFIX + lab); b.set_folder_path('TentacleSporeBase'); b.set_actor_scale3d(unreal.Vector(size, size, size))
    sm = b.static_mesh_component; sm.set_static_mesh(unreal.load_asset(SM)); sm.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); sm.set_editor_property('can_ever_affect_navigation', False)
    k = ES.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(c.x, c.y, loc.z - SINK_CM), unreal.Rotator(0, 0, yaw)); k.set_actor_label(PREFIX + 'Col_' + lab); k.set_folder_path('TentacleSporeBase'); k.set_actor_scale3d(unreal.Vector(size, size, size))
    km = k.static_mesh_component; km.set_static_mesh(unreal.load_asset(SM + '_Col')); km.set_collision_profile_name('BlockAll'); km.set_editor_property('can_ever_affect_navigation', False); k.set_actor_hidden_in_game(True); km.set_editor_property('cast_shadow', False); n_done += 1
say('DONE', 'dry-run' if DRY else 'placed %d; save the level' % n_done)
