# #223 Farming system: gameplay v1

From TGA (Claude), 2026-10-31, an owner assignment relayed by checkking.

This is Blueprint-only: four new Blueprints plus two manifests. It uses TGA's crop art from #252 (`assets/tga/FarmCrops`).

The generator is `gen223.py`. It writes every graph, runs `fix_impure` on each one, and writes both manifests and `VARIABLES.md`.

| File | Nodes | Check |
|---|---|---|
| BP_FarmPlot_graph.txt | 77 | applyall check: Validation OK |
| BP_Farmer_graph.txt | 154 | Validation OK |
| BP_FarmDirector_graph.txt | 128 | Validation OK |
| BP_FarmerHire_graph.txt | 36 | Validation OK |
| manifest_hud.json → BP_ZombieHUD | 14 | dry-run OK on the 10-30b export with #201's ore line merged in first (+30 LinkedTo entries) |
| manifest_zombie.json → BP_Zombie | 19 | dry-run OK on the 10-30b export (+54 LinkedTo entries) |

## What it does

1. **Plots (BP_FarmPlot).** Each plot is a 4 × 4 m field with 16 crop patches.
   - Stage cycle: 0 bare → 1 sown → 2 growing → 3 ripe → 4 stubble.
   - Each farmer job is one step:
     - On a bare or stubble plot, a farmer **sows**.
     - On a sown or growing plot, a farmer **tends** it.
     - On a ripe plot, a farmer **harvests**: 16 food for wheat, 10 for cabbage (`Yield`).
   - A tended crop grows one stage at each **dawn** (BP_DayNight). An untended crop waits.
   - A zombie walking into a sown, growing or ripe field **tramples** it to stubble, so that crop is lost.
2. **Farmers (BP_Farmer).** Each farmer checks every 0.5 s:
   - **Work:** take the first free plot that needs work, walk there, work for 6 s, then carry the harvest to the granary. Delivery adds to HUD **Food** and saves.
   - **Shelter:** at night, or when a zombie is within 20 m, the farmer drops the job and runs to the granary. Work resumes when it is safe.
   - **Death:** 100 HP; at 0 → ragdoll, the plot is freed, Farmers − 1 on the HUD, and the body is gone after 30 s.
   - Fewer farmers means fewer jobs per day, which means less food.
3. **Raids (BP_Zombie manifest).** A zombie's target is its Owner: it walks to the Owner and ApplyDamages it.
   - Right after the zombie's soldier search, a **living farmer within 25 m that is closer than the current target** becomes the target.
   - A dead farmer target drops back to the player.
   - Farmers working outside the walls therefore draw the zombies that pass the fields. Escorting them is the player's job.
4. **Granary (BP_FarmDirector).** The granary is the store and the shelter.
   - It counts days and starts 3 farmers on a new game (`StartFarmers`).
   - It keeps HUD `Food` / `Farmers` up to date.
   - **Save/load:** slot `CastleSaveFarm` (BP_CastleSave), `Data = [Food, Farmers, Day, (Stage, Tended) per PlotId]`.
     - It saves on every delivery, dawn, hire, death and trampled field, and loads at start.
5. **Hiring at the barracks (BP_FarmerHire).** A trigger sits beside the barracks NPC.
   - Walking in shows the banner `[H] Hire a farmer: 60 gold …`. **H** hires one farmer, who walks out from the granary. The maximum is 12.
   - If you can't afford it or the farm is full, the banner says so.
6. **HUD:** `FOOD n      FARMERS n` appears under the ORE line. #227 (army eats) reads `Food` from the same HUD variable.

## Master steps

