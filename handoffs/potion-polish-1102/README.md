# Potion polish (i9, 2026-11-02, Alien's request): APPLIED + Play-verified

Replaces #74's slot drawing in `BPC_PotionBelt` (the BP_ZombieHUD hook is unchanged). Same rules: Q, 35% over 3 s, 8 s cooldown, 60 gold.

## What changed
- **Slot:** a round `M_UI_PotionBadge` (gold bevel ring, potion icon) in line with the Dash and Berserk badges, left of the HP bar. Gold Q key cap top-left, `xN` bottom-right.
- **Cooldown:** a clockwise sweep with a gold edge (replaces the dark curtain). Empty = desaturated icon and dimmer ring.
- **Refuse:** Q when it can't drink → fail sound, red ring flash, short shake.
- **Healing:** green pulsing halo + a soft green glow on the HP bar.
- **Low HP:** below 30% with a potion ready, the halo pulses gold.
- **Q hint (motion graphic):** the first time HP drops below 50% with a potion, an ornate plate rises out of the badge: an animated Q cap + "Drink a Healing Potion / Restores 35% health over 3 s". It holds ~4 s, then fades. It repeats once at 30% (10 s later) unless a potion was drunk. Drinking ends hints for good.
- **BUG FIX (from #74):** the heal never ran. `LastT` was written before the pure `dt` was read, so `dt` was always 0 and `HealLeft` stayed stuck. `LastT` is now written after the heal.

## Files
- `setup_potion_polish_ue.py`: builds the material and adds 8 variables to BPC_PotionBelt. Done.
- `gen_potion_polish.py` → `build/BPC_PotionBelt_polish_graph.txt`: 479 nodes. fix_impure: no changes. applyall check: OK.
- Backup: `Tools/PasteRegen_1027/backup_1102/BPC_PotionBelt_before_polish.uasset` (5.3 Tools folder).

## Verified in Play
Hint shows at <50% HP. Q drinks (x0, sweep, green glow). Q in cooldown = red refuse. HealLeft drains to 0. No potion runtime errors.

## Paste gotchas (5.8)
- Delete the old graph with **Delete**; BackSpace does nothing in 5.8.
- After a delete, the old nodes stay in memory under their names, so a re-paste gets `K2Node_*` names. Count nodes in the exported `Nodes()` list, not with ObjectIterator.

## Not done
- The hero regenerates HP very fast (~20 HP/s in Play), which makes potions nearly pointless. That's a balance call for Alien.
