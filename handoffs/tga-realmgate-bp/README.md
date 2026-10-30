# BP_RealmGate (#169 stage 1 gameplay)

Made 2026-10-30 by `TGA (Claude)`. The owner asked TGA to take it because Codex is out of usage. It's ready to paste:
node blocks are cloned from the Master's and laptop2's exports (BP_Zombie, BP_CastleGateControl), and `applyall check`
prints `Validation: OK` (71 nodes).

## What it does

It's a small actor at `Realm_Gate_Trigger` that drives laptop2's gate pieces (`Realm_Gate_LeafL/LeafR/Bar`, hinge
pivots). Everything runs in Tick, with no input binding and no timers:
- **Prompt:** "E  Open" (blue text, 1.2 m up, always turned to the player) shows when the player is within `UseRange`
  (3 m) and the gate is closed.
- **Open:** pressing **E** there opens it.
  - Both leaves swing `OpenAngle` (**95°**) in opposite directions over **1.2 s** (`OpenRate` 0.833/s) with
    smoothstep easing.
  - The bar lifts 1.5 m.
- **Close:** once the gate is fully open and the player has been out of range for **3 s** (they've passed), it eases
  shut. Coming back into range holds it open.
- **Zombies never open it.** Only the player's E does, and the closed leaves block physically.

## Paste steps (Master)

1. Run `py "<repo>/handoffs/tga-realmgate-bp/create_realmgate_bp_ue.py"`. It creates
   `/Game/CastleDefender/Realm/BP_RealmGate` with its `Prompt` TextRender component.
2. Open it. Paste the 13 lines of `BP_RealmGate_vars.txt` **one at a time** in My Blueprint.
3. **EventGraph:** press **Ctrl+A, Delete**, paste `BP_RealmGate_EventGraph.txt`, compile.
4. **Run the same script again.** It spawns `Realm_Gate_BP` at `Realm_Gate_Trigger` and wires LeafL, LeafR and Bar,
   their base yaw and the bar's rest location. It needs laptop2's `place_realm_ue.py` (#169) in the level first. Save
   the level.

**If a node comes in red:** right-click it, **Refresh Node**, and compile. Two nodes are adapted from similar ones:
`K2_SetWorldRotation` (the prompt turning) and `K2_SetActorLocation` (the bar).

## Test (acceptance)

1. Walk to the gate. "E  Open" appears within 3 m.
2. Press E. The leaves swing open 95° over 1.2 s and the bar lifts.
3. Walk through and away. 3 s later the gate closes behind you.
4. Zombies inside can't open it.

## Tune

- **The leaves swing the wrong way** (toward the player): set **`SwingSign` = -1** on `Realm_Gate_BP`.
- **Other values:** change `OpenAngle`, `OpenRate` and `UseRange` on the instance.

## Not done here

- **Nav modifier:** I didn't add one to the opening. The closed leaves block physically, and realm zombies spawn inside
  from their own points (stage 2).
- **The lever:** it doesn't move.
