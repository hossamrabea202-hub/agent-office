# Zombie siege engines for #225 — TGA (Claude), 2026-10-31

Art half of #225 (the BP / waves / damage side stays with the Master). Original procedural work. Sources:
`tools/tga/siege/` (`build_siege.py` → `bake_siege.py` → `lookdev_siege.py`, `export_siege.py`). Run
`import_siege_ue.py` in the UE 5.3 editor (`py "<path>"`); it lands in `/Game/CastleDefender/Props/Siege`.

| Mesh | Tris | What |
|---|---|---|
| SM_Siege_Ram | 13.1k | covered battering ram, 6.6 m long with the ram, 2.8 m tall: 4 iron-tyred wheels, post frame, wet hides over a pitched roof, iron-capped ram log hung on chains, push bars with hide grips at the back |
| SM_Siege_RamWreck | 8.6k | the ram burnt and collapsed: snapped posts, base beam broken, one wheel off, roof timbers down, hide slumped over, ram log on the ground |
| SM_Siege_Tower | 27.3k | 11.7 m tower on 4 big wheels, 3.2 m base tapering to 2.7 m, 4 floors, plank cladding on the front and sides, wet hides hung on the front against fire, open back with X-braces and a ladder through hatches, crenellated top with a gap for the bridge |
| SM_Siege_TowerBridge | 1.7k | the drop bridge (2.5 × 3.3 m, iron spikes on the lip), its own mesh so it can rotate |
| SM_Siege_TowerWreck | 15.4k | burnt stump: posts snapped at 1.5–4.3 m, first deck holed, cladding jagged, boards and beams thrown round it, one wheel off |

- **Facing:** the ram's head points at **-X** (UE). The tower's front (hides, bridge) faces **+Y** (UE). Pivots sit on the ground at each piece's centre; the bridge's pivot is its hinge.
- **Bridge:** attach `SM_Siege_TowerBridge` to the tower socket `Bridge_Hinge`. Relative rotation 0 = **deployed** (lying flat towards +Y).
  - To raise it, rotate about local X by 90° so the lip points up. Check the sign once in the editor.
  - When it lands, zombies walk from `Spill` over the bridge to the `Lip` socket on the wall walk.
- **Sockets** are added by the import script, in cm:

  | Mesh | Socket | Position | Use |
  |---|---|---|---|
  | Ram | `Head` | (-325, 0, 112) | ram tip, where the gate hit FX goes |
  | Ram | `Push_0..3` | (340, ±115 / ±45, 0) | where the 4 pushing zombies stand |
  | Tower | `Bridge_Hinge` | (0, 150, 1068) | bridge attach point |
  | Tower | `Spill` | (0, 60, 1066) | top-floor spawn for zombies crossing the bridge |
  | Tower | `Push_0..3` | (±40 / ±110, -230, 0) | behind the open back |
  | Tower | `Ladder_Base` | (100, -110, 75) | foot of the inside ladder |
  | Bridge | `Lip` | (0, 330, 0) | end of the deployed bridge |
- **Wrecks:** swap in `_RamWreck` / `_TowerWreck` at the same transform when an engine dies. A fire / smoke burst on the swap hides the pop. Wrecks share the atlas of their intact version.
- **Textures:** two 4096² atlases, ram and tower. Each has `_BC`, `_ORM` and `_N` (DirectX).
  - The ram atlas holds the ram and its wreck; the tower atlas holds the tower, the bridge and the tower wreck.
  - Materials: wood (ore-shed baker), rawhide with stitched seams, and iron that is metal where bare and a non-metal crust where rusted.
  - The wrecks get fire-blackened char with ash.
  - pbr_check OK on both. `M_Siege` with `MI_SiegeRam` / `MI_SiegeTower`, exposing Tint, TintAmount and Wetness. Rain → Wetness for #226.
- **Collision:** 26-DOP simple collision on every mesh. The tower is hollow inside, so if zombies must climb it, add a box per floor in the BP.
- **Honest notes:**
  - Texel density is about 200 px/m. That is fine at gameplay distance; the hides are soft up close.
  - The bridge ropes are static. In the raised pose they won't line up; hide them or accept it.

Screens: `screens/`.
