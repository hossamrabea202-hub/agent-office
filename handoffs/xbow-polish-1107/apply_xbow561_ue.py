# #561 crossbow polish: import the calibrated textures, make a NEW material, swap it onto the crossbow mesh.
# checkking (Claude), 2026-11-07. Editor Python (Master only):
#   py "<repo>/handoffs/xbow-polish-1107/apply_xbow561_ue.py" --src "<folder with the PNGs>"            (dry run: changes nothing)
#   py "<repo>/handoffs/xbow-polish-1107/apply_xbow561_ue.py" --src "<folder>" --import                (step 1: textures + material only)
#   py "<repo>/handoffs/xbow-polish-1107/apply_xbow561_ue.py" --src "<folder>" --apply                 (step 2, after the owner's OK: swap)
#   py "<repo>/handoffs/xbow-polish-1107/apply_xbow561_ue.py" --revert                                 (puts the old material back)
# Live assets are never edited: the old material is DUPLICATED, the copy gets the new textures. Same UVs, same normal map.
import unreal, sys, os, json

ARGS = sys.argv[1:]
def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS and ARGS.index(name) + 1 < len(ARGS) else default
DO_IMPORT = '--import' in ARGS or '--apply' in ARGS
DO_APPLY = '--apply' in ARGS
REVERT = '--revert' in ARGS
SRC = arg('--src', '')
HERE = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(HERE, 'apply_xbow561_backup.json')

SETS = {   # one entry per crossbow; Sovereign is added once its textures are exported (request #562)
    'noble': dict(
        mesh='/Game/CastleDefender/Equipment/crossbow/Noble_Crossbow_LowPoly',
        old_mat='/Game/CastleDefender/Equipment/crossbow/Crossbow___Baked_PBR_1K',
        old_bc='/Game/CastleDefender/Equipment/crossbow/Crossbow_1K_BaseColor',
        old_orm='/Game/CastleDefender/Equipment/crossbow/Crossbow_1K_AO-Crossbow_1K_Roughness-Crossbow_1K_Metallic',
        normal='/Game/CastleDefender/Equipment/crossbow/Crossbow_1K_Normal',
        folder='/Game/CastleDefender/Equipment/crossbow/Polish561',
        png_bc='T_Crossbow561_BaseColor.png', png_orm='T_Crossbow561_ORM.png',
        new_mat='M_Crossbow561'),
}
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
log = lambda *a: unreal.log('XBOW561 ' + ' '.join(str(x) for x in a))

def expressions(mat):
    if hasattr(MEL, 'get_material_expressions'):
        return list(MEL.get_material_expressions(mat))
    return list(mat.get_editor_property('editor_only_data').get_editor_property('expression_collection').get_editor_property('expressions'))

def import_tex(png, folder, name, srgb):
    path = folder + '/' + name
    if EAL.does_asset_exist(path):
        log('exists, kept:', path); return unreal.load_asset(path)
    t = unreal.AssetImportTask(); t.filename = png; t.destination_path = folder; t.destination_name = name
    t.automated = True; t.save = False; t.replace_existing = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset(path)
    tex.set_editor_property('srgb', srgb)
    if srgb:
        tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_SHARPEN4)   # INDUSTRY_SECRETS 1.3.6
    else:
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)   # 1.3.8
    log('imported', path); return tex

def referencers(path):
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    opts = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
    return [str(p) for p in reg.get_referencers(path.rsplit('.', 1)[0], opts) or []]

def build(s):
    folder = s['folder']; new_path = folder + '/' + s['new_mat']
    bc = import_tex(os.path.join(SRC, s['png_bc']), folder, s['png_bc'][:-4], True)
    orm = import_tex(os.path.join(SRC, s['png_orm']), folder, s['png_orm'][:-4], False)
    nrm = unreal.load_asset(s['normal'])
    if nrm:   # Composite Texture: mip normal variance -> roughness, stops distant sparkle (INDUSTRY_SECRETS 1.3.1)
        orm.set_editor_property('composite_texture', nrm)
        orm.set_editor_property('composite_texture_mode', unreal.CompositeTextureMode.CTM_NORMAL_ROUGHNESS_TO_GREEN)
        orm.set_editor_property('composite_power', 1.0)
    if EAL.does_asset_exist(new_path):
        mat = unreal.load_asset(new_path); log('material exists, re-pointing textures:', new_path)
    else:
        mat = EAL.duplicate_asset(s['old_mat'], new_path); log('duplicated', s['old_mat'], '->', new_path)
    old_bc, old_orm = unreal.load_asset(s['old_bc']), unreal.load_asset(s['old_orm'])
    hit = 0
    for e in expressions(mat):
        if not isinstance(e, unreal.MaterialExpressionTextureSample): continue
        t = e.get_editor_property('texture')
        if t == old_bc or t == bc:
            e.set_editor_property('texture', bc); e.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR); hit += 1
        elif t == old_orm or t == orm:
            e.set_editor_property('texture', orm); e.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS); hit += 1
    if hit < 2:
        log('ERROR: found', hit, 'of 2 texture samples to swap in', new_path, '- nothing swapped on the mesh. Send this log line to checkking.')
        return None
    MEL.recompile_material(mat)
    for a in (bc, orm, mat): EAL.save_loaded_asset(a, False)
    log('built', new_path, '(2 samples re-pointed, compiled, saved)'); return mat

def main():
    if REVERT:
        if not os.path.exists(BACKUP): log('no backup file, nothing to revert'); return
        for rec in json.load(open(BACKUP)):
            mesh = unreal.load_asset(rec['mesh']); mesh.set_material(rec['slot'], unreal.load_asset(rec['old']))
            EAL.save_loaded_asset(mesh, False); log('reverted', rec['mesh'], 'slot', rec['slot'], '->', rec['old'])
        return
    backup = json.load(open(BACKUP)) if os.path.exists(BACKUP) else []
    for key, s in SETS.items():
        mesh = unreal.load_asset(s['mesh']); old = unreal.load_asset(s['old_mat'])
        if not mesh or not old: log('ERROR missing', s['mesh'] if not mesh else s['old_mat']); continue
        slots = [i for i, m in enumerate(mesh.static_materials) if m.material_interface == old]
        log(key, 'mesh slots using', s['old_mat'], '=', slots)
        log(key, 'assets referencing the old material (component overrides would bypass the mesh slot):', referencers(s['old_mat']))
        for png in (s['png_bc'], s['png_orm']):
            p = os.path.join(SRC, png); log(key, 'source', p, 'OK' if os.path.exists(p) else 'MISSING')
        if not DO_IMPORT: continue
        mat = build(s)
        if not mat or not DO_APPLY: continue
        for i in slots:
            backup.append(dict(mesh=s['mesh'], slot=i, old=s['old_mat'])); mesh.set_material(i, mat)
            log('swapped', s['mesh'], 'slot', i, '->', mat.get_path_name())
        EAL.save_loaded_asset(mesh, False)
    if DO_APPLY:
        json.dump(backup, open(BACKUP, 'w'), indent=1); log('backup written', BACKUP)
    log('DONE', 'apply' if DO_APPLY else ('import' if DO_IMPORT else 'dry-run'))
main()
