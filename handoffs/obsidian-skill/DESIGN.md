# Obsidian complete-set as an activatable skill: design (read-only study, nothing built)

Paths are under `handoffs/`. SET = `exports/adjustedfilm/faults-1205/BPC_ObsidianSet.t3d.txt`, GEN = `gothic-set-453/wiring/gen_set_v4.py`,
HUD = `exports/adjustedfilm/skilltree-err/BP_SkillTreeHUD_EventGraph.txt`, ARM = `exports/adjustedfilm/faults-1205/BP_ArmoryHUD.t3d.txt`. Each claim is FOUND or GUESS.

## 1. What the complete set does today
- FOUND: "Complete" = `Tier == 4` = 4/4 Obsidian bundles worn (GEN:389). The live graph is v3: SET has 0 `GothicCount` hits. The player pays only the bundle prices; firing costs nothing.
- FOUND, always-on (passive):
  - DR -15 %: `ObsSet.R = DR / 0.15` (`oSetObsSet414`, SET:5863), and the hero multiplies damage by `1 - ObsSet.R x 0.15` (`obsidian-set-v2/README.md:40`).
  - Embers and gold rim from `M_ObsidianSetAura`, on at `R >= 0.5`, so already at tier 3 (`obsidian-set-v2/README.md:41`). Visual only.
- FOUND, one-shot on equip, **no gameplay effect**: the "burst" is only a 0.8 s material flash. Trigger is the 0->1 edge in `Refresh`: `complete AND NOT WasComplete` sets `ObsSet.G = now` (GEN:403-407; `oSetWasComplete415`, SET:5876; `make_M_ObsidianSetAura.py:71,91`). `LoadState` presets `WasComplete` so a load doesn't replay it (`oSetWasComplete170`, SET:3333).
- FOUND, automatic on hit, the only real "attack":
  - Event `OnOwnerHit` (SET:6351), bound to the owner's damage delegate by `Bind` (SET:1517; OnTakeAnyDamage per `obsidian-set-bonus-96/bp/README.md:26`).
  - `oIfShock469` (SET:6427): `Tier >= 3 AND now >= ShockReadyAt`.
  - Then `ShockReadyAt = now + ShockCooldown x (Tier >= 4 ? 0.75 : 1)` and `PushZombies(ShockRadius, ShockDamage, 900)` (SET:6587), and `ObsSet.B = now` (red-gold flare, `oSetObsSet483`, SET:6574).
  - Values: 40 damage, 400 cm, 12 s, so 9 s at 4/4 (`faults-1205/set_cdo_master.json`).
- FOUND: so 4/4 only adds 5 % DR, the flash and a 3 s faster shock over tier 3. There is no separate complete-set power to "activate"; the shockwave is the natural candidate.

## 2. How existing skills are wired (there is no single system)
| Skill | Key (literal on the pin) | Owner | Cooldown state | Icon / sweep |
|---|---|---|---|---|
| Whirlwind / QuakeSlam / Fissure (sword) | One / Two / Three, HUD:1822, 2107, 2392 | BP_SkillTreeHUD DrawHUD | MPC_SkillTree `Cd` R/G/B = end time; 7 / 10 / 12 s minus an MPC value (HUD:2001, 2286, 2571) | `Cd1..3` scalars (HUD:1782, 2067, 2352) drawn by `M_UI_ST_Cooldown1..3` (HUD:29932, 32550, 35126) |
| BlastBolt / ChargedShot (crossbow) | One / Two, HUD:58137, 58296 | same | MPC `CdX` R/G; 8 / 10 s (HUD:58241, 58400) | same materials; `SelectFloat` picks the value |
| Auras | Four / Five / Six (BP_HeroAuras.uasset name table) | BP_HeroAuras | MPC_HeroAbilities `AuraT_X = OnUntil, CdUntil, Dur, Cd` (`master-handover/MASTER_HANDOVER.md:88`) | `MI_UI_ST_AuraSlot4..6` (HUD:59715, 60962, 62209) |
| Dash | LeftShift | BP_HeroAbilities Tick | MPC `DashCd = now + 3` (`exports/checkking/skills/BP_HeroAbilities.t3d:37,59`, Oct 27) | badge |
| Berserk | **none**: auto at `DamageTaken >= 85` | BP_HeroAbilities Tick | `BerserkCd = now + 60` (same file :71,81) | badge |
| Potion | Q | BPC_PotionBelt `DrawPotion(Hud)` | var `CoolUntil` | `M_UI_PotionBadge` MID sweep (`potion-polish-1102/gen_potion_polish.py:62,100,105,187`) |

