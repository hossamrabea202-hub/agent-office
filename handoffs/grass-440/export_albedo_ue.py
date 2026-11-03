# #440 (i5): read-only PNG export of the grass scan albedos (for tint calibration). Aborts in PIE.
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/grass-440/tex/'
MEL = unreal.MaterialEditingLibrary
for mi in ('/Game/CastleDefender/AssetPacks/Fab/Megascans/Plants/Wild_Grass_vczndjqja/Raw/MI_vczndjqja',
           '/Game/CastleDefender/AssetPacks/Fab/Megascans/Plants/Wild_Grass_vlkhcbxia/Raw/MI_vlkhcbxia'):
    m = unreal.load_asset(mi)
    for n in ('BaseColorTexture', 'Mask'):
        t = MEL.get_material_instance_texture_parameter_value(m, n)
        e = unreal.AssetExportTask(); e.object = t; e.filename = OUT + t.get_name() + '.png'; e.automated = True; e.prompt = False; e.replace_identical = True
        e.exporter = unreal.TextureExporterPNG()
        print('export', t.get_name(), t.blueprint_get_size_x(), unreal.Exporter.run_asset_export_task(e))
