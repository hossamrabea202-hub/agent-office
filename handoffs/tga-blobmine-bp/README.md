# BP_BlobMine (#154 bio-active blob minefield)

Made 2026-10-30 by `TGA (Claude)`. The owner asked TGA to take it because Codex is out of usage. It's ready to paste:
node blocks are cloned from the Master's exports, and `applyall check` prints `Validation: OK` (50 nodes).

## What it does

It's a land mine on laptop2's `SM_Flora_BlobMine` (component `Mine`, collision BlockAll so shots and blades hit it).
- **Lies still** until either:
  - the player steps within `TriggerRange` (**1.5 m**), checked every 0.2 s, or
  - it takes **any damage**: crossbow bolt, cannonball, sword.
- **Bursts:**
  - the mine vanishes, with a smoke puff and a squelch
  - **`MineDamage` (25)** to the player if they're within 2.5 m
  - **`BlobsMin`-`BlobsMax` (3-6) `BP_JellyBlob`** spill out around it (existing class, #18/#55)
  - **+`AttackedBonus` (3) more** when it was shot or hit rather than stepped on ("more when attacked")

## Paste steps (Master)

1. Run `py "<repo>/handoffs/tga-blobmine-bp/create_blobmine_bp_ue.py"`. It creates
   `/Game/CastleDefender/Realm/BP_BlobMine` with its `Mine` mesh component.
2. Open it. Paste the 9 lines of `BP_BlobMine_vars.txt` **one at a time**.
3. **EventGraph:** press **Ctrl+A, Delete**, paste `BP_BlobMine_EventGraph.txt`, compile.
4. **Run the same script again.** It swaps laptop2's 22 static `Realm_BlobMine_NN` for BP_BlobMine with the same
   transform, label and tag. If laptop2's `place_realm_ue.py` is re-run later, run this step again. Save the level.

**If a node comes in red:** right-click it, **Refresh Node**, and compile. Two nodes are adapted from similar ones:
`SetActorHiddenInGame` and `SetActorEnableCollision`.

## Test (acceptance)

1. Walk onto a blob mine in the realm. It bursts, you lose about 25 HP, and 3-6 jelly blobs come out.
2. Shoot another one from range. It bursts with 6-9 blobs and no damage to you.

## Not done here

- **The "slows" part of the card:** the jelly blobs carry whatever slow they already have, but the mine adds none of
  its own.
- **"1 blob per 3 hits on a tentacle, up to 40":** that belongs to the tentacle's own BP (`BP_TentacleVitals`), not to
  the mine.
