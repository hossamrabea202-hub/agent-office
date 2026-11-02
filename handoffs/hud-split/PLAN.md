# BP_ZombieHUD split plan (i5 / adjustedfilm, 2026-11-02, from i9's queue, owner OK in the fast chat 10:17)

**Why:** BP_ZombieHUD's EventGraph is one `ReceiveDrawHUD` chain of **4,758 nodes (17.8 MB of T3D)**. Every save
recompiles all of it, it crashed the i5 editor several times (memory), and every new HUD feature pastes into it. Moving
features into ActorComponents (the #411 / #74 pattern: `BPC_X` with a custom event `Draw(Hud)`, called from a 3-node
hook in the HUD) makes each feature compile, paste and roll back on its own.

## What's in the graph (analysis of the 11-01 20:13 export; tools: `regions.js`, `varsplit.js`, `chunks.js`)

The features are wired in series (no Sequence fan-out, no comment boxes), each generator placed its feature in its own
band of the canvas, so the bands are the features:

| Band (y) | Nodes | MB | Feature (texts it draws) | Vars only it uses | Shared HUD vars it reads |
|---|---|---|---|---|---|
| #7 105904..114304 | **1,969** | 7.37 | **Vesna's shop** ("Vesna, the Veiled Blade", prices, "Not enough gold, hunter.") | MsgT, SelSlot, FreeCell | ShopV, Gold, SovV, PlateV, XbowV, *Loc (6) |
| #5 78560..84368 | 1,177 | 4.24 | Cannon prompts, LEVEL UP / WAVE banners, gear pick-up | PickT, PrevLoc | Held, SovV, PlateV, XbowV, *Loc, ShopV |
| #10 130960..136352 | 724 | 2.88 | Pause / main menu (Resume, Restart, Settings, Quit, Begin the Siege) | Ore | ShopV, StatV |
| #6 93360..98256 | 346 | 1.21 | Stats panel (XP, kills, best hit, gold) | | StatV, ... |
| #2 20320..20448 | 314 | 1.25 | Title card "DEFENDER OF THE CASTLE" | | XbowV, SovV, Held |
| rest (#0 #1 #3 #4 #8 #9) | 228 | 0.8 | Vesna prompt, inventory/gold glyphs, death text, stat effects | | |

## Order
1. **BPC_VesnaShop** (band #7, 41 % of the graph). Biggest win, cleanest boundary: 3 own variables, 11 shared reads.
2. **BPC_GearHUD** (band #5): cannon prompts + banners + gear pick-up.
3. **BPC_GameMenu** (band #10).
4. **BPC_StatsPanel** (band #6), then the small bands stay or go together into `BPC_HudMisc`.

After step 1 the HUD graph drops to ~2,800 nodes; after step 3 to ~900.

## How each move is built (generator, file-side, then i9 pastes)
1. Fresh export of BP_ZombieHUD EventGraph (requested; never build on the 11-01 export).
2. Generator `gen_split.js <band>`: takes the band's nodes, and
   - turns every self-context HUD call (DrawText, DrawTexture, DrawRect, Project, GetOwningPlayerController, ...)
     into a call with **Target = Hud** (the custom event's input);
   - shared HUD vars become `Hud → Get <Var>` / `Set <Var>` on a BP_ZombieHUD reference (the event input is typed
     BP_ZombieHUD, so no cast per node);
   - the band's own vars become component variables (created by the setup script);
   - the band's first exec input and last exec output become the custom event `Draw(Hud)` entry and its end.
3. Setup script (`setup_split_ue.py --dry-run` / apply): backup `BP_ZombieHUD_BACKUP_SPLIT1`, create the component +
   variables + defaults, add it to BP_ZombieHUD.
4. i9 pastes the component graph (one paste into the small component, not into the HUD) and the 3-node hook; a rewire
   script wires the hook where the band was and **unlinks the old band (left in place, `--revert` puts it back)**.
   Deleting the old band is a separate, later step after a Play check.
5. Checks: applyall check / dry-run merge on the export, `fix_impure.py`; Play: Vesna's shop opens, buys, refuses
   with "Not enough gold", the gear shows, nothing else on the HUD changed.

## Risks
- Shared vars written by the shop (Gold, the *Loc / *V gear vars) must be written on the HUD, not on component copies:
  the generator only creates component vars for the "only here" list.
- Latent nodes (Delay) can't live in a function, but a custom event is fine.
- Nodes in a band that are wired into another band (cross links) are listed by the generator; it refuses to build if
  any exist, so nothing silently breaks.
