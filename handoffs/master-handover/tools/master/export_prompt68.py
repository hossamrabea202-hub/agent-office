# #101: T3D export of the prompt-drawing Blueprints for the #68 prompt-fade paste -> handoffs/exports/laptop2/prompt68/
import unreal, os, traceback
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
OUT = r'C:\Users\hossa\Documents\agent-office\handoffs\exports\laptop2\prompt68'
WANT = ['BP_NoticeHUD', 'BP_BarracksHUD', 'BP_Cannon', 'BP_GateLever', 'BP_Gate', 'BP_MapPickup', 'BP_BagPickup', 'BP_SkillBookPickup', 'BP_SkillTreeHUD', 'BP_CannonHUD', 'BP_HeroHUD']
out = []
try:
    os.makedirs(OUT, exist_ok=True)
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    bps = reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint'))
    byname = {}
    for a in bps: byname.setdefault(str(a.asset_name), []).append(str(a.package_name))
    # anything with Lever / Pickup / Prompt / Cannon in the name, to catch the real names
    cands = sorted(n for n in byname if any(k in n for k in ('Lever', 'Pickup', 'Prompt', 'Cannon', 'Notice', 'Gate')))
    out.append('candidates: %s' % cands)
    for n in WANT:
        if n not in byname: out.append('%s: not found' % n); continue
        p = byname[n][0]
        bp = unreal.load_asset(p)
        f = os.path.join(OUT, n + '.t3d')
        t = unreal.AssetExportTask(); t.set_editor_property('object', bp); t.set_editor_property('filename', f)
        t.set_editor_property('exporter', unreal.ObjectExporterT3D()); t.set_editor_property('automated', True); t.set_editor_property('prompt', False); t.set_editor_property('replace_identical', True)
        ok = unreal.Exporter.run_asset_export_task(t)
        out.append('%s -> %s ok=%s size=%s' % (p, f, ok, os.path.getsize(f) if os.path.exists(f) else None))
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
