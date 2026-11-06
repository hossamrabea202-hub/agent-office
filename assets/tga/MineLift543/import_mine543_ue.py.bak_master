# #543 mine lift + historic find (TGA PC, 2026-11-06). UE 5.3 Python, safe to re-run. Original procedural work (source/).
#   py "<repo>/assets/tga/MineLift543/import_mine543_ue.py"                 DRY RUN (default): checks files, the kit, the level; writes nothing
#   py ".../import_mine543_ue.py" --apply        imports meshes / textures into Environment/Mine/Lift + /Find, builds 6 materials,
#                                                 4 component-only Blueprints in Gameplay/Mine543. No level change.
#   py ".../import_mine543_ue.py" --place [--dry-run]   puts it in ThirdPersonMap (every actor tagged Mine543, logged to place_mine543.txt):
#        top:    the winding room 20 m under Mine_01 (SM_MineShaft_Top + cribbing + collar + bulkhead + frame + 3 lanterns,
#                BP_MineLift 'MineLift_Top', a BlockingVolume over the shaft hole); BP_MineGateDoor 'MineGate_Up' where
#                MineDoor_Up stands (MineDoor_Up is hidden + its Target cleared, so its E does nothing)
#        bottom: the dungeon's Tunnel_DeadEnd mesh -> SM_MineShaft_Bottom (same actor, same 4 m grid slot), its door frame +
#                MineDoor_Down hidden, cribbing + 2 lanterns, BP_MineLift 'MineLift_Bottom' (no windlass); Partner links both
#        find:   one dungeon OreVein mesh -> SM_Mine_OreVein_Cracked, BP_MineFind 'MineFind_Ulfberht' 1 m in front of it
#   py ".../import_mine543_ue.py" --remove [--dry-run]  undoes --place (destroys Mine543 actors, restores the 4 swapped/hidden ones)
#   py ".../import_mine543_ue.py" --revert       --remove, then deletes Environment/Mine/Lift, /Find and Gameplay/Mine543
# Needs: TGA's #309 MineKit imported (MI_MineRock / Oak / Iron / Ore, SM_Mine_Lantern, SM_Mine_DoorFrame) and #341 placed
# (Mine297_* dungeon actors, MineDoor_Up / MineDoor_Down). The Blueprint LOGIC (door swing, ride, swap, reveal, card) is a
# separate paste: README "Blueprint logic". Until it is in, everything stands still and E does nothing at the new door.
import os, sys, math, unreal

A = sys.argv[1:]
APPLY, PLACE, REMOVE, REVERT = '--apply' in A, '--place' in A, '--remove' in A, '--revert' in A
DRY = '--dry-run' in A or not (APPLY or PLACE or REMOVE or REVERT)
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\assets\tga\MineLift543'
KIT = '/Game/CastleDefender/Environment/Mine'
LIFT, FIND, GP = KIT + '/Lift', KIT + '/Find', '/Game/CastleDefender/Gameplay/Mine543'
TAG = 'Mine543'
EAL, MEL, BEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); LIB = unreal.SubobjectDataBlueprintFunctionLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
log = ['#543 mine lift + find (%s)' % ('DRY RUN, nothing written' if DRY else ' '.join(A))]
say = log.append

LIFT_MESHES = ['SM_MineGate_Door', 'SM_MineGate_Bulkhead', 'SM_MineShaft_Top', 'SM_MineShaft_Bottom', 'SM_MineShaft_Cribbing_Top',
               'SM_MineShaft_Cribbing_Bottom', 'SM_MineShaft_Collar', 'SM_MineWindlass_Drum', 'SM_MineBucket', 'SM_MineRope_1m']
FIND_MESHES = ['SM_Mine_OreVein_Cracked', 'SM_Ulfberht', 'SM_Reveal_LightShaft', 'SM_Reveal_Motes', 'SM_InfoCard']
TEX = [('T_Ulfberht_BC', FIND, True, 'TC_DEFAULT'), ('T_Ulfberht_ORM', FIND, False, 'TC_MASKS'), ('T_Ulfberht_N', FIND, False, 'TC_NORMALMAP'),
       ('T_RevealNoise', FIND, False, 'TC_MASKS'), ('T_InfoCard_Ulfberht', FIND, True, 'TC_DEFAULT'),
       ('T_MineRope_BC', LIFT, True, 'TC_DEFAULT'), ('T_MineRope_ORM', LIFT, False, 'TC_MASKS'), ('T_MineRope_N', LIFT, False, 'TC_NORMALMAP')]
SHELLS = ('SM_MineShaft_Top', 'SM_MineShaft_Bottom')
NO_COLLISION = ('SM_MineRope_1m', 'SM_Reveal_LightShaft', 'SM_Reveal_Motes', 'SM_InfoCard', 'SM_Ulfberht', 'SM_MineBucket')
# Blender metres -> UE cm, Y mirrored like the FBX (same as place_mine297)
def ue(x, y, z): return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)
# lift numbers (Blender metres, see source/build_mine543.py + README): drum axis 1.15 m over the room floor, 0.22 m off the
# shaft centre; bucket hangs rim-flush (pivot z -1.04); the swap happens at bucket z -9.5 (top) <-> +10.2 (bottom), where the
# 1.3 m cribbing frames line up exactly
DRUM, BUCKET_Z, EYE = (0.22, 0.0, 1.15), -1.04, 1.83

