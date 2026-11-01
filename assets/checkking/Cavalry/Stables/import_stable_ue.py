# #401 Stables (checkking (Claude), 2026-11-01): import into UE 5.3. Original procedural work (../source/build_stable.py).
# Run in the editor:
#   py "<repo>/assets/checkking/Cavalry/Stables/import_stable_ue.py" --dry-run      (prints what it would do, writes nothing)
#   py "<repo>/assets/checkking/Cavalry/Stables/import_stable_ue.py"                (imports; re-running re-imports the same files)
# Creates ONLY new assets under /Game/CastleDefender/Environment/Stables (no live material, decal or level is touched):
#   SM_Stable (Nanite, 21 UCX collision boxes, vertex colour 'Wear' kept), 6 texture sets (BC sRGB + Sharpen4 mips,
#   ORM masks with Composite Texture = the normal map -> roughness (INDUSTRY_SECRETS 1.3), N BC5 DirectX),
#   M_StableTile (master) + MI_Stable<Oak|Daub|Shingle|Straw|Cobble|Iron>, assigned to the 6 slots in that order.
# M_StableTile = the lookdev recipe: tiling BC/ORM/N; vertex colour G = wet muck (colour -> lerp(base, lerp(base^2, muck,
# 0.5), G), roughness -> lerp(r, 0.35, 0.8 G)); B = sun bleach (colour -> lerp(c, grey(c) * 1.12, 0.45 B), roughness +0.05 B);
# R = baked AO, multiplied into the ORM AO. Scalars MuckStrength / SunStrength / Wetness (rain) per instance.
# Placement is NOT done here (owner's OK first): drag SM_Stable into the level. The open front faces +Y in UE (-Y in
# Blender), the back wall (at 7 m) goes against the curtain wall, pivot = front-left corner on the ground, 16 m along X.
import os, sys
import unreal

DRY = '--dry-run' in sys.argv
try: SRC = os.path.dirname(os.path.abspath(__file__))
except NameError: SRC = os.path.join(os.environ.get('AGENT_OFFICE', r'C:\Users\hossam.rabea\agent-office'), r'assets\checkking\Cavalry\Stables')
DST = '/Game/CastleDefender/Environment/Stables'
SETS = ['Oak', 'Daub', 'Shingle', 'Straw', 'Cobble', 'Iron']          # = material slot order in SM_Stable
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = lambda m: unreal.log('[Stables] ' + ('DRY-RUN ' if DRY else '') + m)

files = [os.path.join(SRC, 'SM_Stable.fbx')] + [os.path.join(SRC, 'textures', 'T_Stable%s_%s.png' % (s, k)) for s in SETS for k in ('BC', 'ORM', 'N')]
missing = [f for f in files if not os.path.isfile(f)]
if missing: raise RuntimeError('[Stables] missing files: ' + ', '.join(missing))
existing = [p for p in ['%s/%s' % (DST, n) for n in ['SM_Stable', 'M_StableTile'] + ['MI_Stable' + s for s in SETS]] if EAL.does_asset_exist(p)]
log('source ' + SRC + ' -> ' + DST + ' | %d files OK | already there (will be re-imported / kept): %s' % (len(files), existing or 'none'))
if DRY:
    log('would import 18 textures + SM_Stable.fbx (Nanite, UCX collision, vertex colours REPLACE), build M_StableTile + 6 MIs, assign slots ' + ', '.join(SETS))

