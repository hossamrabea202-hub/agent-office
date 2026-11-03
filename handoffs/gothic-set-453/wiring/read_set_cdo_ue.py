# #453 (i5): read-only dump of BPC_ObsidianSet's class defaults (the data v4 extends). Writes set_cdo.json next to this file.
import json, os, unreal
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/gothic-set-453/wiring/set_cdo.json'
bp = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet')
cdo = unreal.get_default_object(bp.generated_class())
def conv(v):
    if isinstance(v, (int, float, str, bool)) or v is None: return v
    if isinstance(v, unreal.Transform):
        t, r, s = v.translation, v.rotation.rotator(), v.scale3d
        return {'t': [t.x, t.y, t.z], 'r': [r.roll, r.pitch, r.yaw], 's': [s.x, s.y, s.z]}
    if isinstance(v, unreal.Name): return str(v)
    if isinstance(v, unreal.Object): return v.get_path_name()
    try: return [conv(x) for x in v]
    except TypeError: return str(v)
d = {}
for n in ('PieceId', 'PieceBone', 'PieceOffset', 'AvailMask', 'KnightCover', 'BundleMask', 'PartPrice', 'PartBundle', 'BundleCost', 'BundleNames',
          'TierAt', 'TierDR', 'ObsPriceMul', 'ShockRadius', 'ShockDamage', 'ShockCooldown', 'HiddenMat'):
    try: d[n] = conv(cdo.get_editor_property(n))
    except Exception as e: d[n] = 'ERR %s' % e
json.dump(d, open(OUT, 'w'), indent=1)
for k, v in d.items(): print(k, str(v)[:160])