def fbx(path):
    t = unreal.AssetImportTask(); t.filename = path; t.automated = True; t.save = True; t.replace_existing = True
    f = unreal.FbxImportUI(); f.import_mesh = True; f.import_as_skeletal = False; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    f.import_materials = False; f.import_textures = False
    d = f.static_mesh_import_data; d.combine_meshes = True; d.auto_generate_collision = False
    d.import_uniform_scale = 100.0                       # same FBX scale fix as the #309 kit (Master, #341)
    d.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE        # rock wet/soot/puddle, vein glow, mote phase
    d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    t.options = f; return t

# ------------------------------------------------------------------------------------------------ material helpers
def E(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e
def Pm(m, cls, name, x, y, default=None, tex=None, sampler=None):
    e = E(m, cls, x, y); e.set_editor_property('parameter_name', name)
    if default is not None: e.set_editor_property('default_value', default)
    if tex: e.set_editor_property('texture', unreal.load_asset(tex))
    if sampler: e.set_editor_property('sampler_type', sampler)
    return e
C = MEL.connect_material_expressions
def out(e, pin, prop): MEL.connect_material_property(e, pin, prop)
MP = unreal.MaterialProperty
def new_material(name, folder):
    path = folder + '/' + name
    if EAL.does_asset_exist(path): EAL.delete_asset(path)      # rebuilt on every --apply (they are only used by #543 assets)
    return AT.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew()), path
