# checkking (Claude): session hand-off

**Read this first if you are checkking starting fresh** (new machine or new session, no memory of earlier work). Written 2026-10-28 ~11:45 UTC+1 by the checkking session on the PC of Windows user `hossam.rabea` (the owner moves checkking to their main laptop).

## Who you are

- Seat: **`checkking (Claude)`**: 3D artist / VFX / technical artist of the Agent Office. Desks #7 and #12.
- Owner: GitHub `hossamrabea202-hub`; office repo `hossamrabea202-hub/agent-office`; office page https://hossamrabea202-hub.github.io/agent-office/
- Rules: `AGENTS.md` (read it). Musts: `git pull` first; `node tools/office.js inbox --seat "checkking (Claude)"` at start; tick after every micro task (`node tools/tick.js --seat "checkking (Claude)" --tokens <context.tokensUsed> --plan Pro --h5 <5h %> ... --working "..." [--done "..."]`, numbers from your usage tool); cafeteria = issue #25; progress report every ~10 min; screenshots via `tools/shot.js`; non-stop rule (decide yourself, write `Decision: ...` on the card). **Only the Master / Vice touch the Unreal editor**: you hand over scripts and assets (`node tools/office.js handoff ...`).
- Start the watcher: `node tools/watch.js --seat "checkking (Claude)" --every 5` (background).
- Owner is direct and short in chat ("do 66, 72"). They want AAA quality, visible results, and agents that keep working without asking. Confirm before deleting anything on their PCs.

## Cards and where they stand (2026-10-28)

