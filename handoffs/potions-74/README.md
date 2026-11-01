# #74 Health potions: drink with Q, buy at Vesna

By `adjustedfilm (Claude)` (i5 core), 2026-11-01. Rules from vice master's decision on the card: hotkey **Q**, heals
**35 % of max HP over 3 s**, **8 s** cooldown, **60 gold** at Vesna. Asset: laptop2's Health Potion (#150), icon
`T_Item_Potion_Health`.

## What the player gets
- **A potion slot** left of the HP bar: the potion icon (greyed out when you have none), `xN`, a small `Q`, and a dark
  curtain that drops while the cooldown runs. You start with one potion.
- **Q** drinks one (if you're hurt, alive and off cooldown): a gulp sound, then HP climbs over 3 s. It uses game time, so
  nothing moves while the game is paused. It never heals past full and doesn't work when dead.
- **In Vesna's shop** an APOTHECARY row: icon, `Health Potion`, `Q: heals 35% over 3 s`, the price (red when you can't
  pay) and `BUY [B]`. Click the row or press B: Gold -= 60, one more potion. Not enough gold: the fail sound.

## How it works
- New component **BPC_PotionBelt** on BP_ZombieHUD, event `DrawPotion(Hud)`, same pattern as #411's BPC_CastleScroll.
- Hero HP is `MaxHP - DamageTaken` on BP_ThirdPersonCharacter (#73), so the heal lowers `DamageTaken` each frame.
- Hook (3 nodes) chained right after #411's `CsHookDraw` in DrawHUD (or after `UX_CallFunction_23` if #411 isn't in).
- Shop open = `MPC_SkillTree` `Shop.R > 0.5` and the game paused (the same test BPC_VesnaTrade uses).
- Tuning on BPC_PotionBelt's Class Defaults: MaxHP 100, HealPct 0.35, HealDur 3, Cooldown 8, Price 60, Potions 1 (start),
  PanelX 40 / PanelY 905 (the shop row, 1080p units: move it if it overlaps Vesna's frame).
- v1 limits: potion count isn't saved across sessions yet.

## Steps
1. `py ".../potions-74/setup_potion74_ue.py" --dry-run`, then without: icon, component + defaults, backup
   **BP_ZombieHUD_BACKUP74**, adds `PotionBelt` to BP_ZombieHUD.
2. Paste `build/BPC_PotionBelt_graph.txt` (240 nodes) into BPC_PotionBelt's EventGraph, compile, save.
3. Paste `build/ZombieHUD_PotionHook_graph.txt` into BP_ZombieHUD, then `py ".../rewire_hook74_ue.py"` (wires, compiles,
   saves). `--revert` takes it out again.
Regenerate: `python gen_potion74.py` (uses #411's generator preamble).

## Checks (Play)
1. The slot shows `x1` left of the HP bar. Take a hit, press Q: HP rises over 3 s, the curtain drops for 8 s, `x0`, icon greys.
2. Q at full HP or during cooldown: nothing happens.
3. Open Vesna: the APOTHECARY row; with 60+ gold, click or B: gold -60, `x1`. With less: red price, fail sound.