def tex_set(m, base, x, y, uv=None):
    s = {}
    for k, suf, smp, yy in (('bc', 'BC', None, 0), ('orm', 'ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, 300),
                            ('n', 'N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, 600)):
        s[k] = Pm(m, unreal.MaterialExpressionTextureSampleParameter2D, suf + 'Tex', x, y + yy, tex=base + '_' + suf, sampler=smp)
        if uv is not None: C(uv, '', s[k], 'UVs')
    return s
def pbr_out(m, s):
    out(s['bc'], 'RGB', MP.MP_BASE_COLOR); out(s['orm'], 'G', MP.MP_ROUGHNESS); out(s['orm'], 'B', MP.MP_METALLIC)
    out(s['orm'], 'R', MP.MP_AMBIENT_OCCLUSION); out(s['n'], 'RGB', MP.MP_NORMAL)
def finish(m, path): MEL.recompile_material(m); EAL.save_asset(path)

def build_materials():
    mats = {}
    # M_Ulfberht: baked set + a gentle float bob in WPO (Float 1 = floating at the find, 0 = still, e.g. in the hand / a rack)
    m, p = new_material('M_Ulfberht', FIND); s = tex_set(m, FIND + '/T_Ulfberht', -900, 0); pbr_out(m, s)
    t = E(m, unreal.MaterialExpressionTime, -1300, 900); hz = Pm(m, unreal.MaterialExpressionScalarParameter, 'BobHz', -1300, 1000, 0.45)
    a = E(m, unreal.MaterialExpressionMultiply, -1100, 950); C(t, '', a, 'A'); C(hz, '', a, 'B')
    a2 = E(m, unreal.MaterialExpressionMultiply, -950, 950, const_b=6.283185); C(a, '', a2, 'A')
    sn = E(m, unreal.MaterialExpressionSine, -800, 950); C(a2, '', sn, '')
    amp = Pm(m, unreal.MaterialExpressionScalarParameter, 'BobCm', -800, 1050, 2.5); fl = Pm(m, unreal.MaterialExpressionScalarParameter, 'Float', -800, 1150, 1.0)
    z = E(m, unreal.MaterialExpressionMultiply, -600, 980); C(sn, '', z, 'A'); C(amp, '', z, 'B')
    z2 = E(m, unreal.MaterialExpressionMultiply, -450, 1000); C(z, '', z2, 'A'); C(fl, '', z2, 'B')
    xy = E(m, unreal.MaterialExpressionConstant2Vector, -450, 900, r=0.0, g=0.0)
    ap = E(m, unreal.MaterialExpressionAppendVector, -300, 950); C(xy, '', ap, 'A'); C(z2, '', ap, 'B'); out(ap, '', MP.MP_WORLD_POSITION_OFFSET)
    finish(m, p); mats['M_Ulfberht'] = m
    # M_MineRope: V is locked to the rope's own length (world Z from its pivot), so a Z-scaled rope never stretches its lay
    m, p = new_material('M_MineRope', LIFT)
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1500, 0); u = E(m, unreal.MaterialExpressionComponentMask, -1300, 0, r=True, g=False, b=False, a=False); C(tc, '', u, '')
    wp = E(m, unreal.MaterialExpressionWorldPosition, -1500, 150); op = E(m, unreal.MaterialExpressionObjectPositionWS, -1500, 250)
    dz = E(m, unreal.MaterialExpressionSubtract, -1300, 200); C(wp, '', dz, 'A'); C(op, '', dz, 'B')
    zz = E(m, unreal.MaterialExpressionComponentMask, -1150, 200, r=False, g=False, b=True, a=False); C(dz, '', zz, '')
    v = E(m, unreal.MaterialExpressionDivide, -1000, 200, const_b=-36.0); C(zz, '', v, 'A')          # one tile = 36 cm (3 lays of 12 cm)
    uv = E(m, unreal.MaterialExpressionAppendVector, -850, 100); C(u, '', uv, 'A'); C(v, '', uv, 'B')
    pbr_out(m, tex_set(m, LIFT + '/T_MineRope', -650, 0, uv)); finish(m, p); mats['M_MineRope'] = m
    # M_RevealVein: the ore set (kit textures, 1 m tiles) + emissive cleft from vertex colour R^2, slowly breathing
    m, p = new_material('M_RevealVein', FIND)
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1300, 0); pbr_out(m, tex_set(m, KIT + '/T_MineOre', -1000, 0, tc))
    vc = E(m, unreal.MaterialExpressionVertexColor, -1300, 1000); sq = E(m, unreal.MaterialExpressionMultiply, -1100, 1000); C(vc, 'R', sq, 'A'); C(vc, 'R', sq, 'B')
    t = E(m, unreal.MaterialExpressionTime, -1300, 1150); tm = E(m, unreal.MaterialExpressionMultiply, -1150, 1150, const_b=1.7); C(t, '', tm, 'A')
    sn = E(m, unreal.MaterialExpressionSine, -1000, 1150); C(tm, '', sn, ''); br = E(m, unreal.MaterialExpressionMultiply, -850, 1150, const_b=0.2); C(sn, '', br, 'A')
    br2 = E(m, unreal.MaterialExpressionAdd, -700, 1150, const_b=0.8); C(br, '', br2, 'A')
    gc = Pm(m, unreal.MaterialExpressionVectorParameter, 'GlowColor', -1000, 1300, unreal.LinearColor(1.0, 0.72, 0.38, 1)); gs = Pm(m, unreal.MaterialExpressionScalarParameter, 'GlowStrength', -1000, 1400, 8.0)
    rv = Pm(m, unreal.MaterialExpressionScalarParameter, 'Reveal', -1000, 1500, 1.0)
    e1 = E(m, unreal.MaterialExpressionMultiply, -800, 1000); C(sq, '', e1, 'A'); C(br2, '', e1, 'B')
    e2 = E(m, unreal.MaterialExpressionMultiply, -650, 1050); C(e1, '', e2, 'A'); C(gc, '', e2, 'B')
    e3 = E(m, unreal.MaterialExpressionMultiply, -500, 1100); C(e2, '', e3, 'A'); C(gs, '', e3, 'B')
    e4 = E(m, unreal.MaterialExpressionMultiply, -350, 1150); C(e3, '', e4, 'A'); C(rv, '', e4, 'B'); out(e4, '', MP.MP_EMISSIVE_COLOR)
    finish(m, p); mats['M_RevealVein'] = m
    # M_RevealShaft: additive unlit beam. Fades at both ends and at grazing angles, noise pans upward, soft where it meets the floor
    m, p = new_material('M_RevealShaft', FIND); m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property('two_sided', True)
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1600, 0); vv = E(m, unreal.MaterialExpressionComponentMask, -1450, 0, r=False, g=True, b=False, a=False); C(tc, '', vv, '')
    hv = E(m, unreal.MaterialExpressionOneMinus, -1300, 0); C(vv, '', hv, '')                   # height up the beam 0..1 (FBX flips V)
    lo = E(m, unreal.MaterialExpressionMultiply, -1150, -50, const_b=6.0); C(hv, '', lo, 'A'); los = E(m, unreal.MaterialExpressionSaturate, -1000, -50); C(lo, '', los, '')
    hi = E(m, unreal.MaterialExpressionOneMinus, -1150, 50); C(hv, '', hi, ''); hip = E(m, unreal.MaterialExpressionPower, -1000, 50, const_exponent=1.6); C(hi, '', hip, 'Base')
    ends = E(m, unreal.MaterialExpressionMultiply, -850, 0); C(los, '', ends, 'A'); C(hip, '', ends, 'B')
    fr = E(m, unreal.MaterialExpressionFresnel, -1150, 200, exponent=2.0); edge = E(m, unreal.MaterialExpressionOneMinus, -1000, 200); C(fr, '', edge, '')
    sc_ = E(m, unreal.MaterialExpressionMultiply, -1450, 350); C(tc, '', sc_, 'A'); k2 = E(m, unreal.MaterialExpressionConstant2Vector, -1600, 450, r=3.0, g=0.7); C(k2, '', sc_, 'B')
    pan = E(m, unreal.MaterialExpressionPanner, -1300, 350, speed_x=0.0, speed_y=0.08); C(sc_, '', pan, 'Coordinate')
    nz = Pm(m, unreal.MaterialExpressionTextureSampleParameter2D, 'NoiseTex', -1100, 350, tex=FIND + '/T_RevealNoise', sampler=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS); C(pan, '', nz, 'UVs')
    nzm = E(m, unreal.MaterialExpressionMultiply, -900, 350, const_b=1.1); C(nz, 'R', nzm, 'A'); nza = E(m, unreal.MaterialExpressionAdd, -750, 350, const_b=0.35); C(nzm, '', nza, 'A')
    df = E(m, unreal.MaterialExpressionDepthFade, -900, 550, fade_distance_default=60.0)
    col = Pm(m, unreal.MaterialExpressionVectorParameter, 'Color', -700, -250, unreal.LinearColor(1.0, 0.8, 0.5, 1))
    st = Pm(m, unreal.MaterialExpressionScalarParameter, 'Strength', -700, -150, 2.0); rv = Pm(m, unreal.MaterialExpressionScalarParameter, 'Reveal', -700, -50, 1.0)
    a1 = E(m, unreal.MaterialExpressionMultiply, -650, 100); C(ends, '', a1, 'A'); C(edge, '', a1, 'B')
    a2 = E(m, unreal.MaterialExpressionMultiply, -500, 200); C(a1, '', a2, 'A'); C(nza, '', a2, 'B')
    a3 = E(m, unreal.MaterialExpressionMultiply, -350, 300); C(a2, '', a3, 'A'); C(df, '', a3, 'B')
    a4 = E(m, unreal.MaterialExpressionMultiply, -350, 0); C(col, '', a4, 'A'); C(st, '', a4, 'B')
    a5 = E(m, unreal.MaterialExpressionMultiply, -200, 100); C(a4, '', a5, 'A'); C(a3, '', a5, 'B')
    a6 = E(m, unreal.MaterialExpressionMultiply, -50, 100); C(a5, '', a6, 'A'); C(rv, '', a6, 'B'); out(a6, '', MP.MP_EMISSIVE_COLOR)
    finish(m, p); mats['M_RevealShaft'] = m
    # M_RevealMotes: additive round sparks (radial mask on each quad's UV), each twinkling on its own phase (vertex colour R)
    m, p = new_material('M_RevealMotes', FIND); m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property('two_sided', True)
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1400, 0); c5 = E(m, unreal.MaterialExpressionConstant2Vector, -1400, 100, r=0.5, g=0.5)
    ds = E(m, unreal.MaterialExpressionDistance, -1250, 50); C(tc, '', ds, 'A'); C(c5, '', ds, 'B')
    d2 = E(m, unreal.MaterialExpressionMultiply, -1100, 50, const_b=2.0); C(ds, '', d2, 'A'); om = E(m, unreal.MaterialExpressionOneMinus, -950, 50); C(d2, '', om, '')
    sa = E(m, unreal.MaterialExpressionSaturate, -800, 50); C(om, '', sa, ''); rad = E(m, unreal.MaterialExpressionPower, -650, 50, const_exponent=2.5); C(sa, '', rad, 'Base')
    vc = E(m, unreal.MaterialExpressionVertexColor, -1400, 300); ph = E(m, unreal.MaterialExpressionMultiply, -1250, 300, const_b=6.283185); C(vc, 'R', ph, 'A')
    t = E(m, unreal.MaterialExpressionTime, -1400, 450); tt = E(m, unreal.MaterialExpressionMultiply, -1250, 450, const_b=2.6); C(t, '', tt, 'A')
    sm = E(m, unreal.MaterialExpressionAdd, -1100, 380); C(ph, '', sm, 'A'); C(tt, '', sm, 'B'); sn = E(m, unreal.MaterialExpressionSine, -950, 380); C(sm, '', sn, '')
    tw = E(m, unreal.MaterialExpressionMultiply, -800, 380, const_b=0.4); C(sn, '', tw, 'A'); tw2 = E(m, unreal.MaterialExpressionAdd, -650, 380, const_b=0.6); C(tw, '', tw2, 'A')
    col = Pm(m, unreal.MaterialExpressionVectorParameter, 'Color', -650, -200, unreal.LinearColor(1.0, 0.85, 0.55, 1))
    st = Pm(m, unreal.MaterialExpressionScalarParameter, 'Strength', -650, -100, 20.0); rv = Pm(m, unreal.MaterialExpressionScalarParameter, 'Reveal', -650, 600, 1.0)
    b1 = E(m, unreal.MaterialExpressionMultiply, -450, 100); C(rad, '', b1, 'A'); C(tw2, '', b1, 'B')
    b2 = E(m, unreal.MaterialExpressionMultiply, -450, -150); C(col, '', b2, 'A'); C(st, '', b2, 'B')
    b3 = E(m, unreal.MaterialExpressionMultiply, -300, 0); C(b2, '', b3, 'A'); C(b1, '', b3, 'B')
    b4 = E(m, unreal.MaterialExpressionMultiply, -150, 100); C(b3, '', b4, 'A'); C(rv, '', b4, 'B'); out(b4, '', MP.MP_EMISSIVE_COLOR)
    finish(m, p); mats['M_RevealMotes'] = m
    # M_InfoCard: unlit translucent card, Reveal 0..1 fades it in (the BP drives it), Brightness for the cave's exposure
    m, p = new_material('M_InfoCard', FIND); m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    tx = Pm(m, unreal.MaterialExpressionTextureSampleParameter2D, 'CardTex', -700, 0, tex=FIND + '/T_InfoCard_Ulfberht')
    bt = Pm(m, unreal.MaterialExpressionScalarParameter, 'Brightness', -700, 300, 1.0); rv = Pm(m, unreal.MaterialExpressionScalarParameter, 'Reveal', -700, 400, 1.0)
    em = E(m, unreal.MaterialExpressionMultiply, -400, 100); C(tx, 'RGB', em, 'A'); C(bt, '', em, 'B'); out(em, '', MP.MP_EMISSIVE_COLOR); out(rv, '', MP.MP_OPACITY)
    finish(m, p); mats['M_InfoCard'] = m
    return mats

