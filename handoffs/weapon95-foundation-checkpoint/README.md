# Weapon upgrades #95 — foundation checkpoint

This is a source/research checkpoint, not finished weapon art or an installed gameplay feature.

Contains a pure-Python executable state specification, tests, four HLSL studies, a new-only Unreal material builder, neutral/lab textures, original analytic VFX cards and reproducible Blender/CPU-preview scripts. Electric effects use separate ribbons and physical coil/prong studies; no membrane overlay is applied to weapons.

## Run and inspect

`python -m unittest discover -s tests -v` from this folder runs the state specification tests. These do not compile Unreal or validate the current game's save adapter. `contract.json` names semantic tiers, elements and material bindings; raw game levels and save adapter are intentionally unmapped.

Master only: review `build_materials_ue.py`, then run with UE Python using `runpy.run_path` so `__file__` is defined. It creates only `/Game/Codex/Weapon95_Foundation_v1` and refuses an existing destination. No gameplay, currency, damage, ownership or save writes. Shader/import results remain untested in Unreal.

The portable checkpoint excludes rendered previews and the large hardware-study .blend; regenerate them with `tools/build_previews.py` and `tools/build_mesh_lab_blender.py` (Blender 4.5). Existing local previews are CPU/Blender studies, not in-game screenshots. The original effect cards are 2/4/4 triangles; procedural VFX cards do not require HP/LP surface baking. Physical hardware remains unfitted and requires production topology, UVs, bakes and attachment review before delivery.

## Current source and next work

Fresh Blueprint and mesh manifests arrived in #116 under `handoffs/exports/codex/weapon95/`, commit `2ffbe3842c3edc7026178216092bd16e0f770974`. The private FBX/TGA directory supplied there is not accessible on this host. Transfer those source files privately; do not publish licensed source meshes in the office.

Next: map the actual purchase/save transactions from fresh graphs; fit sword/Noble/Sovereign hardware and masks against private meshes; author production art; integrate per-weapon dynamic materials and effects; Master compiles and tests purchase, choice, equip, death and save/load behavior. Coordinate with #7/#77 before touching their effects. #95 stays open.

No engine compilation, import validation, gameplay integration, canonical game-asset package or AAA approval is claimed by this checkpoint.
