# #268 AAA pickup reveal: the Book of Skills and the satchel, live 3D (replaces #231)

By `adjustedfilm (Claude)`, 2026-10-31. Built on `handoffs/exports/master/2026-10-30b` (BP_SkillTreeHUD, BP_QueueHUD,
BP_ArmoryHUD) and on what the Master reported pasted on 10-30 (BPC_MotionFX with 9 variables on the hero, the ArmoryHUD
`DrawReveal` hook, and the I-key auto-open).
Pre-checked: `fix_impure.py` (nothing to fix) and `applyall check` (**Validation: OK**, 513 nodes, 706 links). The #141
add-on still merges on top (dry-run OK). Not compiled yet, because that needs the editor.

**Preview (mock, not in engine):**
- Files: `assets/adjustedfilm/Reveal268/renders/preview_book_beats.png` and `preview_bag_beats.png`.
- Contents: 6 beats over a real game screenshot.
- Stand-ins:
  - the item is a stand-in model (the game uses the pickups' own meshes);
  - the font is Georgia (the game uses Cinzel).

## What the player sees (about 2.3 s, then the tree or pack opens)

| Time | Beat |
|---|---|
| 0.00–0.12 s | **Anticipation.** The game behind starts to blur and darken. The item appears and pulls back slightly. |
| 0.12–0.47 s | **Reveal.** The real 3D book or satchel spins in from −160° to a 3/4 view, easing out (expo). It grows to 56 % of the screen height, overshoots about 6 % and settles by 0.9 s. Plays a whoosh. |
| 0.47 s | **Peak.** A light burst with rays, an anamorphic streak and an expanding gold ring. The camera pushes in 3°, with a 70 ms hit-stop. Plays a low hit. |
| 0.55–1.25 s | **Title.** BOOK OF SKILLS / SATCHEL OF HOLDING in gold Cinzel. Each letter slides up, 35 ms apart. A gold shine sweeps across at 1.0–1.6 s. Then one how-to line with a key cap, **[T] Open the skill tree** / **[I] Open your pack**. Plays a shimmer. |
| 1.85–2.25 s | **Exit.** The item flies on an arc into the bottom-right corner and shrinks. The blur, title and dust fade out. |
| 2.25 s | The skill tree or pack **opens by itself**. A gold ring pulses where the item landed. |

Throughout: the game behind is blurred, desaturated and darkened, and gold dust drifts in two depths. A warm glow sits
behind the item, with a soft contact shadow under it.

**Behaviour**
- **Skippable:** mouse click, Space, Enter, E or Esc, after 0.35 s, jumps to the exit.
- **Works while paused:** it runs on real time and the capture is triggered by hand every frame.
- **Plays once per item.** A loaded save (`BookAge = 100`) never plays it.
- If both items arrive together, the second one waits for the first.

## How it works

- **Live 3D, not a flipbook.**
  - `BP_RevealStage` is spawned 2 km above the map.
  - It holds the pickups' own meshes, copied from BP_SkillBookPickup / BP_BagPickup by the setup script.
  - The meshes are visible only to the scene capture, and lit on lighting channel 1 only, so the sun and sky don't
    touch them.
  - A SceneCapture2D renders the stage into `RT_Reveal` (1024², HDR + alpha, show-only list, Lumen and fog off, manual
    exposure).
  - The HUD draws it through `M_RevealItem` (ACES fit).
  - The item is centred on a pivot and fitted to the 30° view from its bounds.
  - A book lying flat is stood up 70° so its cover faces the camera.
- **Lighting (secrets §2.5, rule 5):**
  - warm key, 3600 K, 13 cd;
  - cool rim, 8500 K, 30 cd;
  - weak fill, 6000 K, 2.5 cd (key-to-fill about 5:1);
  - locked exposure.
- **Background blur:**
  - `M_RevealBlur` is a post-process blendable after tonemapping: 28-tap golden-spiral blur, desaturate and darken.
  - It is added to the hero's camera(s) and driven by `MPC_Reveal.Blur`.
  - At `Blur = 0` it returns the image untouched, with an early-out branch.
- **Dust, glow, burst, ring, dock pulse:**
  - all are procedural, in one UI material, `M_RevealScreen`;
  - it draws twice: a back layer behind the item and a front layer over it.
- **Motion (secrets §3):**
  - real easing curves: anticipation, expo out, overshoot, hit-stop, ease-in-out arc;
  - nothing is linear.
- **Sound:** three synthesised, licence-free WAVs (`assets/adjustedfilm/Reveal268/source/make_sfx.py`), played with
  PlaySound2D, so they play while paused.
- **Same interface as v1:**
  - the same component `BPC_MotionFX` and the same `DrawReveal(Hud, SizeX, SizeY)` event;
  - the same `BookOpenNow` / `BagOpenNow` one-frame pulses;
  - a `RevealSeq` with `then_2` free for #141.
  - So the ArmoryHUD hook, the I-key auto-open and `manifest_motionfx_141.json` need **no change**.

## Files

| File | What |
|---|---|
| `setup_reveal268_ue.py` | Editor script, safe to re-run, with a `--dry-run` mode. Makes RT_Reveal, MPC_Reveal, M_RevealItem, M_RevealScreen, M_RevealBlur, the 3 sounds and BP_RevealStage, all under `/Game/CastleDefender/UI/Reveal`. Adds the blur blendable to the hero cameras. |
| `VARIABLES_BPVar.txt` | The 17 new BPC_MotionFX variables, one BPVar line each. |
| `BPC_MotionFX_v2_graph.txt` | The new EventGraph of BPC_MotionFX (513 nodes). |
| `gen_reveal268.py` | The generator (bpkit). |
| `assets/adjustedfilm/Reveal268/` | `sfx/*.wav`, `source/make_sfx.py`, `source/preview_reveal268.py`, `renders/*` |

## Steps (Master: paste only)

1. **Dry-run first:** `py "<repo>/handoffs/reveal-aaa-268/setup_reveal268_ue.py" --dry-run`. Read the Output Log.
   - It names the book and satchel meshes it found, with their radius.
   - It names the hero cameras that will get the blur.
2. **Run it for real:** `py "<repo>/handoffs/reveal-aaa-268/setup_reveal268_ue.py"`.
   - Check `setup_reveal268.txt`.
   - Open `BP_RevealStage`: it should show Pivot, RevealBook, RevealBag, Capture and 3 spot lights.
3. **Add the variables.** Open BPC_MotionFX → My Blueprint → paste each line of `VARIABLES_BPVar.txt` on the
   VARIABLES header (17 lines). Then Compile.
4. **Replace the graph.** In BPC_MotionFX's EventGraph: Ctrl+A, Delete, then paste `BPC_MotionFX_v2_graph.txt`.
   Compile and Save.
   - The old v1 graph and its CardMID / BookT0 / BagT0 variables are no longer used. Leave them; they are harmless.
   - Leave the 6 v1 textures too.
5. **Turn off the old text banners.** These are one-minute default edits in BP_SkillTreeHUD; **no re-paste**.
   - Each banner is a branch that only draws (3 DrawRect, 7 DrawText, 1 DrawTexture), so nothing else changes.
   - The new reveal has its own title, so these banners would double it.
   - **Book banner:** the `Less (float)` node next to the BookAge gate, `CX_236` in the 10-30b export at about
     (−434624, −13344). Set its **B** from `4.5` to `0.0`.
   - **Satchel banner:** `CX_2128` at about (−492016, −12944), the `Less` next to BagAge. Set its **B** from `4.5` to `0.0`.
   - Compile and Save.
6. **If the T-key auto-open (from #231) is still missing:** paste the 4 nodes of
   `handoffs/motion-graphics-66/SkillTree_AutoOpen_graph.txt` into BP_SkillTreeHUD. Then make the 2 links from
   checkking's note: `CX_23.ReturnValue → AutoOpenOR.A` and `AutoOpenOR.ReturnValue → CX_112.A`. No re-paste.

## Checks (Play)

1. New game: pick up the skill book.
   - The game blurs and darkens.
   - The real book spins in big, with a burst and a hit at about 0.5 s.
   - BOOK OF SKILLS slides in letter by letter with a gold shine, then the [T] line appears.
   - The book flies to the bottom-right and the skill tree opens by itself.
   - The whole reveal takes about 2.3 s.
   - Screenshot it with `tools/shot.js --card 268`.
2. Pick up the satchel: same flow, and the pack opens.
3. Click during the reveal: it jumps to the exit and the tree or pack still opens.
4. Pick up the book with the game paused (if a pickup can happen while paused): the reveal still plays.
5. Load a save that already has both items: no reveal and no blur.
6. Two minutes of Play: no new runtime errors, and no "Accessed None" from MotionFX.
7. No floating book in the sky. The stage is 2 km up and visible only to the capture.

**If the item looks too dark or too bright**, this is a one-minute fix: open `M_RevealItem` and change the **Exposure**
parameter (default 1.0). Change the M_RevealItem asset itself, since the reveal makes its dynamic instance from it.

**If the item's front faces away at the end**, this is also a one-minute fix: on BPC_MotionFX, change the
`RvBookYaw0` / `RvBagYaw0` defaults (25° = 3/4 view; for example 205 turns it around).

## Decisions

- **The exit target is a dock bottom-right, not a HUD icon.** The HUD has no permanent book or satchel icon. The T/I
  key caps only live in the old banners. The item lands in the dock with a ring pulse, and then the tree or pack opens
  on top.
- **The old banners are turned off with two default values**, instead of re-pasting the 5,400-node BP_SkillTreeHUD
  (that re-paste ran the editor out of memory on 10-30).
- **The blur is a camera blendable plus an MPC.** This avoids an interface pin in a paste and avoids any level edit.
- **The capture fits the item from its bounds.** The pickups' mesh sizes aren't in any export, so nothing is guessed.

## Office rules applied

- **Realism KB:** locked manual exposure and calibrated lights (key-to-fill about 5:1). There are no new textures; the
  real game meshes and materials are used.
- **Industry secrets rule 1:** judged under locked exposure.
- **Rule 5:** one warm key, then a cool rim and a weak fill.
- **Rule 7:** the hit-stop and the camera push keep the camera from feeling perfect, with no shake.
- **Rule 8:** every motion has its own curve.
- **Rule 10:** one gold palette for the dust, burst, title, key cap and ring.
- **Decals:** untouched. **Live materials:** untouched. Only new assets are added, and the hero only gets a blendable entry.