# ------------------------------------------------------------------------------------------------ Blueprints (components only)
def names(bp): return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}
def add_comp(bp, cls, name, parent=None, socket=None):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    ph = have.get(parent) if parent else None
    if ph is None:
        if parent: say('  WARNING %s: parent %s not found, %s goes on the root (re-parent it by hand)' % (bp.get_name(), parent, name))
        ph = SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=ph, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s.%s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); c = LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))
    if socket: c.set_editor_property('attach_socket_name', socket)
    say('  + %s.%s' % (bp.get_name(), name)); return c
def new_bp(name):
    path = GP + '/' + name
    if EAL.does_asset_exist(path): say('reusing ' + path); return unreal.load_asset(path), path
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    say('create ' + path); return AT.create_asset(name, GP, unreal.Blueprint, f), path
def mesh_comp(bp, name, mesh, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), parent=None, socket=None, coll='NoCollision'):
    c = add_comp(bp, unreal.StaticMeshComponent, name, parent, socket); c.set_editor_property('static_mesh', unreal.load_asset(mesh))
    c.set_editor_property('relative_location', unreal.Vector(*loc)); c.set_editor_property('relative_rotation', unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    c.set_editor_property('relative_scale3d', unreal.Vector(*scale)); c.set_collision_profile_name(coll); return c
def point_light(bp, name, loc, lm, col, radius, parent=None, socket=None):
    L = add_comp(bp, unreal.PointLightComponent, name, parent, socket); L.set_editor_property('relative_location', unreal.Vector(*loc))
    L.set_editor_property('intensity_units', unreal.LightUnits.LUMENS); L.set_editor_property('intensity', lm)
    L.set_editor_property('light_color', unreal.Color(r=col[0], g=col[1], b=col[2], a=255)); L.set_editor_property('attenuation_radius', radius)
    L.set_editor_property('source_radius', 2.0); return L
def build_blueprints():
    warm = (255, 158, 77)                                                    # KB warm lamp (1.0, 0.62, 0.3), like the dungeon lanterns
    # the door: origin = bottom centre of the opening, faces +X (the side the hero comes from); Door pivots on its hinge
    bp, p = new_bp('BP_MineGateDoor')
    mesh_comp(bp, 'Frame', KIT + '/SM_Mine_DoorFrame', coll='BlockAll')
    mesh_comp(bp, 'Door', LIFT + '/SM_MineGate_Door', loc=(0, 60, 0), coll='BlockAll')   # leaf runs -Y from the hinge at +60
    a = add_comp(bp, unreal.ArrowComponent, 'Exit'); a.set_editor_property('relative_location', unreal.Vector(150, 0, 40)); a.set_editor_property('arrow_size', 2.0)
    BEL.compile_blueprint(bp); EAL.save_asset(p)
    # the lift: origin = shaft centre on the floor it serves (top: room floor; bottom: landing floor)
    bp, p = new_bp('BP_MineLift')
    dx, dy, dz = DRUM
    mesh_comp(bp, 'Drum', LIFT + '/SM_MineWindlass_Drum', loc=(dx * 100, 0, dz * 100), coll='BlockAll')
    mesh_comp(bp, 'Bucket', LIFT + '/SM_MineBucket', loc=(0, 0, BUCKET_Z * 100))
    mesh_comp(bp, 'Rope', LIFT + '/SM_MineRope_1m', scale=(1, 1, 0.36), parent='Bucket', socket='Rope')
    mesh_comp(bp, 'Lamp', KIT + '/SM_Mine_Lantern', parent='Bucket', socket='Lamp')
    point_light(bp, 'LampLight', (0, 0, 20), 300.0, warm, 700.0, parent='Lamp')
    cam = add_comp(bp, unreal.CameraComponent, 'RideCam', 'Bucket')                       # looks down past the hero's shoulder
    cam.set_editor_property('relative_location', unreal.Vector(-75, 55, 340)); cam.set_editor_property('relative_rotation', unreal.Rotator(roll=0, pitch=-69.6, yaw=-35.2))
    cam.set_editor_property('field_of_view', 70.0); cam.set_editor_property('auto_activate', True)   # SetViewTarget(lift) uses it
    a = add_comp(bp, unreal.ArrowComponent, 'Exit'); a.set_editor_property('relative_location', unreal.Vector(-170, 0, 40)); a.set_editor_property('arrow_size', 2.0)
    BEL.compile_blueprint(bp); EAL.save_asset(p)
    # the find: the sword turns slowly (child actor with a RotatingMovement, no graph needed) and bobs (material WPO)
    bp, p = new_bp('BP_MineFindSword')
    mesh_comp(bp, 'Sword', FIND + '/SM_Ulfberht', rot=(0, 0, 0))
    rm = add_comp(bp, unreal.RotatingMovementComponent, 'Turn'); rm.set_editor_property('rotation_rate', unreal.Rotator(roll=0, pitch=0, yaw=25))
    BEL.compile_blueprint(bp); EAL.save_asset(p); sword_cls = unreal.load_class(None, p + '.BP_MineFindSword_C')
    bp, p = new_bp('BP_MineFind')                                            # origin on the floor under the sword, +X towards the player
    ca = add_comp(bp, unreal.ChildActorComponent, 'Sword'); ca.set_editor_property('child_actor_class', sword_cls); ca.set_editor_property('relative_location', unreal.Vector(0, 0, 142))
    mesh_comp(bp, 'Beam', FIND + '/SM_Reveal_LightShaft', loc=(0, 0, 2)); mesh_comp(bp, 'Motes', FIND + '/SM_Reveal_Motes')
    c = mesh_comp(bp, 'Card', FIND + '/SM_InfoCard', loc=(40, 120, 80), rot=(0, 0, -25), scale=(1, 0.62, 0.62)); c.set_editor_property('cast_shadow', False)
    point_light(bp, 'FindLight', (45, 0, 175), 600.0, (255, 204, 140), 650.0)
    a = add_comp(bp, unreal.SphereComponent, 'Reach'); a.set_editor_property('sphere_radius', 220.0); a.set_editor_property('relative_location', unreal.Vector(0, 0, 100))
    BEL.compile_blueprint(bp); EAL.save_asset(p)

# ------------------------------------------------------------------------------------------------ assets
def apply_assets():
    missing = [n for n in ('MI_MineRock', 'MI_MineOak', 'MI_MineIron', 'MI_MineOre', 'SM_Mine_Lantern', 'SM_Mine_DoorFrame', 'T_MineOre_BC') if not EAL.does_asset_exist(KIT + '/' + n)]
    if missing: raise SystemExit('import TGA\'s #309 MineKit first (missing %s)' % ', '.join(missing))
    tasks = []
    for n, dst, _, _ in TEX:
        t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'textures', n + '.png'); t.destination_path = dst; t.automated = True; t.save = True; t.replace_existing = True; tasks.append(t)
    AT.import_asset_tasks(tasks)
    for n, dst, srgb, comp in TEX:
        t = unreal.load_asset(dst + '/' + n); t.modify(); t.set_editor_property('srgb', srgb)
        t.set_editor_property('compression_settings', getattr(unreal.TextureCompressionSettings, comp))
        if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)      # already DirectX
        if n == 'T_InfoCard_Ulfberht':
            t.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI); t.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
        EAL.save_loaded_asset(t)
    tasks = []
    for names_, dst in ((LIFT_MESHES, LIFT), (FIND_MESHES, FIND)):
        for n in names_:
            t = fbx(os.path.join(HERE, 'fbx', n + '.fbx')); t.destination_path = dst; tasks.append(t)
    AT.import_asset_tasks(tasks)
    mats = build_materials()
    slot = {'M_MineRock': KIT + '/MI_MineRock', 'M_MineOak': KIT + '/MI_MineOak', 'M_MineIron': KIT + '/MI_MineIron', 'M_MineOre': KIT + '/MI_MineOre'}
    sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for names_, dst in ((LIFT_MESHES, LIFT), (FIND_MESHES, FIND)):
        for n in names_:
            sm = unreal.load_asset(dst + '/' + n)
            if not sm: say('WARNING %s did not import' % n); continue
            for i, s in enumerate(sm.get_editor_property('static_materials')):
                key = str(s.get_editor_property('material_slot_name'))
                mi = mats.get(key) or (unreal.load_asset(slot[key]) if key in slot else None)
                if mi: sm.set_material(i, mi)
                else: say('  slot %s on %s has no material' % (key, n))
            bs = sm.get_editor_property('body_setup')
            if n in SHELLS:
                if bs: bs.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            elif n in NO_COLLISION:
                if sub: sub.remove_collisions(sm)
            elif sub:
                sub.remove_collisions(sm); sub.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.NDOP26)
            else: say('  StaticMeshEditorSubsystem is None (headless): %s keeps no simple collision, add one by hand if the hero should bump it' % n)
            if n == 'SM_MineBucket':                                          # where the rope hooks on, the hero stands, the lamp hangs
                for s_ in list(sm.get_editor_property('sockets') or []): sm.remove_socket(s_)
                for nm, loc in (('Rope', (0, 0, 183)), ('Stand', (30, 0, 97)), ('Lamp', (0, -42, 150))):   # Stand = floor 7 + capsule half-height 90
                    so = unreal.StaticMeshSocket(sm); so.set_editor_property('socket_name', nm); so.set_editor_property('relative_location', unreal.Vector(*loc)); sm.add_socket(so)
            EAL.save_loaded_asset(sm)
    build_blueprints()
    say('assets: %d meshes, %d textures, %d materials, 4 Blueprints in %s' % (len(LIFT_MESHES) + len(FIND_MESHES), len(TEX), len(mats), GP))