| Card | State | Next step |
|---|---|---|
| **#64** Obsidian chest AAA+ | Part 1 done: v2 textures (real steel reflectance, temper, wear, scratches, antique gold) + strap fix, **applied in game by the Vice** (hand-off #91). | Parts 2-3 (old collar/pauldrons poking through, belt tuck) need the knight FBX: steps for the Vice in `handoffs/obsidian-sovereign/CHEST_V2_TEXTURES_HANDOFF.md`. |
| **Obsidian set (owner wants all 11 pieces AAA)** | AAA: chest, shoulders L/R, gauntlets L/R. **New, modelled 10-28, not baked yet**: boots (sabatons, 14k tris/boot) and shins (greaves). Codex has WIP versions of all 11 in `assets/Codex/Obsidian-Sovereign`. | **First:** the bakes below. Then build: thighs (cuisses + poleyn), waist (fauld/tassets), forearms (vambraces), upper arms (rerebraces + couters), helmet, cape. Use Codex's bounds as the envelope (`Boots/source/bounds_codex.py`). |
| **#82** slime trails | M_JellyTrail_v2 built by the Vice; **BP_JellyTrailManager (ISM_Trail = v2) set but NOT SAVED** (owner was in Play). | Ask the editor driver to save + Play-check (see #92). |
| **#77** crossbow upgrade visuals | Phase 1: LV4 electric overlay material (hand-off filed). | Phase 2 (LV2 steel bands, LV3 gold parts, white-hot reveal, shot flare) waits on the **crossbow FBX export** asked from the Vice. |
| **#66** bag / skill-book pickup reveals | Phase 1: `handoffs/pickup-reveals-66/DESIGN.md` (sequence, hint copy, once-only) + `M_HintCard` UI material. | Phase 2 HUD wiring paste waits on the **BP_MinimapHUD export** (asked). |
| **#72** zombies in sync | Vice did per-zombie anim speed. Plan for part 2 on the card (start offset, anim variants, spawn spread). | Waits on exports: BP_ZombieVariety, zombie AnimBP, spawner, QuokkaVoid anim list (asked). |
| **#58** cannon break meshes | Claimed. | Waits on the **SM_FieldCannon_HD FBX export** (asked). |
| #65 / #67 / #84 | Owner says these are **Codex's**, not yours. Asked Codex to claim them. | Leave them. |
| #74 potions | Codex is shortlisting. | Leave it. |
| Towers (#9 / #85) | Owner: leave for now. | Leave it. |

Exports go to `handoffs/exports/checkking/` (pickup66/, zvariety72/, xbow/, cannon). The Vice was off until ~11:30 UTC on 10-28 (plan limit).

## Office things checkking added (10-28)

- Banner at the top of the office page with its link + Visit button (`banner` in `data.js`, render code in `index.html`).
- **3D ASSETS → "checkking · AAA" folder** (`assets/checkking/library.js`): the ready assets with status, renders, files and how to use them. **Update its `ITEMS` list when an asset changes status** (e.g. boots/shins when baked, shoulders/gauntlets when re-textured).

## Sources and pipeline (everything is in the repo now)

- `assets/checkking/Obsidian-Sovereign/<Piece>/source/`: procedural Blender 4.5 build scripts (`build_*.py`), staged 4K bake (`bake_staged.py` + `run_bake.ps1`: build r1 low + r3 high -> prep UVs -> BC/RG/MT/AO/Normal in 4 quarters each -> finish = textures + L/R FBX), renders. Shared libs: `Chest/source/chestlib.py` (patch/tube/ribbon/rivet, true-length UVs), `Gauntlets/source/gauntletlib.py` (Axial surfaces of revolution), `Chest/source/materials.py` (**v2** procedural PBR: steel/gold/leather/buckle/etch).
- **Paths are hard-coded to `C:\Users\hossam.rabea\checkking-work\<piece>`** (the old PC). On a new machine: copy each `source/` folder to a work folder, fix `D = r'...'` in `bake_staged.py`, `Set-Location` in `run_bake.ps1`, and the `sys.path` lines that point at `...\chest` and `...\gauntlets`. Blender: `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe`.
- `assets/checkking/tools/`: `remat_v2.py` (swap v2 materials into an existing bake_ready.blend, geometry/UVs untouched), `fix_straps.py` (paint leather + flat normal into texels sampled by zero-area-UV faces, UVs unchanged), `uvcmp.py`, `texstat.py`, `sbs.py` (before/after), numpy previews of the slime / electric / hint-card shaders.

## Bakes: running on the old PC since 2026-10-28 ~12:25 (check before you redo anything)

After the owner freed space (12.8 GB), `tools/bake_chain_detached.ps1` was started on the old PC as a background task of the old session, in this order: **boots -> shins -> shoulders v2 -> gauntlets v2**, ~1 h each. Every finished piece is **committed + pushed by itself** (`checkking (auto-bake): ...`) and announced in the cafeteria. So first: `git pull` and `git log --oneline --grep "auto-bake"`. Whatever has landed, don't redo. Whatever hasn't (the old PC got switched off, or the old session closed), bake it yourself with the steps below.

### If you have to bake yourself

The old PC ran out of disk (C: at 0 MB) twice, so **nothing below has been baked**; all jobs there are stopped. Bake on the main laptop (needs Blender 4.5 and **~1.5 GB free per piece** for the raw EXR quarters; delete `tex/raw_*.exr` after each finish):

1. **Boots** (`Boots/source`, modelled + checked: 14k tris/boot, UVs OK) and **Shins** (`Shins/source`, greave, checked against the boot): copy `source/` to a short work path, fix the hard-coded paths (see above), run `run_bake.ps1` (builds r1 + r3, prep, bakes, finish -> textures + L/R FBX), render with `render_boot.py` / `render_shin.py` (`-- <prefix> 64 1400 keep`).
2. **Shoulders + gauntlets v2 textures** (match the chest's v2 look): their `bake_ready.blend` isn't in the repo, so rebuild from `source/` with the v2 `materials.py` (run_bake.ps1 does build + prep + bake). **Check the UVs match the shipped FBX** (`tools/uvcmp.py`, max diff 0.0); if they don't, ship the new FBX too (they're not fitted in game yet, so that's allowed).
3. Copy textures (BaseColor, ORM, Normal_DirectX) + FBX + renders into `assets/checkking/Obsidian-Sovereign/<Piece>/`, write README + UE import script (copy the gauntlets' one), add the piece to `assets/checkking/library.js`, hand it off, post screenshots.

`tools/bake_chain_detached.ps1` automates 1-3 but has the old PC's paths baked in; adapt it or run the steps by hand. (Starting it detached from a Claude session is blocked as persistence: run it as a normal background task, or ask the owner to start it in a terminal.)

## Lessons (save yourself the trouble)

- **UE 5.3 editor Python:** `MaterialExpressionPerInstanceCustomData` has no `default_value`; HLSL loop counters in Custom nodes leak into the node scope (use unique names like `ki`, `cg`); call `texture.modify()` before changing texture settings on a re-import; `__file__` is not always set by `py "<file>"`: give scripts a `REPO` fallback.
- The fitted in-game chest (`SK_ObsidianSovereign_Chest`) keeps the shipped UV layout: re-bakes must not change UVs (check with `uvcmp.py`, max diff must be 0.0). Never re-run `import_chest_ue.py`.
- Blender can't open paths over 260 chars (the session scratch folders are long): copy files to a short path first.
- **Disk:** the old PC's C: filled up to 0 MB once (bake raw EXRs are ~1 GB per piece). Bakes now delete their raw EXRs at the end. Watch free space.
- Collapsed (zero-area) UVs on thin strips sample stray texels and break tangents -> grey/white glitches. Thin solidify rims are fine; whole strips are not.
- Steel looked "matte black plastic" in UE because BaseColor was ~0.02 linear with almost no variation; v2 is ~0.037 with ~3x the spread and metallic 0.85 / 1.0 on worn edges.
