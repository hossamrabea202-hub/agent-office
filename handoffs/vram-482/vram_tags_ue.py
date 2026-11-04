# Video memory audit (i5, 2026-11-04, #482). READ-ONLY, asset registry tags only, loads nothing. Writes vram_tags.csv next to this file.
import csv, os, unreal
H = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/vram-482/', 'C:/Users/hossa/Documents/agent-office/handoffs/vram-482/') if os.path.isdir(h))
ar = unreal.AssetRegistryHelpers.get_asset_registry(); rows = []; keys = None
for ad in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D')):
    p = str(ad.package_name)
    if not p.startswith('/Game/'): continue
    g = lambda k: str(ad.get_tag_value(k) or '')
    rows.append([p, g('Dimensions'), g('Format'), g('CompressionSettings'), g('MaxTextureSize'), g('LODGroup'), g('NeverStream'), g('SRGB')])
csv.writer(open(H + 'vram_tags.csv', 'w', newline='')).writerows([['path', 'dims', 'format', 'comp', 'max', 'lodgroup', 'neverstream', 'srgb']] + rows)
print('VRAM rows', len(rows), rows[:2])
