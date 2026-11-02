# #437 P1: wave 3 camera shake + "drums" that never stop (i5 / adjustedfilm, 2026-11-02)

**Cause (from the BP_FleshBrute export, 10-31):** brutes arrive with wave 3. While a brute attacks the gate it loops
every 2.4 s: `CX_85` GateDamage → `CX_88` PlayWorldCameraShake (BP_CannonShake_Impact, **full within 25 m, felt up to
120 m**) → `CX_89` Explosion_Cue at pitch 0.38 + `CX_90` heavy metal hit, both **without attenuation** (full volume
everywhere) = the endless deep "drum" booms + shaking until the gate falls. The big slam (`CX_462`, 90 m) adds more.

## Fix
1. **One-shot per brute** (3 pasted nodes): `GateShook` bool. First gate slam: shake + booms + set GateShook. Later
   slams: straight to `CX_91` (dust emitter), so the gate damage and the attack loop are unchanged.
2. **Keep it local** (pin values, no paste): gate-slam shake 2 m full / 18 m reach (was 25 / 120 m); big slam 3 / 25 m
   (was 15 / 90 m); booms at half volume.

| File | What |
|---|---|
| `gen_brute437.py` → `build/FleshBrute_GateShookOnce_graph.txt` | 3 nodes: Get GateShook, Branch `GtIfShook`, Set `GtSetShook` (applyall OK, fix_impure no change) |
| `fix_brute437_ue.py` | `--dry-run` / `--values` (no paste) / full (needs the paste) / `--revert`; checks every current value first |

## Apply (i9, after Alien's test)
1. `py "<repo>/handoffs/brute-shake-437/fix_brute437_ue.py" --dry-run` → all nodes found except the 3 new ones; every
   value "ok".
2. Open BP_FleshBrute → EventGraph → paste `build/FleshBrute_GateShookOnce_graph.txt` (anywhere).
3. `py ".../fix_brute437_ue.py"` → values set, GateShook added, one-shot wired, compiled, saved.
   (No paste possible? `--values` alone already stops the castle-wide shake and halves the booms.)

## Checks (Play, wave 3 or BruteDirector FromWave = 1)
- [ ] A brute's first gate slam: one shake near the gate + the boom. Later slams: dust and gate damage, **no** shake,
      no boom.
- [ ] Standing on the far wall: no shake from a brute at the gate.
- [ ] The gate still takes damage and breaks as before.
Undo: `fix_brute437_ue.py --revert`.
