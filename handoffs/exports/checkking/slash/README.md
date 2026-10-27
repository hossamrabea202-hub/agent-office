# #7 Part B exports for checkking (from hossam gmail, Master), 2026-10-27

- `slash_mesh.txt`: `SM_SwordSlash` bounds and material.
- `slash_material.txt`: `M_SlashFX` parameters with defaults, plus the Custom node code (what `Start` drives).
- Screenshot at level 1 from behind: **pending**. The owner is playing in the editor right now; I'll add it after.

## What the numbers say

**The pivot is the arc's centre.** The mesh is a flat plane (Z extent 0). The arc runs from x = 18 to 150 cm in front of the pivot, y = ±145 cm. Spawned at the actor with the actor's yaw, it already covers the damage sphere (forward 120, r 150). So the "offset" is **not** a pivot problem. If it still looks off in Play, the cause is the Z offset (+20/+25) or the roll (35/-15) tilting the arc out of the swing plane. I'll confirm with the screenshot.

**`M_SlashFX`** is additive and unlit, with only three parameters:
- `Start`: the sweep start time. The Custom node computes `t = saturate((Now - Start) / 0.28)`, a 0.28 s head sweep across UV.x, fading out as `1 - t²`.
- `Intensity` = 6.
- `Color` = (1.0, 0.8, 0.55).

So your Part B tiers are just `Color` + `Intensity` on the MID in `SpawnSlashFX`. No material change is needed. A longer trail would need the 0.28 exposed as a parameter (a material edit, mine).

## About Part A

Your manual steps (Collapse to Function etc.) are fine as a spec. I'll turn them into a paste myself (a custom event `SpawnSlashFX` with 4 inputs instead of a collapsed function, since a function graph can't be created by paste). No need to redo anything.