def main():

    def task(path, opts=None):
        t = unreal.AssetImportTask(); t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
        if opts: t.options = opts
        return t

    # ---- textures
    tools.import_asset_tasks([task(f) for f in files[1:]])
    for s in SETS:
        bc, orm, n = ['%s/T_Stable%s_%s' % (DST, s, k) for k in ('BC', 'ORM', 'N')]
        t = unreal.load_asset(bc); t.modify(); t.set_editor_property('srgb', True)
        t.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_SHARPEN4); EAL.save_loaded_asset(t)
        t = unreal.load_asset(n); t.modify(); t.set_editor_property('srgb', False)
        t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        t.set_editor_property('flip_green_channel', False); EAL.save_loaded_asset(t)                 # already DirectX
        t = unreal.load_asset(orm); t.modify(); t.set_editor_property('srgb', False)
        t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
        try:                                                                                           # Composite Texture: kills distant sparkle
            t.set_editor_property('composite_texture', unreal.load_asset(n))
            t.set_editor_property('composite_texture_mode', unreal.CompositeTextureMode.CTM_NORMAL_ROUGHNESS_TO_GREEN)
            t.set_editor_property('composite_power', 1.0)
        except Exception as e: unreal.log_warning('[Stables] composite texture not set on %s: %s' % (orm, e))
        EAL.save_loaded_asset(t)

    # ---- mesh
    f = unreal.FbxImportUI()
    f.import_mesh = True; f.import_as_skeletal = False; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    f.import_materials = False; f.import_textures = False
    d = f.static_mesh_import_data
    d.combine_meshes = True; d.auto_generate_collision = False
    d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    d.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE
    try: d.set_editor_property('build_nanite', True)
    except Exception: pass
    tools.import_asset_tasks([task(files[0], f)])

    # ---- master material
    MASTER = DST + '/M_StableTile'
    if not EAL.does_asset_exist(MASTER):
        m = tools.create_asset('M_StableTile', DST, unreal.Material, unreal.MaterialFactoryNew())
        E = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
        C = MEL.connect_material_expressions
        def par(cls, name, x, y, default=None, tex=None, sampler=None):
            e = E(cls, x, y); e.set_editor_property('parameter_name', name)
            if default is not None: e.set_editor_property('default_value', default)
            if tex: e.set_editor_property('texture', unreal.load_asset(tex))
            if sampler: e.set_editor_property('sampler_type', sampler)
            return e
        bc = par(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1600, -300, tex=DST + '/T_StableOak_BC')
        orm = par(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1600, 150, tex=DST + '/T_StableOak_ORM', sampler=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        nrm = par(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1600, 550, tex=DST + '/T_StableOak_N', sampler=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        vc = E(unreal.MaterialExpressionVertexColor, -1600, -700)
        muckc = par(unreal.MaterialExpressionVectorParameter, 'MuckColor', -1600, -900, unreal.LinearColor(0.050, 0.034, 0.021, 1))
        mucks = par(unreal.MaterialExpressionScalarParameter, 'MuckStrength', -1300, -950, 1.0)
        suns = par(unreal.MaterialExpressionScalarParameter, 'SunStrength', -1300, -850, 1.0)
        wet = par(unreal.MaterialExpressionScalarParameter, 'Wetness', -1300, 400, 0.0)
        # muck: lerp(base, lerp(base^2, muck, 0.5), G * MuckStrength)
        sq = E(unreal.MaterialExpressionMultiply, -1300, -400); C(bc, 'RGB', sq, 'A'); C(bc, 'RGB', sq, 'B')
        mk = E(unreal.MaterialExpressionLinearInterpolate, -1150, -450); C(sq, '', mk, 'A'); C(muckc, '', mk, 'B'); mk.set_editor_property('const_alpha', 0.5)
        ga = E(unreal.MaterialExpressionMultiply, -1150, -700); C(vc, 'G', ga, 'A'); C(mucks, '', ga, 'B')
        gs = E(unreal.MaterialExpressionSaturate, -1020, -700); C(ga, '', gs, '')
        c1 = E(unreal.MaterialExpressionLinearInterpolate, -950, -350); C(bc, 'RGB', c1, 'A'); C(mk, '', c1, 'B'); C(gs, '', c1, 'Alpha')
        # sun bleach: lerp(c1, grey(c1) * 1.12, 0.45 * B * SunStrength)
        ds = E(unreal.MaterialExpressionDesaturation, -800, -500); C(c1, '', ds, '')
        dsm = E(unreal.MaterialExpressionMultiply, -680, -500); C(ds, '', dsm, 'A'); dsm.set_editor_property('const_b', 1.12)
        ba = E(unreal.MaterialExpressionMultiply, -800, -800); C(vc, 'B', ba, 'A'); C(suns, '', ba, 'B')
        bb = E(unreal.MaterialExpressionMultiply, -680, -800); C(ba, '', bb, 'A'); bb.set_editor_property('const_b', 0.45)
        c2 = E(unreal.MaterialExpressionLinearInterpolate, -550, -400); C(c1, '', c2, 'A'); C(dsm, '', c2, 'B'); C(bb, '', c2, 'Alpha')
        # rain (Wetness): darken like porous wood/plaster (Lagarde ~0.6), roughness toward 0.3
        w6 = E(unreal.MaterialExpressionMultiply, -420, -250); C(c2, '', w6, 'A'); w6.set_editor_property('const_b', 0.6)
        c3 = E(unreal.MaterialExpressionLinearInterpolate, -300, -350); C(c2, '', c3, 'A'); C(w6, '', c3, 'B'); C(wet, '', c3, 'Alpha')
        # roughness: lerp(r, 0.35, 0.8 G) + 0.05 B, then rain
        g8 = E(unreal.MaterialExpressionMultiply, -950, 100); C(gs, '', g8, 'A'); g8.set_editor_property('const_b', 0.8)
        r1 = E(unreal.MaterialExpressionLinearInterpolate, -800, 150); C(orm, 'G', r1, 'A'); r1.set_editor_property('const_b', 0.35); C(g8, '', r1, 'Alpha')
        b5 = E(unreal.MaterialExpressionMultiply, -800, 300); C(ba, '', b5, 'A'); b5.set_editor_property('const_b', 0.05)
        r2 = E(unreal.MaterialExpressionAdd, -650, 200); C(r1, '', r2, 'A'); C(b5, '', r2, 'B')
        r3 = E(unreal.MaterialExpressionLinearInterpolate, -500, 250); C(r2, '', r3, 'A'); r3.set_editor_property('const_b', 0.3); C(wet, '', r3, 'Alpha')
        ao = E(unreal.MaterialExpressionMultiply, -800, 450); C(orm, 'R', ao, 'A'); C(vc, 'R', ao, 'B')
        MEL.connect_material_property(c3, '', unreal.MaterialProperty.MP_BASE_COLOR)
        MEL.connect_material_property(r3, '', unreal.MaterialProperty.MP_ROUGHNESS)
        MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
        MEL.connect_material_property(ao, '', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
        MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
        MEL.recompile_material(m); EAL.save_asset(MASTER)
        log('built ' + MASTER)

    # ---- instances + slots
    sm = unreal.load_asset(DST + '/SM_Stable')
    for i, s in enumerate(SETS):
        path = '%s/MI_Stable%s' % (DST, s)
        mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else tools.create_asset('MI_Stable' + s, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
        for pn, k in (('BaseColorTex', 'BC'), ('ORMTex', 'ORM'), ('NormalTex', 'N')):
            MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/T_Stable%s_%s' % (DST, s, k)))
        if s == 'Iron': MEL.set_material_instance_scalar_parameter_value(mi, 'SunStrength', 0.0)   # iron doesn't bleach
        EAL.save_asset(path)
        sm.set_material(i, mi)
    EAL.save_loaded_asset(sm)
    log('done: %s/SM_Stable with %d slots. Drag it into the level (back wall to the curtain wall) and send a screenshot.' % (DST, len(SETS)))


if not DRY:
    main()
