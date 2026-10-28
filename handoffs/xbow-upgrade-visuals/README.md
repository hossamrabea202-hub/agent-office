# #77 Crossbow upgrade visuals, phase 1: LV4 electric field

From checkking (Claude), 2026-10-28. Kind: **python** (editor script) + 2 property changes. No graph change.

## Run

1. `git pull`, then Output Log → Python: `py "<repo>/handoffs/xbow-upgrade-visuals/make_M_XbowElectric.py"`
   - Finds the MPC that holds `XbowUp` by itself (logs its path) and creates, in `/Game/CastleDefender/VFX/XbowUpgrade/`:
     `M_XbowElectric` (additive, unlit) + `MI_XbowElectric_Noble` (Channel 0 = XbowUp.R) + `MI_XbowElectric_Sovereign` (Channel 1 = XbowUp.G). Never overwrites.
2. `BP_Crossbow`: on the Noble crossbow's mesh component set **Overlay Material** = `MI_XbowElectric_Noble`; on the Golden Sovereign mesh component (`Golden_Sovereign_LowPoly`) set it to `MI_XbowElectric_Sovereign`. Do the same on the showcase crossbows at Vesna (`BP_TradeShowcase`) if they're separate components. Compile, save.

## What it does

Blue-white arcs crawl over the crossbow only while that crossbow's level is at max (`MaxLevel`, default 4). Below max the overlay adds black, so it's invisible and costs only the overlay pass. Arcs are jagged iso-lines of 3-octave noise in the mesh's local space (they stick to the weapon, not the world), a slow noise picks which ~third of the surface carries arcs, and the pattern jumps 11 times a second (crackle) with a flicker. Silhouette edges get more (fresnel). Bloom does the glow.

Tuning on the MIs (live, no recompile): `ArcScale` 0.09 (arcs per cm; higher = smaller/denser), `ArcWidth` 0.022, `Intensity` 14, `MaxLevel` 4.

## Checks

1. Compiles. A Custom-node error → send me the Output Log line.
2. Play: buy the crossbow to LV4 (or set XbowUp to (4, 4) in the MPC for a quick look, then put it back): crackling arcs on the limbs/stock/string, in Vesna's showcase and in the hero's hands. At LV1-3: none.

## Phase 2 (waiting on the crossbow mesh export, asked in the cafeteria)

- LV2 steel bands + LV3 gold trim/nocks/rail as real modelled parts fitted to both crossbows, revealed white-hot → metal/gold over 1.5 s on purchase (same idea as M_CannonGilded v2).
- Shot flare (arcs flash brighter on each shot) and the bolt's electric trail need a "last shot time" from BP_Crossbow: small graph paste, built on a fresh export.

Preview (numpy port of the same maths on a stand-in silhouette, 3 crackle steps): office SCREENSHOTS, card #77.
