# Read-only (i5, wood polish): export wood prop textures (BaseColor / ORM pairs) to PNG for pbr_check.py.
import json, os, unreal
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, 'tex'); os.makedirs(OUT, exist_ok=True)
PAIRS = [('T_Metal_Steel_D', 'T_GateIron_ARM'), ('T_GateOak_N', 'T_GateOak_ORM'), ('T_SiegeBarricade_Palisade_BaseColor', 'T_SiegeBarricade_Palisade_ORM'),
         ('T_SiegeBarricade_Watchtower_BaseColor', 'T_SiegeBarricade_Watchtower_ORM'),
         ('T_SiegeBarricade_Breach_BaseColor', 'T_SiegeBarricade_Breach_ORM'),
         ('T_ui2leaxlw_8K_B', 'T_ui2leaxlw_8K_ORM'), ('T_MineOak_BC', 'T_MineOak_ORM'),
         ('T_Camp_TorchPost_BaseColor', 'T_Camp_TorchPost_ORM'), ('pine_bark_diff_1k', 'pine_bark_arm_1k'),
         ('T_tmgpcg2fa_1k_B', 'T_tmgpcg2fa_1k_ORM'), ('T_tmgmfeefa_1K_B', 'T_tmgmfeefa_1K_ORM'),
         ('old_field_cannon_texture_4', 'old_field_cannon_texture_5'),
         ('Crossbow_1K_BaseColor', 'Crossbow_1K_AO-Crossbow_1K_Roughness-Crossbow_1K_Metallic'),
         ('T_GateOak_BC', 'T_GateOak_ORM'), ('T_tdfhffuq_2K_B', 'T_tdfhffuq_2K_ORM'),
         ('T_Barracks_Crate_BaseColor', 'T_Barracks_Crate_ORM'), ('T_Barracks_Barrel_BaseColor', 'T_Barracks_Barrel_ORM'),
         ('T_Barracks_WeaponRack_BaseColor', 'T_Barracks_WeaponRack_ORM'), ('fbx_texture_0', 'fbx_texture_1'),
         ('T_vcznah3g_8K_B', 'T_vcznah3g_8K_ORM'), ('T_GateLever_BC', 'T_GateLever_ORM'),
         ('T_SiegeGate_BaseColor', 'T_SiegeGate_ORM'), ('pine_sapling_medium_bark_diff_2k', 'pine_sapling_medium_bark_arm_2k')]
ar = unreal.AssetRegistryHelpers.get_asset_registry()
idx = {}
for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D')):
    idx.setdefault(str(a.asset_name), str(a.package_name))
res = []
for pair in PAIRS:
    files = []
    for n in pair:
        pk = idx.get(n)
        if not pk:
            files.append(None); continue
        t = unreal.AssetExportTask()
        t.object = unreal.load_asset(pk); t.filename = os.path.join(OUT, n + '.png'); t.automated = True; t.prompt = False
        t.replace_identical = True; t.exporter = unreal.TextureExporterPNG()
        ok = unreal.Exporter.run_asset_export_task(t)
        files.append(t.filename if ok else None)
    res.append({'pair': pair, 'files': files, 'pkg': [idx.get(n) for n in pair]})
json.dump(res, open(os.path.join(HERE, 'tex_export.json'), 'w'), indent=0)
print('exported', sum(1 for r in res for f in r['files'] if f), 'of', 2 * len(PAIRS))
