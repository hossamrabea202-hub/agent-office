# #488 read-only: write T_vdbhdju_2K B / N / ORM as PNG for the Blender renders of build_merlon_kit.py. Touches no asset.
#   py export_scan_488_ue.py <folder>
import sys, unreal
OUT = sys.argv[1].rstrip('/\\') + '/'
B = '/Game/CastleDefender/AssetPacks/Fab/Megascans/Surfaces/Stone_Wall_vdbhdju/Medium/T_vdbhdju_2K_'
for s in 'B', 'N', 'ORM':
    e = unreal.AssetExportTask(); e.object = unreal.load_asset(B + s); e.filename = OUT + 'scan_%s.png' % s
    e.automated = True; e.replace_identical = True; e.prompt = False; e.exporter = unreal.TextureExporterPNG()
    print(s, unreal.Exporter.run_asset_export_task(e))
