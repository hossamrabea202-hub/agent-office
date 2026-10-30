# #201 Mine + ore carts + metal stockpile — Blueprint logic v1

From: hossam gmail laptop2 (Claude), 2026-10-30. Blueprint-only. Three new Blueprints + one paste into `BP_ZombieHUD`.
All four graphs: `applyall check` Validation OK; the HUD manifest dry-run on the 2026-10-30b export: Validation OK.

**What it does**
1. `BP_Mine` (placed on the road outside the wall) sends one `BP_OreCart` every 45 s with a random metal:
   iron 55 %, copper 20 %, silver 15 %, gold ore 7 %, starmetal 3 %. Each wave shifts the roll 1.5 points toward the rare
   metals. 10 % of the time the mine "strikes a vein": the next 2 carts carry the same metal.
2. The cart tints its ore load to the metal's colour, walks the NavMesh to the castle gate and, within 5 m of
   `BP_CastleGateControl`, adds 1 to the stockpile and disappears.
3. The cart has 300 HP. If zombies kill it, it drops a `BP_OrePile` of that metal on the road. The hero walks over the pile to
   collect it; it vanishes after 60 s.
4. The stockpile is `Ore[5]` on `BP_ZombieHUD` (same place as `Gold`), drawn as one line under the XP bar:
   `ORE   Fe 12   Cu 3   Ag 1   Au 0   Star 0`.
5. Spending the metals (forge / gate upgrade / mint) is in `RECIPES.md` — the Armory and Vesna shop hooks come next, once
   the owner approves the table.

## Master steps

**A. BP_Mine** — new Blueprint, parent `Actor`, folder `/Game/CastleDefender/Gameplay/Castle/`.
- Components: a StaticMesh (TGA's mine entrance when it lands; any rock/cube now). The cart spawns 3 m along the actor's
  **forward (X) arrow**, so point the arrow down the road.
- Variables (`VARIABLES.md`): `Period` float 45, `VeinLeft` int 0, `VeinMetal` int 0, `LastMetal` int 0.
- Paste `BP_Mine_graph.txt` into the EventGraph. It contains Event BeginPlay (if the graph already has one, delete the
  empty default first), Refresh All Nodes, compile.

**B. BP_OreCart** — new Blueprint, parent `Character` (so it walks the NavMesh like a soldier).
- Components: `Cart` StaticMesh (SM_Camp_HandCart from CampKit, or the #50 cannon cart body), and a StaticMesh named
  exactly **`Load`** (a lump of ore on the cart; its material needs a Vector parameter named **`Tint`** — make a 1-node
  material `M_OreLoad` with a VectorParameter "Tint" into Base Color, or a dynamic instance). Capsule radius ~90, half
  height ~90; Mesh (skeletal) left empty.
- Class defaults: Auto Possess AI = **Placed in World or Spawned**, AI Controller Class = AIController.
  CharacterMovement → Max Walk Speed 250, Use RVO Avoidance on.
- Variables: `Metal` int 0, `HP` float 300.
- Paste `BP_OreCart_graph.txt` (contains Event AnyDamage — delete the stub first if present). Compile.
- Tag the cart so zombies attack it: add the same actor tag / collision profile your zombies use to pick soldiers
  (`Pawn` object type + the #48 target scorer: class `BP_OreCart`, priority 100 within 25 m). That scorer rewire is for
  Codex/Master — the cart already takes damage from any zombie hit.

**C. BP_OrePile** — new Blueprint, parent `Actor`.
- Components: a StaticMesh named **`Load`** (same `M_OreLoad` material), and a Sphere collision radius 120 set to
  Overlap All Dynamic (Generate Overlap Events on).
- Variables: `Metal` int 0.
- Paste `BP_OrePile_graph.txt` (contains Event ActorBeginOverlap). Compile.

**D. BP_ZombieHUD**
- Add variable `Ore` — **Integer, Array**, default 5 entries all 0 (see `VARIABLES.md`).
- `python tools/applyall/applyall.py merge --live <BP_ZombieHUD EventGraph export> --manifest handoffs/mine-201/manifest_hud.json --out merged.t3d`
  then paste, Refresh All Nodes, compile. The counter line draws after the XP bar texture (`UX_CallFunction_23`) and
  before the level-up branch (`K2Node_IfThenElse_H296`). Apply after the #183 manifest or before — they do not overlap.
- Set the DrawText node's **Font** pin to the game font (the one the gold counter uses) — it is left empty, which falls
  back to the engine font. Position is 1.5 % / 14 % of the viewport; move the two Multiply constants if it sits on
  something.

**E. Level**: place one `BP_Mine` 80–150 m outside the gate on the road, inside the NavMesh bounds. Make sure the
NavMesh reaches from the mine to the gate (the carts use the same mesh the zombies do).

**Test**: play, wait 45 s — a cart with coloured ore rolls to the gate, the ORE line counts up. Let zombies reach a
cart: it breaks into a pile; walk the hero over it: counted. Wave 10+: more silver/gold/starmetal.

## Follow-ups (not in this paste)
- Zombie priority on carts (#48 scorer), escort order for soldiers ("guard the cart"), day/night risk knob.
- Spending: see `RECIPES.md`; Armory/Vesna shop rows that take metals instead of gold, and the mint (copper + silver → gold).
- Art: TGA #202 item 1 (mine entrance + 5 ore load meshes), stockpile shed (item 2).

## Part 2 — BP_Forge (spending), added 2026-10-30 after the owner approved RECIPES.md

`BP_Forge_graph.txt` (208 nodes, Validation OK). New Blueprint, parent `Actor`, components: the forge mesh
(`SM_Camp_Forge` + anvil from CampKit) and a Sphere collision radius 300, Overlap All Dynamic, overlap events on.
- Hero steps in → keys 1–6 switch on and the notice banner shows the menu. Steps out → keys off.
- `1` mint 60 gold (1 Cu + 1 Ag) · `2` mint 150 gold (1 Au) · `3` gate bands, next level each press
  (3 Fe → 2 Ag + 2 Fe → 2 Au + 1 Ag) · `4` iron swords (2 Fe) · `5` silver bolts (1 Ag + 1 Cu) · `6` steel plate (4 Fe + 1 Cu).
- Not enough metal → banner says what is missing. Bought → banner confirms, metals leave the stockpile.
- **Add to BP_ZombieHUD** (VARIABLES.md): `ForgeGate`, `ForgeSword`, `ForgeBolt`, `ForgePlate` (int 0). The forge writes
  the levels; the effects (gate HP ×, sword/bolt damage ×, soldier HP ×) are the next small manifests into the gate,
  soldier and bolt Blueprints once this is in and tested. The mint works fully now.
- Paste into the Forge EventGraph (contains ActorBeginOverlap / ActorEndOverlap: delete the stubs first), compile,
  place the forge in the castle yard. Hero items and starmetal recipes come with the pack/equip system (v2).
