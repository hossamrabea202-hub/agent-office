# #96 Obsidian Sovereign: full-set bonus, escalating prices, shield as its own item

Seat: `hossam gmail laptop2 (Claude)` · card #96 · builds on `handoffs/vesna-obsidian-shop/README.md` (#52 shop spec).
Status: **spec + price table + set-aura material script ready.** The HUD and hero graph pastes need fresh exports
(no blind pastes): BP_ZombieHUD (item vectors), BP_QueueHUD (equip rules), BP_SkillTreeHUD (Vesna trade, only the
trade functions), BP_ThirdPersonCharacter (ReceiveAnyDamage), and the armoury save slot.

## 1. The set

11 pieces, one item id each. The ids continue after the Obsidian cuirass (id 10, #52):

| id | Piece | Slot | Own stats (worn) | Art |
|---|---|---|---|---|
| 10 | Cuirass (chest) | torso | DEF +45, damage taken -35 % (#52) | AAA, in game |
| 11 | Pauldrons (shoulders L/R) | shoulders | DEF +12 | AAA, ready to import |
| 12 | Gauntlets L/R | hands | DEF +8, attack speed +5 % | AAA, ready to import |
| 13 | Sabatons (boots L/R) | feet | DEF +8, move speed +5 % | AAA, hand-off #98 |
| 14 | Greaves (shins L/R) | shins | DEF +10 | AAA, hand-off #99 |
| 15 | Helmet | head | DEF +15 | to build (checkking) |
| 16 | Rerebraces + couters (upper arms) | upper arms | DEF +8 | to build |
| 17 | Vambraces (forearms) | forearms | DEF +8 | to build |
| 18 | Fauld + tassets (waist) | waist | DEF +10 | to build |
| 19 | Cuisses + poleyns (thighs) | thighs | DEF +12 | to build |
| 20 | Cape | back | DEF +4, rain/cold immunity look only | to build |

Pair pieces (L/R) are **one item**: buying the boots gives both boots.

**Decision:** pieces without art aren't sold yet. Vesna shows only pieces whose meshes are imported, so the set can't
complete until all 11 exist. Until then the set bonus can be tested with the debug command in section 6.

## 2. Set bonus: "Sovereign's Ember" (all 11 worn)

**Perk (Decision):**
- **Damage taken -15 %** on top of the pieces' own stats (multiply, don't add: `dmg * (1 - piece terms) * 0.85`).
- **Knockback / stagger immunity** while the set is complete.
- **Ember shockwave:** taking a hit while the shockwave is ready releases a ring of embers. It deals 40 damage and
  knockback to zombies within 4 m, then recharges for 12 s. It's the set's "reaction on hit".

**VFX (one overlay material on every piece, `make_M_ObsidianSetAura.py`):**
- Always on while complete: small dark-gold embers crawl up the plates, and a slow gold rim pulse (0.5 Hz).
- Completion: a 0.8 s white-gold flash over the whole set when the last piece goes on.
- On hit / shockwave: a 0.25 s red-gold flare. Optionally add a Niagara ring at the feet (reuse the soldier level-up
  burst from #2 tinted gold) for the shockwave.
- Removing any piece: everything turns off at once (R = 0).

**Driver: MPC vector `ObsSet`** (the script adds it to the MPC that holds `Armor`):

| Channel | Meaning | Written by |
|---|---|---|
| R | 1 = all 11 worn, else 0 | HUD, every frame, next to where Armor.R / Gear.R are written |
| G | game time (s) the set completed | HUD, on the frame R goes 0 -> 1 |
| B | game time (s) of the last shockwave | hero, when the shockwave fires |
| A | pieces worn (0..11), for the HUD set counter | HUD, every frame |

Use **Get Game Time in Seconds**: it is the clock the material Time node uses, so the burst and flare line up.

**HUD:** the inventory shows `OBSIDIAN SET 7/11` under the torso slot. At 11/11 it turns gold and reads
`SOVEREIGN'S EMBER`, with a one-line perk summary.

## 3. Escalating prices at Vesna

The price depends on **how many set pieces the player has bought so far**, not on which piece:

`price(n) = round50(450 * 1.45^n)`, where n = set pieces bought before this one (0..10).

| Purchase # | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gold | 450 | 650 | 950 | 1350 | 2000 | 2900 | 4200 | 6050 | 8800 | 12750 | 18500 |

Full set: 58,600 gold. **Decision:** ×1.45, not the card's example ×1.6. Today's shop items cost 120-450 and a commander
costs 300, so ×1.6 would make the 11th piece cost 49,500 (131,200 for the set), which looks out of reach. One constant
(`ObsPriceMul`) tunes it; the table for ×1.35 / ×1.6 is in `prices.csv`.

- Every set piece in the carousel shows **the same next price** (it's the count that matters), with the line
  `SET PIECE 4/11 · next piece costs more`.
- The cuirass (#52) is set piece #1 if bought first: its fixed 450 becomes `price(n)`.
- Selling back (if the shop ever does it) refunds 50 % of what was paid and does **not** lower the count.

## 4. Hand shield: its own item (not in the set)

- Item id 30, slot **off-hand**. It doesn't count toward the set and isn't needed for the bonus.
- Bought once at Vesna for **600 gold**, then **UPGRADE** like the crossbow (#52): LV2 800, LV3 1400, LV4 2400.
  The levels give block chance 20 / 30 / 40 / 50 % for 60 % less damage on a blocked hit.
- **Own VFX speciality, "Bulwark Rune":** the shield's face carries a rune that glows brighter per level. At LV4, a
  block flashes a gold hex dome for 0.3 s and pushes zombies 1.5 m back. Driver: MPC vector `Shield` (R = level,
  G = last block time). It needs a shield mesh first (art card to file; it fits checkking's Obsidian style but isn't
  part of the set).
- **Built (laptop2, 2026-10-29):** `make_M_BulwarkRune.py` makes `M_BulwarkRune` (Overlay Material on SM_ObsidianSovereign_Shield) and `M_BulwarkDome` (on a sphere, ~1.5 m, shown 0.3 s on an LV4 block), plus MPC vector `Shield`. Preview `preview_bulwark_rune.png` (LV1, 2, 3, 4, block). BP: on buy/upgrade set Shield.R = level; on block set Shield.G = Get Game Time in Seconds. If the rune shows on the back, set `FaceY` = -1 in the material.

## 5. Save and load

The armoury save slot gets:
- `ObsOwned` (int bitmask, bit i = item id 10+i owned) and `ObsWorn` (bitmask), replacing the single ObsV owned/worn.
- `ObsBought` (int 0..11): the purchase count for the price curve.
- `ShieldLevel` (0 = not owned, 1..4).
- On load: rebuild the item cells from the masks, write ObsSet.R/A at once, and **don't** replay the completion burst
  (set G = -100 on load).

## 6. Checks for the editor driver

1. Run `make_M_ObsidianSetAura.py`. The Output Log shows the MPC path and "M_ObsidianSetAura built".
2. Set `M_ObsidianSetAura` as the **Overlay Material** on every Obsidian set mesh component of the hero.
3. Debug: set ObsSet = (1, now, -100, 11) from the console or a key. Embers and the rim show, and the burst plays once.
   Set R = 0: everything goes dark.
4. Buy pieces in any order at Vesna: 450, 650, 950 … The price shown is the same on every set piece.
5. With 10/11 worn: no embers, no perk. Put the 11th on: burst, embers, -15 %, shockwave on the next hit.
   Take one off: everything turns off.
6. Shield: buy, equip and upgrade it on its own. The set status doesn't change.
7. Save, quit, load: pieces, worn state, price count and shield level all come back, and the burst does **not** replay.
