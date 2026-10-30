# Castle aftermath gameplay — Codex, 2026-10-30

Five new Blueprint component EventGraphs implement independent gameplay state for the owner's requests. This is an **isolated compile/test handoff**, not a claim that the features are already playable. Existing game graphs are not replaced by this package.

| Card | Supplied code | Still required in the game |
|---|---|---|
| #41 fallen soldiers | Retry/confirmation controller, narrow source guard patch, read-only PIE diagnostic collector | Reproduce outside-gate death; merge a guard against fresh director/death exports; verify risen mesh/skeleton/visibility |
| #50 workshop/convoy | Order lifecycle, two-crew readiness, independent signed wheel phases, queen-defender targeting decision, deployment handshake | Shop/payment and placement UI; navigation, handle-following and animation; actual cannon spawn; zombie AI adapter |
| #162 battle memory | Persistent-in-session scars/repair bands, per-piece cleanup receipts, staged repair and safe restoration handshake | Debris bindings, salvage pile and work animation; existing gate HP/collision adapter; existing SaveGame wiring |
| #164 blob morph | Immediate partial form, 1.6 s melt overlapping a 4.2 s rise; continuous weights; matching-topology deformation reference | Current blob/zombie assets, corresponding sculpted targets, Unreal material/mesh binding and visual acceptance |
| #163 reactions | Event identity, per-reaction/global cooldowns, immediate interruption for important actions | Existing animation slots/poses and live action-state mapping |

Each `BPC_*` folder contains `EventGraph.txt`, `manifest.json`, and `<BP>_vars.txt` in the Master's BPVar clipboard format. Parent is **ActorComponent**, path `/Game/Codex/CastleAftermath_v1/<BP>`; Tick disabled. Call events explicitly from a future live adapter.

## Install — Master only

1. Unpack the checked archive. Read INTEGRATION.md and DIAGNOSIS.md before wiring anything.
2. In Unreal 5.3, run `create_shells_ue.py`. It creates only new empty assets and refuses an existing destination directory. It does not use unsupported `add_member_variable` or `refresh_all_nodes` APIs.
3. Paste the matching BPVar lines **one at a time** into My Blueprint. Check defaults against VARIABLES.md; array defaults must be empty. Variables must be accessible to their adapters.
4. Export each newly created empty EventGraph. Run `tools/applyall/applyall.py merge --dry-run --live <that fresh export> --manifest <component>/manifest.json --out <scratch>`. Only paste after `Validation: OK`. Then compile and save. If Unreal asks about self context, retain self context and refresh nodes in the editor before reviewing Compiler Results.
5. Run the isolated checks in ACCEPTANCE.md. Do not connect all five to gameplay until those checks pass. Send fresh graph exports for #165/#166 so integration can use exact node IDs and contracts.

## Verification performed

`test_gameplay.py` executes generated K2 node/link topology (including pure-pin reevaluation) plus the primitive snapshot and vertex-reference code. See `test-report.json` for the exact result. `risen41-guard-report.json` separately checks failure-branch reachability in the candidate director graph.

All five serialized pastes pass `applyall.py check`. All five manifests pass `merge --dry-run` against an **empty synthetic fixture for new components**: `Validation: OK`. These are not live exports; target identity was not checked for the empty fixture. `graph-validation.json` records that limitation and the complete output. Master must repeat the dry-run against each actual newly created graph. No existing-graph merge, Unreal compile, navigation, physics, animation, shader compile, or PIE acceptance has been performed on this host.

Run offline checks with Python 3:

```
python build_gameplay.py
python test_gameplay.py
```

Rebuilding changes serialized pin GUIDs; do not rebuild after a graph has been merged and then treat the regenerated paste as the same installed paste.

## Sources and boundaries

- Office AGENTS blob `a36087581d23ce72ff5802a048abe9e120101b07`; Master paste/manifest/BPVar rule in cafeteria comment `6518631829`.
- `tools/applyall/applyall.py` blob `1587443350e17eeb2a640542144af3743e43a7cb`.
- Existing `handoffs/risen-soldiers-41/bp/gen41.py` is the source for the narrow guard candidate. Its normalized SHA256 is in the guard report. It is **not** a fresh live director export. Do not paste a regenerated old director over the game.
- Laptop2 owns cart/workshop/badge art; metadata is `assets/laptop2/CampKit/cannoncart_meta.json`. We use radius 55.4 cm, separate local-Y wheel pivots, front pull and rear push handles.
- Fresh BP_Zombie export inspected: `handoffs/exports/master/2026-10-30/BP_Zombie.t3d`, blob `6513c2531d2bbc1342000b353a8d1379e8d85a98`. It does not replace the missing director, soldier-death, gate, save, or blob contracts in #165/#166.
- TGA owns realm gate/breach #189/#190, blob mines #191 and wall/tower geometric damage #193. This package does not duplicate them. Blob mine eggs are distinct from the rejected blob-to-zombie spawn effect #164.

## Realism rules applied to the design/code

Read the office knowledge README, photoreal playbook, laptop2 STANDARD and INDUSTRY_SECRETS §0, §3–4. Applied rule 3 (causal damage: blast scars survive repair; piece removal follows physical work), rule 8 (measured wheel travel, foot/hand contact and action interruptions), and rule 10 (one movement authority and coherent deformation time/seed). Material rules 1–2 and scene rules 4–7,9 remain **visual acceptance requirements**, not tests claimed here. No existing material, decal receiver, DBuffer setting, light, camera, mesh or save slot is changed. The morph reference is unverified in engine. Judge final assets under the office's locked grey-ball lookdev; respect the new one-piece decal side-by-side rule before any live material rollout.

Blueprint compiler/serializer derives from the office kit and Codex #48 implementation; all new logic is in `build_gameplay.py`. `battle_memory.py` is an offline serialization contract, **not runtime Python or an installed Unreal SaveGame implementation**.
