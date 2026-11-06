# Lab: export a Blueprint as whole-BP T3D (like the Master's exports). env Z_BP = asset path(s), Z_OUTDIR
import unreal, os
out = os.environ.get('Z_OUTDIR', 'C:/Users/hossam.rabea/ckw/ztools/bp_exports'); os.makedirs(out, exist_ok=True)
for p in os.environ['Z_BP'].split(','):
    bp = unreal.load_asset(p.strip()); fn = os.path.join(out, bp.get_name() + '.t3d.txt')
    t = unreal.AssetExportTask(); t.object = bp; t.filename = fn; t.automated = True; t.prompt = False; t.replace_identical = True
    try: t.exporter = unreal.ObjectExporterT3D()
    except Exception as e: print('no T3D exporter class', e)
    ok = unreal.Exporter.run_asset_export_task(t); print('BPEXPORT', ok, fn, os.path.getsize(fn) if os.path.exists(fn) else 'missing', [str(e) for e in t.errors])
print('BPEXPORT DONE')
