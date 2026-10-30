# #214 Golden crossbow fires like a machine gun (fix)

By `checkking (Claude)`, 2026-10-30 night. Built on `handoffs/exports/master/2026-10-30b/BP_Crossbow.T3D` (EventGraph).
Dry-run merge: **Validation OK** (8 nodes, +8 links).

**Fix.** A hard fire-rate gate in BP_Crossbow that holds whatever retriggers the shot (input trigger setup, a fast
reload at high XbowUp, the golden weapon):
- `CX_106.then → CoolIf` (GameTime ≥ `NextFireAt`) `→ CX_114`. An early click is ignored.
- On every shot: `CX_114.then → SetNextFire` (`NextFireAt = GameTime + FireCooldown`) `→ CX_123`.
- `FireCooldown` defaults to **1.0 s**, about the old crossbow's 0.35 + 1.05 s reload. Tune it on the class defaults.

**Steps.**
1. Run `py "<repo>/handoffs/xbow-firerate-214/add_vars_214.py"`. It adds the 2 variables.
2. Export BP_Crossbow's EventGraph, then run `applyall.py merge --manifest handoffs/xbow-firerate-214/manifest_crossbow.json`.
3. Paste, Compile and Save.

**Check.** Golden crossbow: hold and spam the fire button. At most one bolt per second. The normal crossbow behaves as
before.
