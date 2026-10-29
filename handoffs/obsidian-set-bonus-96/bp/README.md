# #96 Blueprint pastes: BPC_ObsidianSet + hero damage

By `hossam gmail laptop2 (Claude)`, 2026-10-29. Built against the 10-28 exports in `handoffs/exports/laptop2/set96/`.
`gen96.py` generates both paste files with the Master's node kit (`tools/master/t81/kit.py`, the same one #81 used).
The wiring check found 0 problems. **Not compiled yet**: that needs the editor.

**Decision:** all set and shield state lives in **one new component on the hero**, not in the HUD graphs. BP_ArmoryHUD is
2,489 nodes and BP_ZombieHUD and BP_SkillTreeHUD are bigger still, so the HUD only calls 4 events and reads 2 numbers.

## What the component does

| Event | Use |
|---|---|
| `BuyPiece(Id 10..20)` | after a set piece is paid for: owned bit on, purchase count +1 |
| `SetPieceWorn(Id, Worn)` | whenever a set piece goes on or off |
| `BuyShield()` | shield buy (LV1) or upgrade (LV2..4) |
| `LoadState(Owned, Worn, Bought, ShieldLvl)` | from the save (the masks of SPEC 5). The completion burst doesn't replay |
| `PushZombies(Radius, Damage, Push)` | used by the shockwave and the LV4 block |

It also keeps itself up to date, and the HUD reads two of its numbers:
- **`NextPrice`**: the price of the next set piece, `round50(450 x ObsPriceMul^bought)` = 450, 650, 950 … 18,500, then 0.
- **`NextShieldPrice`**: 600 / 800 / 1400 / 2400, then 0 = MAX.
- **`WornCount`**: for the `OBSIDIAN SET 7/11` line.
- It writes MPC **ObsSet** = (complete, completion time, last shockwave, worn count) and **Shield** = (level, last block time).

**Ember shockwave** (bound to the hero's OnTakeAnyDamage): when the set is complete and 12 s have passed since the
last one, every BP_Zombie within 4 m takes 40 damage and is launched 9 m/s away. Tune it with ShockDamage,
ShockRadius and ShockCooldown on the component.

**Hero damage** (the second paste): it replaces `Damage x (1 - Gear.R x 0.25)` with
`... x (1 - Armor.R x 0.35) x (1 - ObsSet.R x 0.15) x Block`.
- The Obsidian cuirass's -35 % (#52) wasn't in the damage yet. **Decision:** it goes in here. Drop that factor if you
  added it somewhere else.
- Block = 0.4 when the shield blocks. The chance is 20 / 30 / 40 / 50 % at LV1..4. A block writes Shield.G (rune
  flash and dome), and at LV4 it also pushes zombies within 1.5 m back.

Not in here yet: **knockback immunity** for the complete set. Whatever launches the hero would have to check
`ObsSet.R`, and that's not in these exports.

## Steps (editor driver)

1. **Create:** run `py ".../handoffs/obsidian-set-bonus-96/bp/create_bpc_obsidianset.py"`. It makes
   `/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet` with 13 variables and defaults, adds it to
   BP_ThirdPersonCharacter as `ObsidianSet`, and adds the hero bool `ObsBlocked`. If your build has no
   `add_member_variable`, add the variables by hand from the `VARS` table in the script.
2. **Component graph:** open BPC_ObsidianSet's EventGraph, paste `BPC_ObsidianSet_graph.txt`, then compile and save.
3. **Hero graph:** open BP_ThirdPersonCharacter, go to Event AnyDamage and paste `Hero_ObsidianDamage_graph.txt`. Then
   rewire 4 links (the names are from the export):
   - `Get Vector Parameter Value (Gear)`.then -> **ObsIn** (the 1-pin Sequence at the left of the paste).
   - **ObsOut**.then_0 -> the `Branch (IsDead)` it used to go to.
   - The old `Damage x (1 - Gear.R x 0.25)` Multiply's result -> **ObsDmg**.A.
   - **ObsDmg**.ReturnValue -> `DamageTaken + …`.B.
   - Then compile and save.
4. **Shield VFX** (#117 hand-off):
   - Set M_BulwarkRune as the Overlay Material on the shield mesh.
   - Attach an `/Engine/BasicShapes/Sphere` to the shield with M_BulwarkDome: scale 3, no collision, no shadow, always
     visible. It's invisible except for 0.3 s after an LV4 block.
5. **HUD hooks** (BP_ArmoryHUD, Vesna trade). Get Player Character -> Cast to BP_ThirdPersonCharacter -> ObsidianSet:
   - Set piece **price** = `NextPrice`. On a paid BUY: subtract `NextPrice` from Gold first, then call `BuyPiece(Id)`.
   - Every equip or unequip of a set piece -> `SetPieceWorn(Id, Worn)`. The cuirass (id 10) is the one that exists today.
   - Shield: BUY/UPGRADE shows `NextShieldPrice` and calls `BuyShield()`. MAX when it's 0.
   - Save: store ObsOwned / ObsWorn / ObsBought / ShieldLevel. Load: call `LoadState(...)` once.

## Checks

Use `test_obsidianset.py` in Play. Set `STEP` at the top and run it once per step. It prints the variables and the
MPC values.

1. `prices`: NextPrice goes 650, 950, 1350, 2000, 2900, 4200, 6050, 8800, 12750, 18500, then 0 (450 was before the
   first buy).
2. `full`: ObsSet.R = 1 and WornCount 11, and G doesn't change (no burst on load).
   - `off`: R = 0, 10 worn.
   - `on`: R = 1 and G = now (the burst plays).
3. `hit`: ObsSet.B = now, and nearby zombies take 40 damage and fly back. Run `hit` again at once: nothing happens
   (cooldown).
4. `shield`: ShieldLevel goes 1, 2, 3, 4, 4. NextShieldPrice goes 800, 1400, 2400, 0, 0.
5. In play with a level-4 shield: some hits do 40 % damage, the rune flashes, and the dome pops.
