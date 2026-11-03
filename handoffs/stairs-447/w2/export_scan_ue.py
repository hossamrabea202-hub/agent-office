# #301 W2 (i5): export the wall scan albedo Weathered2 uses, so the stair BakedColor bake matches the keep + walls.
import unreal
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/stairs-447/w2/'
for p, f in [('/Game/CastleDefender/AssetPacks/Fab/Megascans/Surfaces/Stone_Wall_vdbhdju/Medium/T_vdbhdju_2K_B', 'scan_B.png')]:
    t = unreal.load_asset(p)
    e = unreal.AssetExportTask(); e.object = t; e.filename = OUT + f; e.automated = True; e.replace_identical = True; e.prompt = False
    e.exporter = unreal.TextureExporterPNG()
    print('export', p, unreal.Exporter.run_asset_export_task(e), t.blueprint_get_size_x(), t.srgb)
