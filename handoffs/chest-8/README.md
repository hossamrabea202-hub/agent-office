# #8 Treasure chest in the old outer (East Front) tunnel: paste-only

By `adjustedfilm (Claude)`, 2026-10-31. Owner card #8: *"a closed treasure chest containing a good amount of money in the
middle of the tunnel, must be closed, open with E, it opens and its shiny and gold obtained and shine gone (surrounded by
dangerous creatures protecting the tunnel)"*. The owner added today: **E opens it**, **glow VFX with a reveal**, **a gold
cashing sound**.

Replaces the C++ `TGAChest` plugin route (TGA 2, needs a native rebuild, never integrated). Nothing here needs C++.

## Pre-checks (done)

| Check | Result |
|---|---|
| `fix_impure.py BP_TreasureChest_graph.txt` | **no changes** (save checks and casts are on the exec chain) |
| `applyall check` | 203 nodes, 236 links, **Validation OK** |
| existing Blueprints changed | **none** (it uses BP_ZombieHUD.Gold, BP_NoticeHUD.PushNotice and BP_CastleSave as they are) |
| self-calls to own events | **none** (ChestPoll runs from a timer by name, the #254 lesson) |

## What the player gets

1. **Walking down the tunnel:** a warm gold glow breathes in front of the closed chest, with a small twinkling star
   glint at the lid seam.
2. **About 35 m away, the first time:** the guards appear:
   - **4 zombies** along the tunnel, 4.5–9 m in front of and behind the chest;
   - **a half-horse zombie** 7.5 m behind it.

   The tunnel is only 2.5–5 m wide, so they spawn along it, not in a ring.
3. **At the chest:** the notice says **[E] Open the chest**.
4. **E:**
   - the latch clicks and the lid creaks open over 0.9 s (ease-out) and lands back with a thud;
   - **gold light shafts rise out of the chest** (revealed bottom to top in 0.45 s), with drifting gold sparkles;
   - the light bursts to 4x, and the glint flashes off;
   - **a ka-ching chime and a shower of coins** play at 0.35 s;
   - the banner says **Treasure! +1500 gold**, and the gold is added.
5. **The shine dies out** over the next 1.6 s. The chest stays open and dark.
6. **Saved at the moment it opens** (slot `CastleSaveChest1`): it never pays twice, and a reload shows it open, with no
   guards and no shine.

## Steps (Master)

1. `py "<repo>/handoffs/chest-8/setup_chest8_ue.py" --dry-run`. Read the Output Log: it lists the chest mesh candidates
   and the body + lid it picked (searched in `/Game/AncientTreasures` first). Then run it again without `--dry-run`. It
   makes:
   - `/Game/CastleDefender/Gameplay/Chest/`: SFX_ChestOpen, SFX_GoldCash, M_ChestRays, M_ChestGlint;
   - BP_TreasureChest, with Body, Hinge → Lid, Glow, Glint and Rays.

   If it picked the wrong meshes, run it again with `--body <StaticMesh path> --lid <StaticMesh path>`.
2. Open BP_TreasureChest. Paste the 21 lines of `VARIABLES_BPVar.txt` on the VARIABLES header, one at a time, then
   Compile.
3. Paste `BP_TreasureChest_graph.txt` into its EventGraph. Compile and save.
4. Run `py "<repo>/handoffs/chest-8/setup_chest8_ue.py" --place --dry-run`, then again without `--dry-run`. It puts
   **TreasureChest_8** on the middle East Front tunnel floor, facing the castle end. `--unplace` removes it.

## Tests (Play)

1. Walk the tunnel: the glow breathes in front of the closed chest. About 35 m out, 4 zombies and the half-horse appear
   and come for you.
2. At the chest: **[E] Open the chest**. Press E: the lid opens, the rays rise, the coin shower plays, and **+1500**
   gold shows in the banner and on the HUD.
3. A few seconds later: no rays, no glow, no glint. The chest sits open.
4. Press E again: nothing happens.
5. Quit and Play again: the chest is open, and there are no guards and no gold.
6. To test again: delete `Saved/SaveGames/CastleSaveChest1.sav`.

## One-minute fixes (Master may do them on the spot)

| If | Change on BP_TreasureChest (class defaults or the placed one) |
|---|---|
| the lid opens forward / into the chest | `LidPitch` -105 → **+105** |
| the hinge is on the wrong side (the pack's chest faces -X or ±Y) | rotate the placed actor 180° / 90°, or move the `Hinge` component to the lid's back edge |
| too much / too little gold | `Reward` (per placed chest) |
| the glow is too strong / weak | `GlowBase` (60 cd); the rays: M_ChestRays `Intensity` (12) |
| more chests | place more, each with its own `ChestId` |

## Rules applied

- **Realism KB:** a real light behind every glow (rule 6), 2700 K warm gold, shadows off for a small fill.
- **INDUSTRY_SECRETS:**
  - every motion has its own curve (ease-out lid, ease-out ray growth, fades);
  - one gold palette for the glow, rays, sparkles and glint;
  - true dark in the tunnel once the shine dies (§2: true black only in caves and small rooms).
- **Sounds:** synthesised and licence-free (`assets/adjustedfilm/Chest8/source/make_sfx_chest.py`):
  - **lid:** latch, wood creak (stick-slip through wood body modes), thud;
  - **gold:** two struck bells (bell partials 1 / 2.76 / 5.40 / 8.93) plus 55 inharmonic coin hits.

  They haven't been heard in engine yet; tell me if they need changes.
- **No licensed asset in the repo:** the chest mesh comes from the pack on the Master's PC.
