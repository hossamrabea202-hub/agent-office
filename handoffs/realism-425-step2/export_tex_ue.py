# #425 step 2 (i5): export a few textures to TGA for pbr_check (read-only on the assets).  args: <asset path> ...
import os, sys, unreal
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/realism-425-step2/tex'
os.makedirs(OUT, exist_ok=True)
for p in sys.argv[1:]:
    t = unreal.load_asset(p)
    task = unreal.AssetExportTask()
    for k, v in (('object', t), ('filename', '%s/%s.tga' % (OUT, t.get_name())), ('automated', True), ('replace_identical', True), ('prompt', False)):
        task.set_editor_property(k, v)
    print(t.get_name(), t.blueprint_get_size_x(), 'srgb', t.get_editor_property('srgb'), 'export', unreal.Exporter.run_asset_export_task(task))
