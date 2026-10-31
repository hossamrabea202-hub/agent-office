# #314 "press T" reminder + #313 "all cannons are mounted": one tiny toast

By `adjustedfilm (Claude)`, 2026-10-31, from two owner `W:` cards:
- **#314:** *"when skill tree has points to be used, a tiny fade in fade out notification saying press T comes every 10 minutes"*
- **#313:** *"when all canons occupied, mount a canon is not clickable, with a tiny notification fade in and out ( all canons are mounted )"*

Built on `handoffs/exports/master/2026-10-30b` (BP_NoticeHUD, BP_BarracksHUD, BP_SkillTreeHUD, BP_Cannon).

## Pre-checks (done)

| File | fix_impure | applyall check | dry-run merge |
|---|---|---|---|
| `BPC_Toast_graph.txt` (new component, 115 nodes) | no changes | **OK** | (new BP) |
| `NoticeHUD_ToastHook_graph.txt` (10 nodes) | no changes | **OK** | **OK** on NoticeHUD 10-30b + the #307 antidote merge |
| `BarracksHUD_CannonFull_graph.txt` (17 nodes) | no changes | **OK** | **OK** (5 rewires) |

No self-calls to own events (the #254 lesson): timers call `RemindPoll` / `CannonPoll` by name, and RemindPoll sets the toast
variables itself.

## What the player gets

- **The toast:** one tiny line at 80 % screen height.
  - It fades in over 0.35 s, holds, and fades out over 0.6 s (3 s in all).
  - Small Cinzel, warm white, with a 1 px shadow and a faint dark backing.
  - It runs on real time, so it also shows in paused menus.
- **#314:** while you have unspent skill points, **"Unspent skill points - press T"** shows 10 minutes after the points
  appear, then every 10 minutes.
  - The points come from the skill tree's own formula: `Level - 1 - MPC_SkillTree.St.A`.
  - Game time is used, so the 10 minutes don't count while paused.
  - Spending every point stops the reminder and resets the clock.
- **#313:** when every cannon is taken, the barracks menu's **Man a cannon** row is dimmed to 45 %. Clicking it sends no
  order and shows **"All cannons are mounted"**.
  - A cannon counts as taken if the player rides it (`BP_Cannon.bMounted`), or if a soldier holds order 3 (Man a cannon)
    with his goal within 5 m of it.
  - Nothing in the game stored this, so it's worked out once a second.

## Steps (Master)

1. `py "<repo>/handoffs/toast-313-314/setup_toast_ue.py" --dry-run`, then run it again without `--dry-run`. It makes
   `/Game/CastleDefender/Gameplay/Castle/BPC_Toast` and adds it to the hero as **Toast**.
2. Open BPC_Toast. Paste the 9 lines of `VARIABLES_BPVar.txt` on the VARIABLES header, one at a time, then Compile.
3. Paste `BPC_Toast_graph.txt` into BPC_Toast's EventGraph. Compile and save.
4. **BP_NoticeHUD.** This needs #307 (the antidote) in first.
   1. Paste `NoticeHUD_ToastHook_graph.txt`.
   2. Make 4 links:

   | # | From | To |
   |---|---|---|
   | 1 | `AntOut` then 0 (now goes to `NoticeIn`) | **ToastIn**.execute (replaces the old link) |
   | 2 | **ToastOut** then 0 | `NoticeIn`.execute |
   | 3 | `CX_1` (Event Receive Draw HUD) Size X | **ToastSizeX**.A |
   | 4 | `CX_1` Size Y | **ToastSizeY**.A |

   Compile and save. Or use `applyall.py merge` with `manifest_noticehud_toast.json`.
5. **BP_BarracksHUD.**
   1. Paste `BarracksHUD_CannonFull_graph.txt` (17 nodes).
   2. Make 5 links:

   | # | From | To |
   |---|---|---|
   | 1 | `CX_548` (the "Man a cannon" click branch) **then** (now goes to `CX_549`) | **CnIf**.execute (replaces the old link) |
   | 2 | **CnToOrder** then 0 | `CX_549` (GetAllActorsOfClass BP_Cannon).execute |
   | 3 | **CnToNext** then 0 | `CX_595`.execute (the next row's test; it already has other inputs, keep them) |
   | 4 | `CX_1321` (MakeColor of the row label) ReturnValue | **CnColIn**.A |
   | 5 | **CnSel**.ReturnValue | `CX_1333` (DrawText "Man a cannon") **TextColor** (replaces the link from CX_1321) |

   Compile and save. The names are from the 10-30b export. If one moved, find it by its role in the table.

## Tests (Play)

1. **Toast:** run `Toast` on the hero's Toast component from editor Python, or wait for test 2. A tiny line fades in and
   out low on the screen.
2. **#314:** gain a level and don't spend the point.
   - 10 minutes later (set `RemindEvery` to 30 on the component's defaults to test quickly) the toast says
     "Unspent skill points - press T", and it repeats.
   - Spend the point: no more reminders.
3. **#313:**
   1. Order soldiers to **Man a cannon** until every cannon is crewed, or mount the last one yourself. The row dims within
      1 s.
   2. Click it: nobody moves, and the toast says "All cannons are mounted".
   3. Order one crew elsewhere: the row is normal again and works.
4. No "Accessed None" in 2 minutes of Play.

## Tuning (one minute, BPC_Toast class defaults)

| Variable | Default | What it does |
|---|---|---|
| `RemindEvery` | 600 s | how often the press-T reminder repeats |
| `ToastDur` | 3 s | how long the toast stays |
| `CannonReach` | 500 cm | how near a crewman's goal must be to count a cannon as taken |

## Found while building this

The 10-30b `BP_BarracksHUD` export carries **3,936 unlinked duplicate nodes**: `K2Node_*` copies that share PinIds with
live nodes. That's about half the graph. They look like a leftover copy from an old paste. They do nothing, but they make
this HUD heavy and slow to edit.

A separate cleanup card would remove them: delete the unconnected `K2Node_CallFunction_*` / `K2Node_VariableGet_*`
islands, then do a fresh export and run `applyall check`. That cleanup isn't part of this hand-off.
