# #472 fix F: wires that were never made (i5 for i9). Scripts, no paste, independent of fixes A to E

`handoffs/aaa-472/t3d_orphans.js` scanned 193 project Blueprints for impure nodes with no exec input. **Proven on i5 with a micro-test:** such a node returns None at runtime, and the Blueprint still compiles with only a warning. So these have been silently broken.

**Important:** found on i5's copies, except BP_BattleDirector and BPC_ShieldKit, which I confirmed in your 11-03 exports. If you already fixed one, the link is simply remade; if a node is gone, the dry run stops and changes nothing.

**Tested:** every script on a temporary copy, links only: all made, 0 failures. **Not compiled, not played.**

## Run each (dry run first). Any order, one Blueprint each
`py handoffs/aaa-472/ops/graph_ops_ue.py <repo>/handoffs/aaa-472/ops/ops_F_<name>.json --dry-run`, then `--apply`. Must print `compile True | link/value failures [] | new errors []`, then `saved True`.

| name | Blueprint | What was broken | After the fix |
|---|---|---|---|
| `gore` | BPC_Gore337 | sword cuts spawned a severed limb but never hid the limb on the zombie, no wound cap, no blood burst, not recorded as severed | limb comes off for real, with cap and blood |
| `director` | BP_BattleDirector | the WallBreaker's Target was always empty | it heads for its breach spot |
| `upgrades` | BPC_CastleUpgrades | "does a save exist" was never run, so **saved castle upgrades never loaded**; the shop offer notice never showed | upgrades load, notice shows |
| `shieldkit` | BPC_ShieldKit | same: **saved shields never loaded** | shields load |
| `halfhorse` | BP_HalfHorseZombie | BeginPlay stopped early: no capsule size, torso not attached, bones not hidden, HP 400 / XP / damage / start anim never set | built as designed |
| `barracks` | BP_BarracksHUD | the recruit bar read the barracks NPC's location from an empty value | bar sits over the NPC |
| `risen` | BP_RisenDirector | the rest-notice text was never shown | notice shows |
| `flares`, `medics` | BPC_Flares, BPC_Medics | shop offer notice never showed | notice shows |
| `hero` | BP_ThirdPersonCharacter | BurnThink read BurnEnd[0] with no working guard (Blueprint's AND does not short-circuit): log error whenever it ticks with nothing burning | no error |

## Test list (Play)
- [ ] **Sword-cut limbs (gore):** the arm is gone from the zombie, the severed one falls, a wound cap shows, blood bursts. Not too gory for Alien (#337).
- [ ] **WallBreaker:** walks to a breach spot and works on it. It has never had a target, so its behaviour is new: **watch its balance**.
- [ ] **Half-horse:** looks right (torso on horse), has 400 HP, attacks. Never ran this code either: may need tuning, tell TGA.
- [ ] **Upgrades + shields:** buy one, quit, reload: it is still there. A NEW game with an old save slot now loads the old state: delete `CastleSaveCastle` and `ShieldKit` for a clean start.
- [ ] Barracks bar over the NPC; shop notices appear once when you walk near, not repeating.
- [ ] Log: no new `Accessed None`; BurnEnd index error gone.

## Revert
`Saved/bak472/<name>.uasset.fixF`: close the editor, copy back over Content/... (drop `.fixF`), reopen.

## Decisions
- **Decision: fixed only where the intent is clear** from the names, numbering and a dangling wire next to the cut node.
- **Decision: left alone, may be deliberate or replaced:** BP_Crossbow's old casts (newer CX_ versions sit next to them), the hero's landing DisableInput chain (CX_12) and fire light cast (sfAsLight7), BP_ZombieHUD and BP_SkillTreeHUD cut draws (HUD belongs to #458), BP_TorchBearer (its T3D is hard to read; needs a closer look).
- **Decision: not touched:** the other "literal index next to AND" reads in BPC_Quests, BP_Forge, BPC_CastleUpgrades, BPC_ObsidianSet: their arrays look fixed-size, so they should not fire. A Play log will show if any do.
