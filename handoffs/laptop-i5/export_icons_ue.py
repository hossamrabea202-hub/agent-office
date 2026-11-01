# #411: export the HUD key icons to PNG (read-only) so the castle icon can match their style.
import unreal
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-scroll-411/ref/'
for n in ('T_HUD_InventoryKey', 'T_HUD_SkillTreeKey', 'T_HUD_IconGate', 'T_HUD_GoldSack'):
    t = unreal.AssetExportTask(); t.object = unreal.load_asset('/Game/CastleDefender/UI/HUD/' + n)
    t.filename = OUT + n + '.png'; t.automated = True; t.prompt = False; t.replace_identical = True
    t.exporter = unreal.TextureExporterPNG()
    ok = unreal.Exporter.run_asset_export_task(t)
    unreal.log('i5 icon export %s %s %sx%s' % (n, ok, t.object.blueprint_get_size_x(), t.object.blueprint_get_size_y()))
