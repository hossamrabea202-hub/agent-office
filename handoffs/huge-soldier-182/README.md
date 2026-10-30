# #182 Huge soldier inside the castle — cause and fix

From: hossam gmail laptop2 (Claude), 2026-10-30. Target: `BP_ZombieRisen` EventGraph (paste + 2 rewires, no variables).

**Cause:** `BP_ZombieRisen` (the fallen soldier that rises, #41) is a child of `BP_Zombie`. BP_Zombie's BeginPlay rolls the
giant / wall-breaker size (`SetActorScale3D` 3× and 1.35×, and the Mesh 3×) — the risen soldier inherits that roll, so
now and then a soldier-looking zombie stands up three times tall inside the walls.

**Fix:** right after the parent BeginPlay call in BP_ZombieRisen, force the actor, `Mesh` and `KnightMesh` back to scale 1.
The #41 director still applies its own 1.2 for a risen commander afterwards.

**Master steps:** `python tools/applyall/applyall.py merge --live <BP_ZombieRisen EventGraph export> --manifest
handoffs/huge-soldier-182/manifest.json --out merged.t3d` (dry-run on 2026-10-30b: Validation OK, +6 nodes), paste,
compile. Test: let soldiers die near the wall for a few waves — no giant soldiers rise.
