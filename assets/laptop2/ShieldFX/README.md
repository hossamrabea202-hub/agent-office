# Blue shield skill VFX textures (#180)

Generated 2026-10-30 by `hossam gmail laptop2 (Claude)` (`build_shieldfx.py`). 1K linear masks, alpha = mask, RGB a
suggested tint (blue-white). Import with sRGB off, Masks compression, clamp.

| Texture | Level | Use |
|---|---|---|
| `T_ShieldFX_RimGlow` | LV1 **Ward** | overlay material on the shield (like `M_XbowElectric`): emissive = mask × colour × pulse(1 Hz). Block % +10 |
| `T_ShieldFX_Shockwave` | LV2 **Bash** | 4×2 flipbook (8 frames, 0.4 s) on a ground-aligned Niagara sprite at the bash point; knocks zombies back 3 m |
| `T_ShieldFX_Runes` | LV3 **Runeward** | emissive overlay on the shield face, multiply by a panning noise for flicker; reflects 20 % damage |
| `T_ShieldFX_DomeCells` | LV4 **Bulwark** | the block dome's surface (#117 dome): tile 4× around, fresnel rim, cells drift (UV pan 0.03) |
| `T_ShieldFX_Spark` | all | hit sparks sprite (Niagara burst of 6, 0.3 s) when a block succeeds |

Material/Niagara wiring is Master/TGA work (same pattern as the crossbow LV4 electric overlay, #94). Colour: ward blue
(0.35, 0.65, 1.0); the LV4 dome a little more cyan.
