import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
p = open(os.path.join(D, 'open_target.txt')).read().strip()
bp = unreal.load_asset(p)
f = os.path.join(D, 't3d', 'live_%s.t3d' % p.rsplit('/', 1)[1])
t = unreal.AssetExportTask(); t.set_editor_property('object', bp); t.set_editor_property('filename', f)
t.set_editor_property('exporter', unreal.ObjectExporterT3D()); t.set_editor_property('automated', True); t.set_editor_property('prompt', False); t.set_editor_property('replace_identical', True)
ok = unreal.Exporter.run_asset_export_task(t)
cdo = unreal.get_default_object(bp.generated_class())
vals = []
for n in ('StrikeRange', 'StrikeDamage', 'StrikeEvery', 'MaxStrikers', 'LeanSign', 'WobbleTime', 'WindupDeg', 'StrikeDeg', 'MaxHP'):
    try: vals.append('%s=%s' % (n, cdo.get_editor_property(n)))
    except Exception as e: pass
open(os.path.join(D, 'exp_one.txt'), 'w').write('%s %s\n%s' % (ok, f, ' '.join(vals)))
