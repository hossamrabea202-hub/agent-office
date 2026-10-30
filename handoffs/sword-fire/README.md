# Sword fire — the hero's blade burns when zombies are close

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
3. `BP_ThirdPersonCharacter`: add the 6 variables in `VARIABLES.md` (FireMID, FireLight, FireHeat, FireOn, FireRange, FireNear).
4. Paste `Hero_SwordFire_graph.txt` into the EventGraph (paste file: Validation OK, 37 nodes). Then two wires by hand
   (the applyall merge cannot run on the hero export: the whole-asset conversion drops the Enhanced Input and
   PlayMontage nodes, so the live file fails its own check):
   - Event BeginPlay's exec (`K2Node_Event_1`) → the pasted **CreateDynamicMaterialInstance** node (`sfMakeFireMID2`),
     replacing its old wire to the cast node `K2Node_DynamicCast_0`;
   - the pasted **Set Timer by Function Name** (FireThink) → that cast node `K2Node_DynamicCast_0`.
   Refresh All Nodes, compile.
5. Play: walk to zombies → the blade flames and glows orange on the ground; walk away → it cools.

## Tuning (all on MI_SwordFire, no code)
- `Intensity` 8 (brightness), `Speed` 1.4 (flame rise), `Scale` 2.5 (flame size; bigger number = smaller flames),
  `EdgePower` 2 (how much the fire hugs the edges), `Tint`, `StandoffCm` 2 (how far flames stand off the blade).
- In the Blueprint: `FireRange` 600 cm, `FireOn` (false = never burns; #95 can set it from the element choice later),
  the light's 4000 max intensity is the Multiply constant in FireThink.

## Not in this hand-off
Fire damage / burning zombies, the sword-slash trail turning to fire (`SM_SwordSlash` MID, same ramp works), and the
#95 purchase/choice. Say the word for any of them.
