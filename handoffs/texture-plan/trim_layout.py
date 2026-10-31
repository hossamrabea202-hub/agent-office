# #262 step 4 (TGA, 2026-10-31): the two shared trim-sheet layouts for #261, as data.
#   python trim_layout.py  -> trim_layout.json (strip pixel rows + UV V ranges) and the tables in TRIM_GUIDE.md
# 2048 x 2048 sheets. Strips tile along U (horizontal), so a plank / strap of any length maps onto one strip.
# Texel density: 512 px/m on the sheet (the props target), i.e. a 256 px strip = 0.5 m of real height.
# Gutter: 8 px between strips, filled by edge-extending the strip (dilation) -> clean down to mip 3 (256 px sheet = 1 px gutter).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); RES, PXM, GUT = 2048, 512, 8
SHEETS = {
    'WoodIron': [('OakPlank_Clean', 256, 'oak board face, 50 cm wide'), ('OakPlank_Worn', 256, 'same board, edge wear + dirt in grain'),
                 ('PinePlank', 256, 'pine board, lighter, resin knots'), ('Plank_Charred', 192, 'fire-blackened board, 37.5 cm'),
                 ('Beam_Side', 256, 'squared beam face, 50 cm'), ('Beam_EndGrain', 128, 'end-grain squares, 128 px each (25 cm)'),
                 ('IronStrap', 64, 'flat iron band, 12.5 cm'), ('IronStrap_Rivets', 64, 'band with rivet row'), ('NailRow', 32, 'nail heads on a 6 cm strip'),
                 ('Hinge', 96, 'strap hinge with knuckle, 19 cm'), ('Rope', 64, 'twisted rope, 12.5 cm (cylinder UV around)'),
                 ('LeatherStrap', 64, 'stitched leather strap, 12.5 cm'), ('Spare', 216, 'unique details: brackets, bolts, lock plates (no tiling)')],
    'StonePlaster': [('Ashlar_Block', 256, 'cut stone course, 50 cm'), ('Ashlar_Worn', 256, 'same course, chipped arrises + moss line'),
                     ('Moulding_Ogee', 128, 'carved ogee moulding profile, 25 cm'), ('Sill', 128, 'window sill / coping top, 25 cm'),
                     ('Arch_Voussoir', 192, 'wedge stones for arches, 37.5 cm'), ('Plaster_Limewash', 256, 'limewashed plaster, flat'),
                     ('Plaster_Edge', 128, 'plaster broken edge showing stone, 25 cm'), ('Brick_Course', 128, 'two brick courses, 25 cm'),
                     ('Mortar_Line', 32, 'recessed mortar joint, 6 cm'), ('Cobble_Edge', 128, 'kerb / step edge, 25 cm'),
                     ('Spare', 312, 'unique details: keystones, carvings (no tiling)')]}
out = {'res': RES, 'texel_density_px_per_m': PXM, 'gutter_px': GUT, 'sheets': {}}
md = []
for name, strips in SHEETS.items():
    y, rows = 0, []
    for sname, h, note in strips:
        rows.append(dict(strip=sname, y0=y, y1=y + h, height_px=h, height_cm=round(h / PXM * 100, 1), v0=round(1 - (y + h) / RES, 6), v1=round(1 - y / RES, 6), note=note))
        y += h + GUT
    assert y - GUT <= RES, (name, y)
    out['sheets'][name] = rows
    md += ['### T_Trim_%s (2048 x 2048, %d px used)' % (name, y - GUT), '', '| Strip | Rows (px, top = 0) | Height | Real size | UV V range | Content |', '|---|---|---|---|---|---|']
    md += ['| %s | %d-%d | %d px | %.1f cm | %.4f-%.4f | %s |' % (r['strip'], r['y0'], r['y1'], r['height_px'], r['height_cm'], r['v0'], r['v1'], r['note']) for r in rows] + ['']
json.dump(out, open(os.path.join(HERE, 'trim_layout.json'), 'w'), indent=1)
open(os.path.join(HERE, 'trim_tables.md'), 'w', encoding='utf-8').write('\n'.join(md))
print('trim_layout.json + trim_tables.md')