- FOUND, activation pattern in every case: per-frame `WasInputKeyJustPressed` AND a gate (unlocked, `now >= end`, not dead, not paused), then spawn or effect, then write end time. No Input Actions are involved. Conditions: `CX_175` HUD:1933, `CX_4988` HUD:58217.
- GUESS: the MPC value subtracted from the cooldown is the skill rank. `HasMappingContext` (HUD:57090) selects sword vs crossbow.
- **Keys are NOT assignable. No rebinding system exists.** FOUND:
  - Every key above is a hard-coded pin default.
  - `Config/DefaultInput.ini` has no action or axis mappings.
  - IMC_Default / Crossbow / Cannon cover only movement, crossbow and cannon. The only `PlayerMappable*` strings are engine property names in those IMC assets; no asset uses a remap or key-selector.
  - BP_ControlsHUD is a help panel toggled with H (`exports/master/2026-10-30b/BP_ControlsHUD_EventGraph.txt` polls only H and the mouse).
- FOUND, taken keys: 1-6, Q, E, T, H, P, R, F (cannon), B and A/D (menus), Shift, Space, WASD, Esc. `Seven`, `Eight`, `Nine`, `Zero` appear in no BP/BPC/IMC under Gameplay (name-table scan, backups excluded).

## 3. Smallest design: skill "Sovereign's Ember", all in BPC_ObsidianSet
**Effect.** At 4/4 the on-hit auto shock stops. The key fires a stronger shockwave. DR -15 % and the embers stay passive, so Vesna's "SOVEREIGN'S EMBER -15%" text stays true (`exports/adjustedfilm/gothic-453/BPC_VesnaTrade.decomp.txt:406`) and needs no paste. Tier 3 keeps its on-hit shock.

**Defaults (GUESS, tune on class defaults).** Instant, duration 0. Cooldown **15 s**, damage **80**, radius **600**, push 900. Why: 80/15 = 5.3 dmg/s against today's maximum 40/9 = 4.4, a small reward for pressing. 15 s sits above Fissure (12 s) and far below Berserk (60 s).

**No HUD paste needed.** FOUND: BP_ArmoryHUD already calls `DrawArmoury(Hud, SizeX, SizeY)` every DrawHUD (`ohHookDraw6`, ARM:33146), skipped only while VesnaTrade `Covering` (`TradeObsIfC`, ARM:5023). The game HUD is BP_NoticeHUD, which calls its parent's DrawHUD (BP_ThirdPersonGameMode.uasset; `faults-1205/BP_NoticeHUD.t3d.txt:5`).

**New variables** (setup script like `gothic-set-453/wiring/setup_gothic_ue.py`; none marked SaveGame):
| Name | Type | Default |
|---|---|---|
| EmberKey | Key | Seven |
| EmberCooldown / EmberDamage / EmberRadius | double | 15 / 80 / 600 |
| EmberMat | MaterialInterface | M_UI_PotionBadge |
| EmberMID | MaterialInstanceDynamic | none (created once) |
| EmberIcon | Texture2D | new icon |
| EmberRefuseAt | double | -100 |

Reuse `ShockReadyAt` as the ready time. Taking a bundle off then cannot dodge the cooldown through the tier-3 shock.

**Graph changes:**
1. `oIfShock469` condition becomes `Tier == 3 AND ready`. The 0.75 select goes dead; leave it.
2. `DrawArmoury` starts with a Sequence: `then_0` = new event `DrawEmberSkill(Hud, SizeX, SizeY)`, `then_1` = existing body.
3. `DrawEmberSkill`: if `Tier != 4`, or paused, or `Shop.R > 0.5`: return (no icon).
   - `WasInputKeyJustPressed(EmberKey)` on GetPlayerController, with the key pin wired from the variable.
   - Ready and hero not `IsDead` (hero cast as in the potion gen, lines 33-37): `ShockReadyAt = now + EmberCooldown`, `PushZombies(EmberRadius, EmberDamage, 900)`, `ObsSet = (R, now, now, A)` (flash + flare). `Refresh` keeps G when not "just" completed (GEN:404), so the write survives.
   - Not ready: `EmberRefuseAt = now`, fail sound, red ring (potion pattern).
   - Draw: MID badge with sweep `clamp((ShockReadyAt - now) / EmberCooldown)` (gen_potion_polish.py:187; params `Icon`, `Pot`, `Pot2`, `setup_potion_polish_ue.py:78-82`) and key cap text from `Key_GetDisplayName(EmberKey)`.
   - Ignores `IsAttacking`, so it works as an emergency button mid-swing. GUESS: this is the wanted feel.