# ------------------------------------------------------------------------------------------------ level
def tagged(tag=TAG): return [a for a in EAS.get_all_level_actors() if tag in [str(t) for t in a.tags]]
def mark(a, label):
    a.set_actor_label(label); a.tags = list(a.tags) + [unreal.Name(TAG)]; say('  %-26s %s' % (label, a.get_actor_location())); return a
def by_label(label):
    f = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == label]; return f[0] if f else None
def mesh_of(a):
    c = a.get_component_by_class(unreal.StaticMeshComponent) if a else None
    return (c, c.get_editor_property('static_mesh')) if c else (None, None)
STATE = os.path.join(HERE, 'place_mine543_state.txt')                       # what --place changed on actors it did not make
def remove_placed():
    found = tagged(); say('remove %d Mine543 actors' % len(found))
    if not DRY:
        for a in found: EAS.destroy_actor(a)
    if os.path.exists(STATE):
        for line in open(STATE).read().splitlines():
            kind, label, val = line.split('|')
            a = by_label(label)
            if not a: say('  restore: %s not found' % label); continue
            say('  restore %s %s -> %s' % (label, kind, val))
            if DRY: continue
            if kind == 'mesh': mesh_of(a)[0].set_editor_property('static_mesh', unreal.load_asset(val))
            elif kind == 'hidden': a.set_actor_hidden_in_game(val == 'True'); a.set_is_temporarily_hidden_in_editor(False); a.set_actor_enable_collision(True)
            elif kind == 'target': a.set_editor_property('Target', by_label(val) if val else None)
        if not DRY: os.remove(STATE); LES.save_all_dirty_levels()
