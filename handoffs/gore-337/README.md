# #337 part 2: blood splats on every hit + "not too gory" limb severing

By `adjustedfilm (Claude)`, 2026-10-31. Owner `W:`: *"zombiez lose body parts in battles with sword slashes, not so much
gor also the blood spread looks cartonish..."*. Research: `RESEARCH.md`. Assets (part 1): `assets/adjustedfilm/Blood337`
(splats, stump caps, droplet and mist materials, import script). Built on the Master's 2026-10-30b BP_Zombie export (the
Master: "use 10-30b for now"). Bones come from `exports/adjustedfilm/gore-337/bones.txt`.

## What the player gets

- **Every hit:** a dark, wet blood splat lands under the zombie. There are 8 real shapes; a heavy hit leaves a bigger one.
  It dries to brown and matte over 30 s, then fades out. The game's own blood burst still plays; its rebuild waits on the
  BP_BloodBurst export.
- **Severing, kept "not too gory":**
  - It only happens on a melee hit from up to 3.5 m away, and only on a heavy hit (25 % of the zombie's HP or more) or a
    killing hit.
  - A normal heavy hit only severs once the zombie is already wounded (second hit or later).
  - At most 2 limbs per zombie, and at most 8 loose limbs in the world.
  - Chances, heavy / killing hit:

    | Limb | Heavy | Killing |
    |---|---|---|
    | forearm | 25 % | 35 % |
    | upper arm | 10 % | 20 % |
    | lower leg | – | 15 % |
    | head | – | 10 % (Full gore setting only) |
  - The limb falls away with an outward push and a spin, has its own dried cap, collides with the world only, and is gone
    after 20 s.
  - The stump gets a dried, dark cap. Nothing hangs off it.
- **Gore setting** (`GoreLevel` on BPC_Gore337):
  - 0: off;
  - 1: reduced, the default: no heads;
  - 2: full.

  `LimbsOn = false` keeps the splats only.

## Pre-checks (done)

| Check | Result |
|---|---|
| `applyall check` | BPC_Gore337 146 nodes / 186 links; BP_SeveredLimb337 56 / 75; BP_WoundCap337 18 / 23; hook 8 / 7: all **Validation OK** |
| `fix_impure.py` | no changes on all 4 |
| `merge --dry-run` of `manifest_zombie_gore.json` on the 10-30b BP_Zombie export | **Validation OK**, +10 links (expected +10) |
| self-calls to own events | none (CheckParent is a timer by name) |

## Steps (Master)

1. `py "<repo>/assets/adjustedfilm/Blood337/import_blood337_ue.py" --dry-run`, then without it. That gives the textures,
   the self-drying decal material, 4 stump caps, and the droplet and mist materials.
2. `py "<repo>/handoffs/gore-337/setup_gore337_ue.py" --dry-run`, then without it. It makes BPC_Gore337,
   BP_SeveredLimb337 (Body capsule as the root, Limb, LimbCap) and BP_WoundCap337 (Cap).
   If the log says `MANUAL:`, drag Body onto the root (a one-minute fix).
3. Paste in this order:
   - BPC_Gore337: paste the 16 lines of `BPC_Gore337_BPVar.txt` one at a time, Compile, then paste
     `BPC_Gore337_graph.txt` into its EventGraph.
   - BP_SeveredLimb337: paste `BP_SeveredLimb337_graph.txt`.
   - BP_WoundCap337: paste `BP_WoundCap337_graph.txt`.

   Compile and save each one.
4. `py ".../setup_gore337_ue.py" --finish --dry-run`, then without it. It sets the cap meshes and the decal material,
   and adds the component **Gore** to BP_Zombie.
5. BP_Zombie: `applyall merge --live <fresh BP_Zombie export> --manifest handoffs/gore-337/manifest_zombie_gore.json`,
   then Ctrl+A, Delete, paste the merged file, compile and save. The hook goes right after the BP_BloodBurst spawn.

## Tests (Play)

1. Hit zombies: a dark splat lands under them each hit. Watch one for 30 s: it goes brown and matte, then fades.
2. Heavy sword hits on a wounded zombie: now and then a forearm or upper arm comes off. It falls, rolls and lies there.
   The stump shows a dark cap. The zombie keeps fighting.
3. Killing blows: sometimes a lower leg goes. Set `GoreLevel` = 2 to also allow the head.
4. Cannon kills never sever (melee only).
5. A limb lying around vanishes after 20 s, and its cap goes with it. When a zombie is removed, its stump cap goes too.
6. **The biggest risk**, which I can't confirm without the editor: the loose limb is a copy of the zombie that is
   collapsed to the one limb. If it shows the whole body, or the limb in the wrong place, set `LimbsOn = false` (splats
   and nothing else) and post a screenshot on #337. I'll switch to the backup method then.
7. No "Accessed None" in the log.

**Rules applied (INDUSTRY_SECRETS):** §3.5 gore without C++ (hide bone, cap, spawned limb, the Dying Light 2 way), §0
rule 1 (measured blood values), §4 VFX (lit, wet, no glow), and "not too gory" per RESEARCH §4.1.