**Set stops being complete.** The next `Refresh` (0.5 s timer or event) lowers `Tier`. FOUND: the icon and key turn off and the tier-3 on-hit shock returns, using the same `ShockReadyAt`. Re-completing plays the flash as today.

**Save impact: none.** FOUND: the slot `CastleSaveObsidian` stores `Data = [ObsOwned, ObsWorn, ObsBought, ShieldLevel]` (GEN:486-503). The new variables stay out of it, and cooldown is a runtime game-time value, ready again after a load.

**Assignable key, in 2 steps:**
- Step A (this design): `EmberKey` is a variable, so it changes in one place, with the cap label following. This does NOT let the player rebind.
- Step B (needs owner's OK, ~60 nodes): "press a key" capture. While a `Rebinding` bool is on, loop `EmberKeyChoices` (Key array of free keys only; Blueprint has no any-key event, GUESS) with `WasInputKeyJustPressed`. Persist the index in a **new** slot `CastleSaveObsidianKey` (same BP_CastleSave class, `Data = [index]`), leaving the existing slot untouched. Trigger: a button in Vesna's tier box means a BPC_VesnaTrade paste; a click on the badge needs a visible cursor. Prefer a [REBIND] row in the old armoury panel inside `DrawArmoury`, if it still shows (GUESS: `Covering` may hide it, so check first).

**Still missing before a paste:**
- BP exports: **none block.** SET and ARM are fresh; the potion cast covers the hero's `IsDead`. Re-export SET right before pasting if anyone changed it.
- One 1080p Play screenshot with 4/4 worn, to place the badge. GUESS: next free slot `X = 0.546 x W`, `Y = 0.929 x H` (auras step 0.08 at .306 / .386 / .466, HUD:59715 ff.); that export is from Nov 2, and potion/Dash badges are elsewhere.
- Icon: no ember skill texture found. Derive from `obsidian-bundles-424/gen/make_bundle_icons.py`, or reuse a bundle icon first.

## 4. Risks and open questions (recommended default in bold)
- **What does the owner mean by "the effect"?** Shockwave vs the -15 % DR vs the visual aura. **Shockwave only; confirm with the owner before building.** Making DR a timed buff means changing Vesna text and weakens armour already sold.
- **Should tier 3 keep the auto shock?** Otherwise tier 3 has no shock, and Vesna's "-10% + EMBER SHOCKWAVE" is wrong. **Keep it.** Side effect: 4/4 loses passive reaction but gains the button, so the numbers above must feel better.
- **v4 collision.** Whole-graph paste; v3 is live and v4 waits on meshes (`gothic-set-453/wiring/README.md`). **Write the skill as one shared patch imported by both gen_set_v3 and gen_set_v4;** ship on v3 now and v4 regenerates with it.
- **Which default key?** 7 is free but far from WASD. G/V/C/X/Z appear to be free but single letters can't be proven from name tables (they collide with pin names). **Seven, in the number row with the other skills**, then step B.
- **Own badge or a slot in the skill bar?** The bar lives in SkillTreeHUD with its own slide-in. **Own badge from the component**, matching the potion pattern. It won't animate with the bar; acceptable for v1.
- **Key pressed while the shop or a book is open.** Hook skipped when `Covering`; paused gate covers the rest. **No extra work.** Test Book of Skills (T).
- **`GetAllActorsOfClass(BP_Zombie)` on press** (GEN:465): already used per shock, and now only on a key press. **Fine.** Other enemy types (Brutes etc., if not BP_Zombie children) stay unhit, as today. GUESS on those classes.
- **Local project may lag the Master.** Local `BPC_ObsidianSet.uasset` is dated Nov 2 while the export is Nov 3. **Trust the Nov 3 export;** generate from it.
- **Play checklist:** 4/4 shows badge; 7 fires, sweep runs 15 s; 7 again refuses; getting hit no longer auto-fires; take off a bundle: badge gone, on-hit shock back, cooldown kept; save and reload: pieces same, no flash replay, old save slot loads.
