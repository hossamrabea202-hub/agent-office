Title: Bug: hero cape renders flat white; soldier capes come loose (lying on the ground, standing by the cart)

Owner report (2026-10-28), Play screenshot in the courtyard by the cart, "Command the swordsman" prompt up:

> what is this light with soldiers

**What the screenshot shows**
- The hero's cape is a flat white, unlit shape behind him with the crest readable through it (looks like an emissive/untextured fallback, not the red cloth).
- A red soldier cape lies flat on the cobbles under the swordsman's feet, and another red cape stands on its own next to the cart wheel, with no soldier in it.

**Master's finding (16:30):** there is no cape component on the hero or on BP_SoldierSword/BP_SoldierXbow: the cape is part of `ShadowknightUE_SK` (material slot 2, `MI_Hero_Cloth_Royal` / `M_HeroCloth_AAA`), so it cannot detach. The cloth material is not dirty. The white hero cape with the crest showing and the red cape-shaped glows on the ground / by the cart therefore look like an **overlay or highlight material applied to the cloth slot** (the E 'Command the swordsman' target highlight, an aura, or the level-up FX) rendering on the cape section only, possibly left behind when the soldier moves. Reproduce in Play with the order wheel open and check Overlay Material / custom depth on the soldier meshes first.

**Suspects**
1. `M_HeroArmor_AAA` (and 14 other materials) were left dirty/unsaved in the editor by an earlier session; the cape material may be mid-edit, uncompiled or broken. Save or revert it, then re-check in Play.
2. Cloth / attachment on the soldier capes: the cape mesh detaches from the body (leader pose / attachment lost on recruit, order change or level-up FX #33), or the cloth sim explodes. Related: #67 hero cape clipping, #84 cape over emblem, #97 Codex source collection.
3. Capes left behind by despawned/recycled soldiers (pooling) are not destroyed with the soldier.

**Done when:** in Play, the hero cape is red cloth with the crest, every soldier cape stays on its soldier through recruit, orders, fights and death, and no cape is ever left on the ground on its own.

---
Priority: high
Pinned from the owner via hossam gmail (Claude), Master Agent. Agents: comment "Claimed by <your name>" to take it, close the issue when done.
