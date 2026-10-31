# Texture budget (checkking, 2026-10-31, owner-approved): caps texture resolution by folder with "Maximum Texture Size",
# AAA third-person style (by camera distance). Source files are not touched: set MAX back to 0 to undo.
#   py "<repo>/handoffs/texture-budget/set_texture_budget_ue.py"            (DRY_RUN = True first: only reports)
# Writes texture_budget.txt next to itself: per rule, how many textures change and the estimated memory saved.
import os, unreal

DRY_RUN = True          # set False to apply
UNDO = False            # True: set every texture under the rules back to 0 (no cap)
RULES = [   # (content folder prefix, max size). First match wins: keep the specific folders above the general ones.
    ('/Game/CastleDefender/Characters/Hero/Armor', 2048),     # hero armour: always on screen, close to the camera
    ('/Game/CastleDefender/Weapons/CK', 1024),                # weapon kit (held / displayed)
    ('/Game/CastleDefender/Weapons', 1024),
    ('/Game/CastleDefender/Characters/Enemies', 2048),        # zombies, creatures
    ('/Game/CastleDefender/Characters/NPC', 1024),            # miner / medic gear, NPC props
    ('/Game/CastleDefender/Characters/Knight', 1024),         # soldiers' gear
    ('/Game/CastleDefender/Props', 1024),                     # barrels, carts, fences, crops, siege engines, signs
    ('/Game/CastleDefender/Environment/Barracks', 1024),
    ('/Game/CastleDefender/Environment/Decals', 1024),
    ('/Game/CastleDefender/Environment/Rocks', 2048),
]
SKIP = ('/Game/CastleDefender/UI',)   # UI textures stay as they are (no mips, pixel-exact)

try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\texture-budget'
EAL = unreal.EditorAssetLibrary
reg = unreal.AssetRegistryHelpers.get_asset_registry()
assets = reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D'))
stats = {r[0]: [0, 0.0] for r in RULES}
log = []
def mb(w, h, bpp):   # memory incl. mips
    return w * h * bpp / 8 * 1.333 / (1024 * 1024)
for a in assets:
    path = str(a.package_name)
    if path.startswith(SKIP): continue
    rule = next((r for r in RULES if path.startswith(r[0])), None)
    if not rule: continue
    tex = unreal.load_asset(path)
    w, h = tex.blueprint_get_size_x(), tex.blueprint_get_size_y()
    cap = 0 if UNDO else rule[1]
    if not UNDO and max(w, h) <= cap: continue
    bpp = 8 if 'Normal' in path or 'ORM' in path else 4
    s = max(w, h) / cap if cap else 1
    saved = mb(w, h, bpp) - mb(w / s, h / s, bpp) if cap else 0
    stats[rule[0]][0] += 1; stats[rule[0]][1] += saved
    if not DRY_RUN:
        tex.modify(); tex.set_editor_property('max_texture_size', cap); EAL.save_loaded_asset(tex)
total = sum(v[1] for v in stats.values())
for k, (n, s) in stats.items(): log.append('%-50s %4d textures  ~%6.0f MB saved' % (k, n, s))
log.append('TOTAL ~%.0f MB GPU/disk saved%s' % (total, '  (DRY RUN: nothing changed)' if DRY_RUN else '  (applied)'))
out = 'Texture budget\n' + '\n'.join(log)
open(os.path.join(HERE, 'texture_budget.txt'), 'w').write(out); unreal.log(out)