def place():
    for n in ('BP_MineLift', 'BP_MineGateDoor', 'BP_MineFind'):
        if not EAL.does_asset_exist(GP + '/' + n) and not DRY: raise SystemExit('run --apply first (%s missing)' % n)
    mine, up, dn = by_label('Mine_01'), by_label('MineDoor_Up'), by_label('MineDoor_Down')
    if not (mine and up and dn): raise SystemExit('need Mine_01, MineDoor_Up and MineDoor_Down (#341 place_mine297) in the level')
    old = tagged()
    if old: say('re-run: removing the last --place first'); remove_placed()
    dungeon = tagged('Mine297')
    dead = [a for a in dungeon if 'SM_Mine_Tunnel_DeadEnd' in str(mesh_of(a)[1].get_name() if mesh_of(a)[1] else '')]
    frames = [a for a in dungeon if mesh_of(a)[1] and mesh_of(a)[1].get_name() == 'SM_Mine_DoorFrame']
    veins = sorted([a for a in dungeon if mesh_of(a)[1] and mesh_of(a)[1].get_name() == 'SM_Mine_OreVein'], key=lambda a: a.get_actor_location().x, reverse=True)
    if not dead or not veins: raise SystemExit('dungeon pieces not found (Mine297 DeadEnd / OreVein): run #341 place_mine297 first')
    dead, vein = dead[0], veins[0]
    state, world = [], unreal.EditorLevelLibrary.get_editor_world()
    m = mine.get_actor_location(); T0 = unreal.Vector(m.x, m.y, m.z - 2000.0)          # the winding room, 20 m under the hut
    say('winding room origin %s (20 m under Mine_01)' % T0)
    for dxy in ((-350, -350), (950, -350), (-350, 350), (950, 350)):               # the room must stay under the ground everywhere
        p = T0 + unreal.Vector(dxy[0], dxy[1], 0)
        hit = unreal.SystemLibrary.line_trace_single(world, p + unreal.Vector(0, 0, 6000), p + unreal.Vector(0, 0, 450), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        say('  ground over room corner %s: %s' % (dxy, ('hit at z %.0f (room roof %.0f)' % (t[4].z, T0.z + 420)) if t and t[0] else 'NO GROUND ABOVE ROOF: check by eye'))
    def at(base, x, y, z, yaw=0.0): return base + unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)
    def spawn(asset, loc, yaw, label, cls=False):
        if DRY: say('  %-26s %s yaw %.0f' % (label, loc, yaw)); return None
        a = EAS.spawn_actor_from_class(unreal.load_class(None, asset), loc, unreal.Rotator(roll=0, pitch=0, yaw=yaw)) if cls else \
            EAS.spawn_actor_from_object(unreal.load_asset(asset), loc, unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        return mark(a, label)
    def lantern(loc, label):
        lan = spawn(KIT + '/SM_Mine_Lantern', loc, 0, label)
        if DRY: return
        smc = lan.static_mesh_component; p = smc.get_socket_location('Light') if smc.does_socket_exist('Light') else loc + unreal.Vector(0, 0, 20)
        L = mark(EAS.spawn_actor_from_class(unreal.PointLight, p, unreal.Rotator(0, 0, 0)), label + 'Light'); lc = L.point_light_component
        lc.set_editor_property('intensity_units', unreal.LightUnits.LUMENS); lc.set_editor_property('intensity', 400.0)
        lc.set_editor_property('light_color', unreal.Color(r=255, g=158, b=77, a=255)); lc.set_editor_property('attenuation_radius', 900.0); lc.set_editor_property('source_radius', 2.0)
        L.attach_to_actor(lan, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    say('top (winding room):')
    S = at(T0, 3.9, 0, 0)                                                     # shaft centre on the room floor
    spawn(LIFT + '/SM_MineShaft_Top', T0, 0, 'Mine543_ShaftTop'); spawn(LIFT + '/SM_MineShaft_Cribbing_Top', S, 0, 'Mine543_CribTop')
    spawn(LIFT + '/SM_MineShaft_Collar', S, 0, 'Mine543_Collar'); spawn(LIFT + '/SM_MineGate_Bulkhead', at(T0, 1.2, 0, 0), 180, 'Mine543_Bulkhead')
    spawn(KIT + '/SM_Mine_DoorFrame', at(T0, 1.2, 0, 0), 0, 'Mine543_RoomFrame')
    spawn(LIFT + '/SM_MineGate_Door', at(T0, 1.2, -0.62, 0), 85, 'Mine543_RoomDoor')        # stands open into the passage: he came through it
    lantern(at(T0, 2.1, -1.5, 2.2), 'Mine543_RoomLantern_0'); lantern(at(T0, 5.5, 1.4, 2.2), 'Mine543_RoomLantern_1'); lantern(at(T0, 2.9, 1.0, -3.0), 'Mine543_ShaftLantern_T')
    top = spawn(GP + '/BP_MineLift.BP_MineLift_C', S, 0, 'MineLift_Top', cls=True)
    g = spawn('/Engine/BasicShapes/Cube', S + unreal.Vector(0, 0, 110), 0, 'Mine543_ShaftGuard')   # nobody walks into the hole
    if g:                                                                     # (an invisible 2.3 x 2.3 x 2.2 m block over it)
        g.set_actor_scale3d(unreal.Vector(2.3, 2.3, 2.2)); g.set_actor_hidden_in_game(True); g.static_mesh_component.set_collision_profile_name('BlockAllDynamic')
    say('door (replaces the teleport at MineDoor_Up):')
    uxf = up.get_actor_transform(); gate = spawn(GP + '/BP_MineGateDoor.BP_MineGateDoor_C', up.get_actor_location(), up.get_actor_rotation().yaw, 'MineGate_Up', cls=True)
    state += ['hidden|MineDoor_Up|%s' % up.is_hidden_ed(), 'target|MineDoor_Up|MineDoor_Down', 'target|MineDoor_Down|MineDoor_Up']
    say('bottom (landing, replaces %s):' % dead.get_actor_label())
    dl, dyaw = dead.get_actor_location(), dead.get_actor_rotation().yaw
    def atb(x, y, z):                                                         # in the dead end module's frame
        v = unreal.Vector(x * 100.0, -y * 100.0, z * 100.0); r = math.radians(dyaw)
        return dl + unreal.Vector(v.x * math.cos(r) - v.y * math.sin(r), v.x * math.sin(r) + v.y * math.cos(r), v.z)
    state.append('mesh|%s|%s' % (dead.get_actor_label(), mesh_of(dead)[1].get_path_name()))
    near = [f for f in frames if (f.get_actor_location() - dl).length() < 600]
    for f in near: state.append('hidden|%s|%s' % (f.get_actor_label(), f.is_hidden_ed()))
    state.append('hidden|MineDoor_Down|%s' % dn.is_hidden_ed())
    SB = atb(3.25, 0, 0)
    spawn(LIFT + '/SM_MineShaft_Cribbing_Bottom', atb(3.25, 0, 14.5), dyaw, 'Mine543_CribBottom')
    lantern(atb(2.0, 1.2, 2.2), 'Mine543_LandingLantern'); lantern(atb(2.25, 1.0, 4.0), 'Mine543_ShaftLantern_B')
    bot = spawn(GP + '/BP_MineLift.BP_MineLift_C', SB, dyaw, 'MineLift_Bottom', cls=True)
    say('find (replaces the mesh of %s):' % vein.get_actor_label())
    state.append('mesh|%s|%s' % (vein.get_actor_label(), mesh_of(vein)[1].get_path_name()))
    vxf = vein.get_actor_transform(); fl = vxf.transform_location(unreal.Vector(100, 0, 0))   # the vein faces +X: 1 m out from its face
    find = spawn(GP + '/BP_MineFind.BP_MineFind_C', unreal.Vector(fl.x, fl.y, vein.get_actor_location().z), vein.get_actor_rotation().yaw, 'MineFind_Ulfberht', cls=True)
    if DRY: return
    mesh_of(dead)[0].set_editor_property('static_mesh', unreal.load_asset(LIFT + '/SM_MineShaft_Bottom'))
    mesh_of(vein)[0].set_editor_property('static_mesh', unreal.load_asset(FIND + '/SM_Mine_OreVein_Cracked'))
    for a in near + [up, dn]: a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True); a.set_actor_enable_collision(False)
    up.set_editor_property('Target', None); dn.set_editor_property('Target', None)          # the old teleport doors do nothing now
    bot_drum = [c for c in bot.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith('Drum')]
    for c in bot_drum: c.set_visibility(False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)   # the windlass is at the top
    links = [(top, 'Partner', bot), (bot, 'Partner', top), (top, 'Gate', gate), (bot, 'Gate', bot),   # bottom: Gate = itself (no None reads)
             (top, 'IsTop', True), (bot, 'IsTop', False), (top, 'RopeTop', 115.0), (bot, 'RopeTop', 1450.0)]
    for a, prop, v in links:
        try: a.set_editor_property(prop, v)                                   # these exist once the variable lines are pasted
        except Exception: say('  could not set %s.%s (paste VARIABLES_BP_MineLift_BPVar.txt first, then re-run --place)' % (a.get_actor_label(), prop))
    open(STATE, 'w').write('\n'.join(state)); LES.save_all_dirty_levels()
    say('Partner / Lift links are set if the logic paste is in; otherwise set them by hand (README).')

if REVERT or REMOVE: remove_placed()
if REVERT and not DRY:
    for f in (LIFT, FIND, GP):
        if EAL.does_directory_exist(f): EAL.delete_directory(f); say('deleted ' + f)
if APPLY and not DRY: apply_assets()
if PLACE: place()
if DRY and not (PLACE or REMOVE or REVERT):
    have = [n for n in LIFT_MESHES + FIND_MESHES if os.path.exists(os.path.join(HERE, 'fbx', n + '.fbx'))]
    tx = [n for n, _, _, _ in TEX if os.path.exists(os.path.join(HERE, 'textures', n + '.png'))]
    say('files: %d / %d FBX, %d / %d textures' % (len(have), len(LIFT_MESHES) + len(FIND_MESHES), len(tx), len(TEX)))
    kit = [n for n in ('MI_MineRock', 'MI_MineOak', 'MI_MineIron', 'MI_MineOre', 'SM_Mine_Lantern', 'SM_Mine_DoorFrame', 'T_MineOre_BC') if EAL.does_asset_exist(KIT + '/' + n)]
    say('kit: %d / 7 needed assets present' % len(kit))
    for l in ('Mine_01', 'MineDoor_Up', 'MineDoor_Down'): say('level: %s %s' % (l, 'found' if by_label(l) else 'MISSING'))
    say('Mine297 dungeon actors: %d' % len(tagged('Mine297')))
    ok = len(have) == len(LIFT_MESHES) + len(FIND_MESHES) and len(tx) == len(TEX) and len(kit) == 7
    say('DRY RUN %s. Next: --apply, then --place --dry-run, then --place' % ('OK' if ok else 'FAILED (see above)'))
outtxt = '\n'.join(log)
if PLACE and not DRY: open(os.path.join(HERE, 'place_mine543.txt'), 'w').write(outtxt)
unreal.log(outtxt); print(outtxt)
