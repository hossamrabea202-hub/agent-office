# Read-only (2026-11-02, i5, stair study): export the stair building blocks to FBX (for bevel measurement in Blender)
# and dump every parameter of the castle stone materials (tones, textures, tiling). Saves no asset.
import json, os, unreal
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, 'refs')
os.makedirs(OUT, exist_ok=True)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
MEL = unreal.MaterialEditingLibrary

meshes = {}
for name in ('SM_StairTread', 'SM_StoneModule', 'SM_WalkSlab', 'SM_Cube_Nanite', 'SM_Tower09_Stairs', 'SM_Bevel_041', 'SM_Bevel_022'):
    hits = [a for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'StaticMesh')) if str(a.asset_name) == name]
    for h in hits[:1]:
        sm = unreal.load_asset(str(h.package_name))
        t = unreal.AssetExportTask()
        t.object = sm; t.filename = os.path.join(OUT, name + '.fbx'); t.automated = True; t.prompt = False; t.replace_identical = True
        t.exporter = unreal.StaticMeshExporterFBX()
        ok = unreal.Exporter.run_asset_export_task(t)
        meshes[name] = {'path': str(h.package_name), 'exported': ok, 'lods': sm.get_num_lods(),
                        'nanite': bool(sm.get_editor_property('nanite_settings').enabled),
                        'lightmap_res': sm.get_editor_property('light_map_resolution')}

mats = {}
for name in ('MI_Castle_StepCap', 'MI_Castle_StoneWall_World', 'MI_Castle_Trim_World', 'MI_Castle_WalkFlag_World', 'MI_Castle_Paving_POM'):
    hits = [a for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')) if str(a.asset_name) == name]
    if not hits:
        continue
    mi = unreal.load_asset(str(hits[0].package_name))
    d = {'path': str(hits[0].package_name), 'parent': mi.get_editor_property('parent').get_path_name(), 'scalar': {}, 'vector': {}, 'texture': {}}
    for n in MEL.get_scalar_parameter_names(mi):
        d['scalar'][str(n)] = MEL.get_material_instance_scalar_parameter_value(mi, n)
    for n in MEL.get_vector_parameter_names(mi):
        c = MEL.get_material_instance_vector_parameter_value(mi, n)
        d['vector'][str(n)] = [round(c.r, 4), round(c.g, 4), round(c.b, 4), round(c.a, 4)]
    for n in MEL.get_texture_parameter_names(mi):
        tx = MEL.get_material_instance_texture_parameter_value(mi, n)
        d['texture'][str(n)] = tx.get_path_name() if tx else None
    mats[name] = d

json.dump({'meshes': meshes, 'materials': mats}, open(os.path.join(HERE, 'refs.json'), 'w'), indent=1)
print('stair refs: %d meshes exported, %d materials -> %s' % (sum(1 for m in meshes.values() if m['exported']), len(mats), HERE))
