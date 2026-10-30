# Atmosphere sprites (owner list 4 / 5 / 19)

Generated 2026-10-30 by `hossam gmail laptop2 (Claude)` (`build_atmos.py`). Import with sRGB off, alpha = mask.

| Texture | Use |
|---|---|
| `T_Atmos_DustMotes` (4×4 flipbook) | Niagara sprite, random sub-image, 0.5–2 cm, slow drift + turbulence, only inside sunbeams and the barracks |
| `T_Atmos_Sunbeam` | god-ray card: translucent unlit plane from windows/the gate arch, additive 0.15, slight sway |
| `T_Atmos_FogCard` (2048×1024, tiles in u) | valley mist at dawn: 3 big planes at different depths, scrolling 0.002 u/s each, additive 0.08–0.15, fade by camera distance |
| `T_Atmos_RealmFog` (tiles in u) | the realm's low pink fog inside the dome: same setup, translucent (not additive) 0.25, `EmissiveBoost` 1.5 for the vein streaks |

Rules: never full-screen, never more than 3 overlapping cards; keep the card edges off-screen or behind geometry.
