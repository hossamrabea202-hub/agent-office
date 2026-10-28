# #66 Bag + skill book pickup reveals: design

From checkking (Claude), 2026-10-28. Same visual language as the map-pickup unlock (minimap animates in): animated reveal, gold frame, Cinzel text, no default fonts. Short, skippable, once per pickup.

## Sequence (both pickups), seconds from pickup

| t | What happens |
|---|---|
| 0.0-0.6 | Item icon (bag / book) flies from the pickup point on screen to the panel's anchor, scaling 0.6 → 1.15 → 1.0, white-hot glow cooling to gold (same curve as the map unlock). |
| 0.4-1.2 | The unlocked HUD part animates in where it lives: **bag** → the pack panel slides open and the torso slot pulses gold twice; **book** → the skill bar slots 1-3 pop in left to right (0.12 s apart) and the T badge pulses. |
| 0.8-1.6 | Hint card frame draws on from the top centre outwards in both directions (gold line with a bright spark at each head); corner diamonds light as the line passes. |
| 1.2-2.4 | Hint lines fade + slide in, 0.25 s apart; a gold shimmer sweeps across the card once. |
| hold | 7 s, or until the player presses the key it teaches (I / T), or **Esc / any click = skip**. |
| out | 0.5 s fade, card shrinks 4 % toward the icon. |

Never during a wave fight: if a wave is active, the hint card waits until the wave ends (the icon fly-in and unlock still play at once).

## Copy (Cinzel, title in gold caps, keys in a gold key cap like the H MORE CONTROLS button)

**Bag, title: THE SATCHEL**
- **[I]** Open your pack
- Click an item, then a slot to equip it. Armour goes in the **torso** slot.
- Sell loot and buy gear at **Vesna's** market.

**Skill book, title: THE BOOK OF SKILLS**
- **[T]** Open the skill tree
- Every level grants a **skill point**.
- Spend points to unlock a skill, then rank it up.
- **[1] [2] [3]** Cast your skills.

## Once only

A HUD bool per pickup, `HintBagSeen` / `HintBookSeen`, set when the card closes (by timeout, key or skip) and saved with the rest of the HUD state in the existing save/load (F9, wave autosave, F10; same path as `CastleSaveArmory`). Load with a seen flag = no card. Picking the item up again (new game) = card again.

## Assets

- `M_HintCard` (UI domain, translucent), built by `make_M_HintCard.py`: obsidian panel, gold double frame drawn on by `Age`, corner diamonds, shimmer sweep, `Fade` for the out. The HUD draws it with DrawMaterial at the card rect, sets `Age` = time since the card started and `Aspect` = width / height, then draws the Cinzel text on top.
- Icons: the existing bag / book item textures (the ones the pack uses), so nothing new to import.
- Wiring (DrawHUD, timers, flags, save): a paste built on the requested BP_MinimapHUD export, so it matches how the map unlock is drawn.
