# #294 Cannonballs bounce off the realm bubble; soldiers, zombies, wasps and the hero pass through

By `adjustedfilm (Claude)`, 2026-10-31 late. I took this over from TGA, who is busy on #361.
Owner: "Real should bounce back canon bullets on ground but soldiers and zombies and flies and hero can get through".

## Why the old fix doesn't work any more

#284 bounces a ball on its **Event Hit** with the bubble. The owner's reshaped bubble (`Realm_Bubble_Owner`) is
**OverlapAllDynamic**, so a ball never *hits* it and flies straight through. The #299 fix changed the bubble's collision
and its mesh's collision setting, but the owner's rule now is to leave the bubble alone.

## The fix: the ball watches its own path

A new component, **`BPC_RealmBounce`**, goes on **BP_Cannonball**. Every frame it traces from where the ball was to where
it is now, against the **real bubble mesh** (Component Line Trace, complex). This works with overlap collision, with any
shape and at any ball speed, because no frame can skip the wall.

When the path crosses the membrane:
- the ball is put 30 cm back outside;
- its velocity is mirrored on the surface, at half speed (`BounceKeep` 0.5);
- it is forced downward (`MinDown` 200 cm/s or more), so it lands **outside** the realm and explodes there as usual;
- it bounces only once.

Nothing else is needed:
- Pawns already pass, because the bubble only overlaps them.
- When the realm collapses (#284 hides the bubble), the balls fly normally.
- It doesn't fight #284's hit-bounce if that was pasted: with overlap collision that hook never fires, and if the
  bubble ever blocks again, the hit stops the ball before my trace sees a crossing.
- The bubble's **mesh, material, transform and collision are not changed.** The setup only adds the tag `RealmBubble`
  if it is missing; #284 uses the same tag.

## Steps (Master: paste only, about 5 minutes)

1. `py "<repo>/handoffs/realm-bounce-294/setup_realmbounce294_ue.py" --dry-run`, then run it without `--dry-run`.
   - It creates `/Game/CastleDefender/Gameplay/Realm/BPC_RealmBounce` and tags the bubble.
   - It reports the bubble's collision: it must be Query (QueryOnly or QueryAndPhysics); OverlapAllDynamic is fine.
   - If it prints `WARNING: also tagged …`, an old dome still has the tag. Remove the tag from the old dome.
2. Open BPC_RealmBounce → My Blueprint. Paste the 6 lines of `VARIABLES_BPVar.txt` on the VARIABLES header, one at a
   time. Compile.
3. In the EventGraph, paste `BPC_RealmBounce_graph.txt` (58 nodes). Compile, then Save.
4. `py ".../setup_realmbounce294_ue.py" --attach --dry-run`, then run it with `--attach` only. This adds the component
   `RealmBounce` to BP_Cannonball, compiles and saves.

Pre-checked: `fix_impure.py` finds nothing to fix, and `applyall check` passes (**Validation: OK**, 58 nodes, 68 links).
Not compiled yet, because that needs the editor.

## Checks (Play)

1. Fire a cannon at the bubble. The ball bounces off downward, lands outside the realm and explodes there.
2. Fire again from another angle, or at the tall part. It still bounces off; no ball reaches the inside.
3. Walk the hero in, and send soldiers in. Everyone passes through the wall, and so do zombies and wasps.
4. A cannon fired away from the bubble behaves exactly as before.
5. After the realm collapses, balls fly through where the bubble was.
6. Two minutes of Play with cannons firing: no "Accessed None" from BPC_RealmBounce.
7. Screenshot or clip with `tools/shot.js --card 294`.

**Tuning:** on BP_Cannonball, select `RealmBounce` and change `BounceKeep` (how much speed it keeps) and `MinDown` (how
hard it is pushed down).
