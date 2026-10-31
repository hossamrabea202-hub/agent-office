# #11 Survivors: wounded soldiers arrive, ask to join, heal at the barracks, then fight

By `adjustedfilm (Claude)`, 2026-10-31.
- **System only**, by owner order: "only system, we will use meta humans later".
- **The body is a stand-in:** the soldier's own mesh and animation. A MetaHuman replaces it later by changing BP_Survivor's
  Mesh only; the graphs stay.
- **Built on** `handoffs/exports/master/2026-10-30b`:
  - BP_BarracksHUD (how a recruit is spawned);
  - BP_NoticeHUD (`PushNotice(Text, Tier)`);
  - BP_SoldierSword, BP_CastleGateControl and BP_NPC_Barracks (names checked).
- **Pre-checked:** `fix_impure.py` found nothing to fix, and `applyall check` gives **Validation: OK** on both graphs:
  - `BPC_Survivors`: 56 nodes;
  - `BP_Survivor`: 153 nodes.
- **No existing Blueprint is changed:** two new Blueprints and one component on the hero.

## What the player sees

1. **Arrival.** Sometimes, while no zombie is alive, a wounded soldier limps toward the gate from about 30 m outside.
   - A notice says: *"A wounded soldier is at the gate. He asks to join your army."*
   - Frequency: about one every 3–4 minutes of calm, never in the first 2 minutes, and at most 2 waiting at once.
   - He walks slowly (walk 130, animation at 0.7x). A gold line floats over his head: **Wounded soldier**.
2. **He waits just inside the gate.**
   - From afar the line reads *Wounded soldier – wants to join your army*.
   - Within 4 m it reads **[E] Take him into your army**.
3. **Press E.**
   - Notice: *"He thanks you and limps to the barracks to heal."*
   - He walks to the barracks NPC (label: *Going to the barracks to heal*).
   - If the army already has 30 men, the line shows *Your army is full – make room first* for 3 s, and he keeps waiting.
4. **He heals** next to the barracks for 60 s. The line counts *Healing 0 % … 100 %* and his animation speeds back up to
   normal.
5. **He joins.** A normal **BP_SoldierSword** appears on his spot, exactly like a recruit bought at the barracks: same
   AI, orders, levelling and saving as any recruit. Notice: *"A survivor has healed and joined your soldiers."*

## How it works

- **`BPC_Survivors`** is a hero component named "Survivors" with a 3 s timer, `SurvPoll`. It spawns a survivor when all
  of these hold:
  - no BP_Zombie is alive;
  - fewer than `MaxWaiting` survivors are around;
  - `MinGap` seconds have passed since the last one;
  - game time is past `FirstDelay`;
  - a `Chance` roll succeeds.
  - **Where he spawns:**
    - the gate is BP_CastleGateControl;
    - "outside" is the direction away from the castle centre (2300, 1725), the centre of the #41 castle box;
    - he spawns `ArriveDist` past the gate, ±7 m sideways, on the navmesh, facing the gate.
- **`BP_Survivor`** is a Character with AI possess on spawn. A 0.25 s `Think` timer does three things:
  - turns the label toward the camera;
  - runs the state machine (`State` 0–3, as above);
  - sets the label text.
  - Moves use `SimpleMoveToLocation`, re-issued only while he stands still, so the path isn't restarted 4 times a second.
- **The heal step is the existing recruit path.** When he has healed, a BP_SoldierSword spawns at his transform, the
  same node the barracks uses, and the survivor is destroyed. So he counts toward the army, takes orders and saves like
  any other recruit.

## Files

| File | What |
|---|---|
| `setup_survivors11_ue.py` | Editor script, safe to re-run, with `--dry-run`. Creates BP_Survivor (soldier body copied from BP_SoldierSword's Mesh, a gold Label text, walk 130, AI possess) and BPC_Survivors, and adds "Survivors" to the hero. |
| `VARIABLES_BPVar.txt` | 7 BPVar lines for BPC_Survivors and 9 for BP_Survivor. Defaults and meanings are in `VARIABLES.md`. |
| `BPC_Survivors_graph.txt` | BPC_Survivors EventGraph |
| `BP_Survivor_graph.txt` | BP_Survivor EventGraph |
| `gen_survivors11.py` | generator (bpkit) |

## Steps (Master: paste only)

1. **Dry-run first:** `py "<repo>/handoffs/survivors-11/setup_survivors11_ue.py" --dry-run`. Read the Output Log: it
   names the soldier body it will copy.
2. **Run it for real:** `py "<repo>/handoffs/survivors-11/setup_survivors11_ue.py"`, then check `setup_survivors11.txt`.
3. **Add the variables.** Open `/Game/CastleDefender/Gameplay/Survivors/BPC_Survivors` → My Blueprint → paste the 7
   BPC_Survivors lines of `VARIABLES_BPVar.txt` on the VARIABLES header, one at a time, then Compile. Do the same on
   **BP_Survivor** with its 9 lines.
4. **Paste the graphs.** Paste `BP_Survivor_graph.txt` into BP_Survivor's EventGraph, then Compile and Save. Then paste
   `BPC_Survivors_graph.txt` into BPC_Survivors' EventGraph, then Compile and Save.
   - Paste BP_Survivor **first**, because BPC_Survivors spawns it.
5. **Compile and save the hero** (it now carries "Survivors").

**Faster test:** temporarily set BPC_Survivors `FirstDelay` = 5, `MinGap` = 10 and `Chance` = 1. Put them back to
120 / 150 / 0.12 afterwards.

## Checks (Play)

1. Calm, after the test values above: a survivor spawns outside the gate and the notice shows. He limps in and stops
   just inside the gate. The gold line faces the camera.
2. Walk up to him: the line changes to **[E] Take him into your army**. Press E: notice shown, he walks to the barracks NPC.
3. At the barracks: *Healing n %* counts up for 60 s, then a normal sword soldier stands in his place and the notice shows.
   That soldier takes orders like any recruit.
4. With a zombie alive, no new survivor arrives (one already inside keeps going).
5. Army at 30: pressing E shows *Your army is full – make room first*.
6. Two minutes of Play: no "Accessed None" from BP_Survivor or BPC_Survivors.

## Decisions

- **Survivors only arrive when no zombie is alive, and zombies don't target them.** They are safe until they become soldiers.
  - **Why:** zombie targeting lives in BP_Zombie, and this card is a self-contained system.
  - **Possible follow-up:** let zombies attack survivors on the road, in the same way as TGA's farmer raid manifest (#223).
- **MaxArmy = 30 counts every BP_SoldierSword**, including crossbowmen and commanders (they are its children).
  - **Why:** there is no cap variable in the 10-30b exports.
  - **When #75's cap lands:** point MaxArmy at that cap.
- **Healing happens at the barracks NPC** (60 s), the same place recruits come from. When he has healed he becomes a plain
  sword recruit, rank 1.
- **The key is E**, the game's "talk" key. Survivors wait at the gate, away from the barracks and Vesna, so it doesn't clash.
- **Survivors still on their way are not saved.** A loaded game starts without them. A healed survivor is a normal soldier
  and saves like one.
- **The body is a stand-in** (soldier mesh and anim class). It may show without the knight armour if that is a separate
  component on the soldier. **MetaHuman later** (owner): replace BP_Survivor's Mesh; the logic doesn't change.

## Office rules applied

- **The Master only pastes:** a setup script with a dry-run, BPVar lines, two clean graphs, exact steps and a test list.
- **Nothing visual was made** (system-only card): no texture, material or decal change.
