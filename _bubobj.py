import unreal
sm=unreal.load_asset('/Game/CastleDefender/Gameplay/Realm/_Backup/SM_RealmBubbleHi_20261031_2228')
t=unreal.AssetExportTask(); t.object=sm; t.filename=r'C:/Users/hossa/Documents/agent-office/_bub.obj'; t.automated=True; t.prompt=False; t.replace_identical=True
try: t.exporter=unreal.StaticMeshExporterOBJ()
except Exception as e: pass
ok=unreal.Exporter.run_asset_export_task(t)
open(r'C:/Users/hossa/Documents/agent-office/_bubobj_out.txt','w').write('obj %s'%ok)
