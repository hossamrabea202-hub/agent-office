# #447 courtyard stairs: one baked, watertight asset (i5, 2026-11-02)

**What it is:** `SM_Stair447_Courtyard34`. It replaces the two 34-step courtyard flights F2 and F3: 182 boxes, the 1 cm
"coating" plates and the stepped side stones (#447).
- **Mesh:** one closed manifold.
  - 296 tris, 0 non-manifold edges
  - 2 slots: Tread (StepCap tone) / Body (StoneWall tone, limewash 0.5)
  - collision is complex-as-simple; the invisible `StairRamps` stay
- **Baked from a 1.87M-tri high poly:**
  - 4K normal (16-bit source)
  - 4K mask: R AO, G mortar joint, B foot-wear path, A per-stone tone
- **Material:** new `M_Castle_StairBaked`, a duplicate of `M_Castle_StoneWall_World`. The baked normal is blended over
  the world normal; joints are darker, the foot path is polished and the stones vary in tone. **Live materials and
  decals are untouched.**
- **Placement:**
  - F2: at (1250, 495, 0)
  - F3: at (1250, 3005, 0), Y scale −1
  - The merged meshes `CastleStones_0_0_4` / `0_1_6` get copies without the 8 stepped stones each (`*_s447`). The
    originals are not edited.

## Apply on the Master
1. Unzip into the project root. It brings `Content/CastleDefender/Environment/Castle/StairsBaked/` (assets already built).
2. Editor console:
   `py "<repo>/handoffs/stairs-447/work/apply_stairs447_ue.py" place --dry-run`
   Expect: 90 old pieces per flight, and the merged swap for both flights.
3. Then `... place --apply`, look at it, **save the map**.
4. Undo any time with `... place --revert`. Old pieces are only hidden (folder `Stairs_Old_447`), never deleted. The
   list of what was hidden is written next to the script.

## Checks
- **Play:** walk up and down both flights; no snagging at the top landing. Stand under the stair on the bench side.
- **Look:** no z-fighting on the side wall, worn nosings, darker mortar, no seams between treads.
- **Done on i5, without saving the map:** dry-run 90/90, apply, wide and close shots (`build/after_*.png` vs
  `build/before_*.png`). PIE is not possible on i5.

## Rebuild / other flights
`work/build_stair.py` with a spec json, then:
- `-- build`
- `-- bake <spec> <out> 4096`

The other 9 stair assets: specs come from `STUDY.md` (flights F0/F1, F4/F5, F14/F15, F17, F18, keep dog-legs, keep
steps, F16).