0. **Import the crop art first:** `py ".../assets/tga/FarmCrops/import_farm_ue.py"` (hand-off #252).
1. **Create the Blueprints:** `py ".../handoffs/farm-223/setup_farm_ue.py"`. Run 1 creates the 4 Blueprints with their components and the farmer defaults.
2. **Add the variables:** add each Blueprint's variables from `VARIABLES.md` (BPVar lines, or by hand). On BP_FarmPlot, make `Kind`, `Yield` and `PlotId` Instance Editable. Add `Food` and `Farmers` to **BP_ZombieHUD**.
3. **Paste the graphs** into each EventGraph in this order, compiling after each one:
   **BP_FarmPlot → BP_FarmDirector → BP_Farmer → BP_FarmerHire**.
   - Delete the default BeginPlay and Overlap stubs first.
   - Compile errors on cross-calls (DoWork, SaveNow, FarmerDied, SpawnFarmer) are expected until the other Blueprints exist.
   - At the end, **Refresh All Nodes and compile all four again**.
4. **Run the setup script again.** Run 2 fills `StageMeshes` (wheat 1–4 in slots 1–4, cabbage young/young/ripe in slots 6–8).
5. **Merge the BP_ZombieHUD manifest:** export the EventGraph to `live.t3d`, then:
   ```
   python tools/applyall/applyall.py merge --live live.t3d --manifest handoffs/farm-223/manifest_hud.json --out merged.t3d
   ```
   - Apply it after #201's ore line, which is already in.
   - Then paste, compile, and set the DrawText **Font** pin to the game font.
6. **Merge the BP_Zombie manifest** the same way with `manifest_zombie.json`.
   - It needs BP_Farmer compiled first, because it reads `Dead`.
   - Rewires: `CX_503.Completed → zfAsFarmerTarget`, and the farmer loop's `Completed → CX_1`.
7. **Level setup:**
   - **Granary:** place one `BP_FarmDirector` in the yard, near the gate, inside the NavMesh, and give its Granary a shed mesh.
   - **Hire trigger:** put `BP_FarmerHire` beside the barracks NPC.
   - **Plots:**
     - Place 2–6 `BP_FarmPlot` on flat ground outside the walls, inside the NavMesh. Zombies have to pass near them.
     - Give each plot its own **PlotId** (0, 1, 2…) and set **Kind** (0 wheat, 1 cabbage; cabbage gets **Yield 10**).

## Test list

1. **New game:** 3 farmers walk to the plots. Bare plots become sown wheat after 6 s each. FARMERS 3 is on the HUD.
2. **Tending:** the next jobs tend the sown plots. At dawn, tended plots show growing wheat; the next day they are ripe.
3. **Harvest:** ripe plots are harvested to stubble. The farmer walks to the granary and FOOD goes up by 16 (10 for cabbage).
4. **Night or zombie near:** farmers drop their tools and run to the granary. When it is day and clear, they go back to work.
5. **Raid:** let a zombie pass within 25 m of a working farmer → it turns on him. At 0 HP the farmer ragdolls, FARMERS − 1, and the body is gone after 30 s. The zombie then goes back to its old targets.
6. **Trample:** walk a zombie through a growing field → stubble.
7. **Hire:** stand at the barracks trigger → banner shows. Press H with ≥ 60 gold → −60 gold, FARMERS + 1, and a farmer walks out of the granary. With < 60 gold, you get the "not enough gold" banner.
8. **Save/load:** quit and restart → same FOOD, same farmer count, and the plots show the same stages.

## Honest notes

- **Farmer body:** the farmer uses the soldier's body and anim BP (copied by the setup script) until TGA makes a farmer character. That character is on the card as a follow-up. The work itself has no animation yet: he stands for 6 s.
- **Hiring:** it is a trigger next to the barracks NPC, not a row in BP_BarracksHUD's recruit menu. That menu graph is 31 MB, and a row there is a separate, larger manifest. Say if you want it moved into the menu.
- **Saving:** the save keeps the farmer count, not each farmer's position. On load, everyone starts at the granary.
- **Zombie costs:** zombies only reconsider targets at their existing retarget point, so the farmer check costs nothing extra per frame. Each farmer scans the zombie list every 0.5 s. That is fine up to about 200 zombies × 12 farmers.
