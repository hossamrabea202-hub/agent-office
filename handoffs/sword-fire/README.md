# Sword fire — the blade burns near zombies, burning hits keep burning, the slash trail turns to fire

From: hossam gmail laptop2 (Claude), 2026-10-30 (owner: "i want it now"). This is the **fire element of #95** delivered on its
own, Blueprint-only; the gold-parts tiers and the element choice stay on #95.

**Look:** world-aligned flames rise off the blade's edges (fresnel), coloured by a heat ramp (deep red → orange → yellow →
white), plus a warm point light on the sword that lights the ground and the zombies. Zombies within 6 m → the blade heats up
over ~0.3 s; none → it cools. The sword's own material is **not** touched: the fire is an **Overlay Material** on the Sword
component (new material, new instance).

## Master steps (10 min)
1. Pull. In the editor Python console: `py "<repo>/handoffs/sword-fire/make_sword_fire_ue.py"`
   → `/Game/CastleDefender/VFX/SwordFire/`: 2 textures, `M_SwordFireOverlay`, `MI_SwordFire`.
2. Open `M_SwordFireOverlay`, drag the output of the node described **WPO_OUT** into *World Position Offset*, Apply, Save
   (Python cannot connect that pin). Skip this if you want flames flat on the blade.
3. `BP_ThirdPersonCharacter`: add the 10 variables in `VARIABLES.md`.
4. Paste `Hero_SwordFire_graph.txt` into the EventGraph (Validation OK, 88 nodes), then wire by hand (`manifest.json`
   lists the same ten wires; the applyall merge cannot run on the hero export because the whole-asset conversion
   drops the Enhanced Input / PlayMontage nodes):
   - **BeginPlay** (`K2Node_Event_1`) → pasted *CreateDynamicMaterialInstance* (`sfMakeFireMID2`), replacing its wire to
     the cast `K2Node_DynamicCast_0`; pasted *Set Timer* **BurnThink** → that cast node.
   - **Slash**: `CX_737` (Set Scalar "Intensity" on the slash) → pasted branch *IfHotSlash*, replacing its wire to `CX_728`
     (SetLifeSpan); the branch's False → `CX_728`; pasted *SlashHot* (Set Scalar) → `CX_728`.
     Data: `CX_721` Return Value (the slash MID) → the Target of both pasted *SlashEmber* and *SlashHot*;
     `CX_735` Return Value → pin A of the pasted Multiply next to SlashHot.
   - **Burn**: `K2Node_CallFunction_CH7` (the sword hit's Apply Damage, its exec out was free) → pasted branch *IfHotHit*;
     `K2Node_ComponentBoundEvent_CH0` Other Actor → the Object pin of the pasted cast *AsZombieHit*.
   Refresh All Nodes, compile.
5. Play: walk to zombies → the blade flames and glows orange on the ground; walk away → it cools. Hit a zombie with the
   hot blade → it burns for 3 s (20 damage/s, flames on its body) and the slash trail is ember-orange and 3× brighter.

## Tuning (all on MI_SwordFire, no code)
- `Intensity` 8 (brightness), `Speed` 1.4 (flame rise), `Scale` 2.5 (flame size; bigger number = smaller flames),
  `EdgePower` 2 (how much the fire hugs the edges), `Tint`, `StandoffCm` 2 (how far flames stand off the blade).
- In the Blueprint: `FireRange` 600 cm, `FireOn` (false = never burns; #95 can set it from the element choice later),
  the light's 4000 max intensity is the Multiply constant in FireThink.

## Tuning the burn
`BurnDamage` 5 per tick (4 ticks a second), `BurnTime` 3 s, both on the hero. The zombie's flames are `MI_Burning`.

## Not in this hand-off
The #95 purchase / element choice (set `FireOn` from it when it lands).
