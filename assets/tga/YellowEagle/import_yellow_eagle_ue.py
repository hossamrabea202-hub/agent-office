# Yellow Eagle set (#367, TGA): import the knight-fitted gauntlets, greaves and sabatons (L + R, LOD0-3) into UE 5.8.
# Run in the editor:  py "<repo>/assets/tga/YellowEagle/import_yellow_eagle_ue.py"
# DRY_RUN = True (default) only checks the files and prints what it would do. Set DRY_RUN = False to import.
# PREVIEW = True (after an import) spawns a temporary ShadowknightUE_SK actor with the 6 pieces at the knight-space
# placement in the open level, for a screenshot against the real knight mesh. Nothing is saved; delete the actors
# (folder "YE_FitPreview" in the Outliner) after the screenshot.
# Creates only NEW assets under /Game/CastleDefender/Characters/Hero/Armor/YellowEagle (its own master M_YellowEagle,
# one MI per piece shared by L/R). No existing asset, material or blueprint is touched.
# The meshes are in KNIGHT SPACE (ShadowknightUE_Skeleton ref pose, #368): attach them to a bone with
# offset = inverse(bone component transform), the same way as the Obsidian v2 set (handoffs/obsidian-set-v2).
import os
import unreal

DRY_RUN = True
PREVIEW = False
SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = '/Game/CastleDefender/Characters/Hero/Armor/YellowEagle'
KNIGHT = '/Game/ShadowKight/Mesh/ShadowknightUE_SK'
PIECES = ['Gauntlets', 'Greaves', 'Sabatons']
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = []

def fbx(piece, side, lod=0):
    return os.path.join(SRC, piece, 'fbx_knight', 'SM_Eagle%s_%s%s.fbx' % (piece, side, '' if lod == 0 else '_LOD%d' % lod))
def texf(piece, n):
    return os.path.join(SRC, piece, 'textures', 'T_Eagle%s_%s.png' % (piece, n))

missing = [p for pc in PIECES for p in [fbx(pc, s, l) for s in 'LR' for l in range(4)] + [texf(pc, n) for n in ('BC', 'ORM', 'N')] if not os.path.isfile(p)]
log.append('files: %d missing%s' % (len(missing), ''.join('\n  MISSING ' + m for m in missing)))
log.append('knight mesh %s: %s' % (KNIGHT, 'found' if EAL.does_asset_exist(KNIGHT) else 'NOT FOUND (preview will be skipped)'))

def task(path, dest, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = dest; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
def fbx_ui():
    f = unreal.FbxImportUI()
    f.import_mesh = True; f.import_as_skeletal = False; f.import_materials = False; f.import_textures = False
    d = f.static_mesh_import_data
    d.combine_meshes = True; d.generate_lightmap_u_vs = False; d.auto_generate_collision = False
    d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return f

def make_master():
    path = ROOT + '/M_YellowEagle'
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
    m = tools.create_asset('M_YellowEagle', ROOT, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -700, -200)
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -700, 100, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -700, 400, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -700, -420); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, -250)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    MEL.connect_material_property(mul, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(path)
    return m

def import_piece(pc, master):
    dst = '%s/%s' % (ROOT, pc); tn = 'T_Eagle' + pc
    tex = {'BC': (True, unreal.TextureCompressionSettings.TC_DEFAULT), 'ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
           'N': (False, unreal.TextureCompressionSettings.TC_NORMALMAP)}
    tools.import_asset_tasks([task(texf(pc, n), dst) for n in tex])
    for n, (srgb, comp) in tex.items():
        t = unreal.load_asset('%s/%s_%s' % (dst, tn, n))
        t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
        if n == 'N': t.set_editor_property('flip_green_channel', False)      # baked DirectX
        EAL.save_loaded_asset(t)
    mi_path = '%s/MI_Eagle%s' % (dst, pc)
    mi = unreal.load_asset(mi_path) if EAL.does_asset_exist(mi_path) else tools.create_asset('MI_Eagle' + pc, dst, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, master)
    for pn, n in (('BaseColor', 'BC'), ('ORM', 'ORM'), ('Normal', 'N')):
        MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/%s_%s' % (dst, tn, n)))
    EAL.save_asset(mi_path)
    tools.import_asset_tasks([task(fbx(pc, s), dst, fbx_ui()) for s in 'LR'])
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for s in 'LR':
        sm = unreal.load_asset('%s/SM_Eagle%s_%s' % (dst, pc, s))
        for lod in (1, 2, 3):
            r = sms.import_lod(sm, lod, fbx(pc, s, lod))
            if r != lod: log.append('  WARN %s LOD%d import returned %s' % (sm.get_name(), lod, r))
        for i in range(len(sm.static_materials)): sm.set_material(i, mi)
        EAL.save_loaded_asset(sm)
        log.append('  %s: %d LODs, MI %s' % (sm.get_name(), sms.get_lod_count(sm), mi.get_name()))

def preview():
    if not EAL.does_asset_exist(KNIGHT): log.append('preview skipped: knight mesh not found'); return
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    at = unreal.Vector(0, 0, 2000)                                    # in the air above the level origin
    k = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, at, unreal.Rotator(0, 0, 0))
    k.skeletal_mesh_component.set_skeletal_mesh_asset(unreal.load_asset(KNIGHT)); k.set_actor_label('YE_Knight'); k.set_folder_path('YE_FitPreview')
    for pc in PIECES:
        for s in 'LR':
            path = '%s/%s/SM_Eagle%s_%s' % (ROOT, pc, pc, s)
            if not EAL.does_asset_exist(path): log.append('  preview: %s not imported' % path); continue
            a = eas.spawn_actor_from_class(unreal.StaticMeshActor, at, unreal.Rotator(0, 0, 0))
            a.static_mesh_component.set_static_mesh(unreal.load_asset(path)); a.set_actor_label('YE_%s_%s' % (pc, s)); a.set_folder_path('YE_FitPreview')
            a.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            a.attach_to_actor(k, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)   # same spawn point: relative = identity = knight space
    log.append('preview: spawned YE_Knight + pieces at z=2000 cm (Outliner folder YE_FitPreview). Screenshot front / side / hands / feet, then delete the folder. Not saved.')

if DRY_RUN:
    log.append('DRY_RUN: would create %s/M_YellowEagle and, per piece in %s: 3 textures, MI_Eagle<Piece>, SM_Eagle<Piece>_L/_R with LOD1-3' % (ROOT, PIECES))
elif missing:
    log.append('STOP: files missing, nothing imported')
else:
    m = make_master()
    for pc in PIECES: import_piece(pc, m)
if PREVIEW and not DRY_RUN: preview()
out = '\n'.join(['import_yellow_eagle_ue (#367) DRY_RUN=%s PREVIEW=%s' % (DRY_RUN, PREVIEW)] + log)
open(os.path.join(SRC, 'import_yellow_eagle_report.txt'), 'w').write(out); unreal.log(out)
