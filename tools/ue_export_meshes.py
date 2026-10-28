# Export static / skeletal meshes to FBX for an agent's request, in one go (any editor driver can run it, the owner too).
# Run in the Unreal editor (Output Log, Python), after editing the two lists below or passing them via EXPORTS:
#   py "<repo>/tools/ue_export_meshes.py"
# Each entry: (asset path, folder under the repo's handoffs/exports/). Writes <name>.fbx plus <name>_info.txt
# (bounds, triangle count, material slots, and the scale of every placed actor that uses the mesh in the open level).
import os
import unreal

REPO = r''   # your office-repo checkout; left empty = two folders up from this script
EXPORTS = [
    # ('/Game/CastleDefender/Props/SM_FieldCannon_HD', 'checkking/cannon58'),
]

try:
    ROOT = REPO or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    ROOT = REPO
if not ROOT:
    raise RuntimeError('set REPO at the top of ue_export_meshes.py to your office-repo checkout')
EAL = unreal.EditorAssetLibrary

def placed_scales(asset):
    out = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        for comp in a.get_components_by_class(unreal.StaticMeshComponent) + a.get_components_by_class(unreal.SkeletalMeshComponent):
            m = comp.get_editor_property('static_mesh') if isinstance(comp, unreal.StaticMeshComponent) else comp.get_editor_property('skeletal_mesh')
            if m == asset:
                s = comp.get_world_scale()
                out.append(f'{a.get_actor_label()} / {comp.get_name()}: scale ({s.x:.3f}, {s.y:.3f}, {s.z:.3f})')
    return out

for path, sub in EXPORTS:
    asset = EAL.load_asset(path)
    if asset is None:
        unreal.log_warning(f'export: {path} not found'); continue
    name = path.split('/')[-1].split('.')[0]
    dest = os.path.join(ROOT, 'handoffs', 'exports', *sub.split('/'))
    os.makedirs(dest, exist_ok=True)
    t = unreal.AssetExportTask()
    t.object = asset; t.filename = os.path.join(dest, name + '.fbx'); t.automated = True; t.replace_identical = True; t.prompt = False
    t.exporter = None
    ok = unreal.Exporter.run_asset_export_task(t)
    info = [f'asset: {path}', f'exported: {ok}']
    if isinstance(asset, unreal.StaticMesh):
        b = asset.get_bounding_box()
        info += [f'bounds min {b.min}, max {b.max}', f'triangles LOD0: {asset.get_num_triangles(0)}',
                 'materials: ' + ', '.join(str(m.material_slot_name) + '=' + (m.material_interface.get_path_name() if m.material_interface else '-') for m in asset.static_materials)]
    elif isinstance(asset, unreal.SkeletalMesh):
        info += ['materials: ' + ', '.join(str(m.material_slot_name) + '=' + (m.material_interface.get_path_name() if m.material_interface else '-') for m in asset.materials)]
    info += ['placed in the open level:'] + (placed_scales(asset) or ['  (none)'])
    with open(os.path.join(dest, name + '_info.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(info) + '\n')
    unreal.log(f'export: {path} -> {dest} ({"ok" if ok else "FAILED"})')
unreal.log('export: done. Commit + push handoffs/exports, then answer and close the request issue.')
