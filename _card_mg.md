From: hossam gmail (Claude) — Master, by owner order (2026-10-31 07:33)
For: **laptop i5 / hossam gmail laptop2 (Claude) — or any free agent operator**. Claim it with `node tools/office.js claim <n>`.

## Owner verdict
The satchel and Book of Skills pickup reveals (#139 / #140, hand-off #231) look bad ("so ugly"). **#231 is cancelled: do not paste it.**
There is no owner video. Redesign the reveals to AAA standard.

## Why v1 fails
It's a 64-frame flipbook (8x8 atlas, 512 px per frame, 24 fps): soft and choppy, with a flat screen dim.

## Target (AAA item reveal, ~2 s, skippable)
1. **Real-time 3D item, not a flipbook.** Use the real satchel and book meshes in a UI showcase: an offscreen showcase stage + SceneCapture2D -> render target at 1024+, or a 3D widget. Light it with a warm key, a cool rim and a soft contact shadow, at locked exposure (realism KB).
2. **Choreography in 5 beats:**
   - anticipation: 0.12 s pull-back
   - reveal: 0.35 s, ease-out expo, with about 6 % overshoot and settle
   - peak: light burst, a small camera push and a short hit-stop
   - title: per-letter slide-in, 30–40 ms stagger, gold shine sweep
   - exit: 0.4 s fly into the HUD icon, with an icon pulse
3. **Background:** blur and darken the game behind it (a post-process blur / desaturate ramp, not a flat dim). Add gold dust particles and a soft bloom glow.
4. **Typography:** short gold title (Cinzel, already in the project) plus one how-to line; key hints as small key caps.
5. **Sound sync:** whoosh on the reveal, low hit on the peak, shimmer on the title.
6. Works while the game is paused. Any key or click skips it. It plays once per item. Then auto-open the tree / pack, as in v1.

## Rules
- AGENTS.md: realism KB + INDUSTRY_SECRETS §2 (lighting/camera) and §3 (motion).
- **UE 5.3 Python has NO** `BlueprintEditorLibrary.get_basic_type_by_name / get_array_type / get_struct_type / get_object_reference_type`, and `Blueprint.new_variables` can't be read. Ship variables as **BPVar lines** (one per paste), and test your scripts against 5.3.
- Master only pastes: hand back pre-checked manifests (`fix_impure.py` + `applyall check`) with exact steps.
- Don't touch any decal or decal material.
- Before/after screenshots on this card.
