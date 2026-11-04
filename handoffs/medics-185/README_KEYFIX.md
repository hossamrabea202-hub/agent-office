# Medics buy key fix (owner via checkking, 11-04, card #502). Script, no paste

Bug (found by the #482 audit, read from `BPC_Medics_graph.txt`): `MedKeys` -> `mdSetMWas40` (MWas = key M down now) -> `mdIfM41` (key down AND NOT MWas).
MWas is set to "down" just before it is tested, so the condition is never true: **the M key can never recruit a medic.**

Fix (`ops_medics_key_fix.json`, graph_ops): test first, store after, on both branches:
`MedKeys.then -> mdIfM41`; `mdIfM41.then -> mdSetMWas40 -> mdIfFull45` (the old buy path, unchanged after it); `mdIfM41.else -> new Set MWas` (same key value).
So "was the key down last frame" is still last frame's value when it is tested: one recruit per key press.

Steps on i9 (editor idle, not in Play; your local paths):
1. `py <repo>/handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/medics-185/ops_medics_key_fix.json --dry-run` -> `check OK`
   (needs MedKeys, mdSetMWas40, mdIfM41, mdIfFull45, mdKeyM34 by name; if it stops, send i5 the output).
2. Same with `--apply` -> backup `Saved/bak472/BPC_Medics.uasset.fixMedKey`, expect `RESULT compile True | link/value failures [] | new errors []`.
Test (Play): at the barracks NPC press M with 150+ gold: one medic, gold -150; hold M: still one; press again: a second, up to 4.

Same bug, NOT fixed here (owner's call, same pattern): BPC_Flares fxSetFWas32 > fxIfBuy33, BPC_Cavalry ccSetLWas49 > ccIfL50,
BPC_CastleUpgrades cuSetJWas62 > cuIfJ63.
Not tested on i5 (i5's editor was busy after its restart); built from the #185 graph file. The dry run on i9 checks every node and pin first.
