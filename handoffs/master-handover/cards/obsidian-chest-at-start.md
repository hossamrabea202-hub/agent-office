Title: Bug: new game starts with the hero wearing the Obsidian Sovereign chest

Owner report (2026-10-28), with a Play screenshot at WAVE 0, gold 0: the hero stands in the courtyard wearing the dark Obsidian Sovereign chest (arrow emblem) over the silver hero armour, nothing bought.

> why does game start with me wearing this?

**Expected:** a new game starts in the plain silver armour. The Obsidian chest only shows after buying it at Vesna and equipping it.

**Master's finding (16:25):** the swap itself is correct: `ObsidianChest` on the hero uses `MI_ObsidianSovereign_Chest_Hero` (ArmorMode -1, show only when worn) and `MPC_SkillTree Armor.R` is 0 in the editor. What turns it on at runtime is the **armoury save slot** `CastleSaveArmory.sav`: the HUD loads it on start and writes Armor.R = ObsV worn every frame, so a chest bought and equipped in an earlier session is still worn at wave 0. **Owner decision needed:** does the armoury carry over between games (meta-progression), or does Begin the Siege start fresh and only Continue load it?

**Original suspects**
1. `MPC_SkillTree Armor.R` is still at the Obsidian value in the editor: material parameter collections keep the last value set, so the swap survives into the next Play. Fix: reset it to 0 on BeginPlay of a new game (before the armoury load), and in the asset default. (`Tools\master\mpc_armor_check.py` reads/resets it.)
2. The armoury save slot (CastleSaveArmory) still has the chest marked owned/worn from a test: a New Game must ignore or clear it; only Continue loads it.
3. The Vesna shop hand-off (`handoffs/vesna-obsidian-shop`) left the worn flag defaulting to on.

**Done when:** starting a new game shows the silver armour; buying and equipping the Obsidian chest at Vesna swaps it in; Continue restores whatever was worn; Play twice in a row from the editor gives the same result.

---
Priority: high
Pinned from the owner via hossam gmail (Claude), Master Agent. Agents: comment "Claimed by <your name>" to take it, close the issue when done.
