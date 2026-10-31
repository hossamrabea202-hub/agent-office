# #376 Realm vision: the world looks different inside the bubble, whatever its shape

By `adjustedfilm (Claude)`, 2026-10-31 late. Built from the Master's spec on #376, after the owner reshaped the bubble
for the 3rd time. It is now tall and organic and wraps around the tentacle, so there is **no sphere or capsule**: the
inside test runs against the **real bubble mesh**. It keeps working after any future reshape, with no re-fit.

## How it works

- `BP_RealmVision` is one actor with an **unbound** PostProcess `Vision` (priority 5) that starts at weight 0.
- Every 0.05 s it checks whether the **camera** is inside the bubble:
  1. If the camera is more than 2 m outside the bubble's bounds, it is outside, and no traces run.
  2. Otherwise it fires 3 rays from the camera: up, forward and left. Each ray runs a Component Line Trace (complex)
     against the bubble mesh only. It steps past every hit, up to 8 hits each way, outward and then back inward, so it
     works with one-sided or two-sided collision. `TwoSided` is set by `--place` from a real trace test.
  3. An odd number of crossings means inside. The majority of the 3 rays decides, so one fold of the membrane can't
     fool it, and the tentacle fold still counts as inside.
- The look **fades** in and out in about 0.6 s (`FadeSpeed` 5). It **pulses** with the breathing: the weight dips up
  to 8 % (`BreathAmt`) at `BreathHz`.
- If the bubble is hidden or removed (the realm collapse in #284), the look fades out.
- The bubble's mesh, material and transform are only **read**. No decal is touched.

**Inside look (the Master's start values):** saturation 0.78/0.86/0.80, contrast 1.12, gain 0.92/1.04/0.94,
gamma 0.97/1.0/1.02, tint 0.86/1.0/0.88, chromatic fringe 1.6, vignette 0.75, bloom 1.6, grain 0.25, exposure −0.35.

**Decision: where the owner tunes it.** The look values live on `Realm_Vision → Vision → Post Process Settings` in
Details. That is the same panel as any post-process volume, it is per instance, and it can be tuned live in PIE.
`FadeSpeed`, `BreathHz`, `BreathAmt` and `TwoSided` are instance-editable variables (category "Realm Vision").
Copying 10 look values into the component every tick would add nodes and give nothing more.

## Steps (Master: paste only, about 10 minutes)

1. `py "<repo>/handoffs/realm-vision-376/setup_realmvision376_ue.py" --check`. This is read-only. Push
   `realmvision376_check.txt`. It shows:
   - the bubble mesh and its collision complexity;
   - the two-sided trace test;
   - the material's scalars, so I can match `BreathHz` to the real breathing.
   - **If the test says "no hit from above (complex collision missing?)", stop and tell me on #376.** The bubble's
     collision is the owner's asset, so I won't change it without asking.
2. `py ".../setup_realmvision376_ue.py" --dry-run`, then run it without `--dry-run`. This makes
   `/Game/CastleDefender/Gameplay/Realm/BP_RealmVision` with the PostProcess `Vision` and the look.
3. Open BP_RealmVision → My Blueprint. Paste the 8 lines of `VARIABLES_BPVar.txt` on the VARIABLES header, one at a
   time. Compile.
4. In the EventGraph, paste `BP_RealmVision_graph.txt` (379 nodes). Compile, then Save.
5. `py ".../setup_realmvision376_ue.py" --place --dry-run`, then run it with `--place` only. This places
   `Realm_Vision` (tag `laptop2_realm`), sets `Bubble` = Realm_Bubble_Owner and `TwoSided` from the test, and saves the
   level.

Pre-checked: `fix_impure.py` finds nothing to fix, and `applyall check` passes (**Validation: OK**, 379 nodes, 682 links,
48 traces chained). Not compiled yet, because that needs the editor.

## Checks (Play)

1. Walk the hero into the bubble. The look fades in over about half a second: greener, softer colours, a vignette, more
   bloom.
2. Stand still inside. The look breathes slightly.
3. Go into the fold around the tentacle. It is still "inside".
4. Walk out. The look fades back to normal.
5. Far from the bubble there is no effect and no cost (no traces run there).
6. Two minutes of Play: no "Accessed None" from BP_RealmVision.
7. Screenshot inside and outside with `tools/shot.js --card 376`.
- If the switch flickers at the membrane, raise `FadeSpeed` down to 3 (slower).
- If it says inside when you are outside (or the other way round), flip `TwoSided` on Realm_Vision and tell me on #376.
