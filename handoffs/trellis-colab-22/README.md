# TRELLIS on paid Colab — task #22 research result

Checked 2026-10-28. Research complete; no Colab GPU session or model inference was run. The supplied notebook is a preflight diagnostic, not a tested installer or generator.

## Decision
Use TRELLIS.2 as a candidate generator for isolated props and rough asset variants, with an A100-class paid Colab runtime if one is available. Keep measured architecture, traversable collision and skeletal fitting in the authored Blender/Unreal pipeline. Do not replace the measured tower with an image-generated mesh.

The owner's local MX570 A was measured at 2 GB VRAM. That laptop is not a suitable inference target for either documented model configuration. It can still inspect and refine exported models in Blender.

## Verified requirements
| Option | Official requirement | Implication for this project |
|---|---|---|
| TRELLIS original | Linux-tested; NVIDIA GPU with at least 16 GB; multiple output representations including meshes | A fallback experiment, not guaranteed on a particular 16 GB Colab runtime |
| TRELLIS.2 | Linux-tested; NVIDIA GPU with at least 24 GB; verified upstream on A100/H100; CUDA Toolkit 12.4 recommended | Prefer A100 for the first compatibility trial; L4 is an unverified candidate, not a promised working configuration |
| Paid Colab | Resource availability and usage limits vary; purchased service does not guarantee a particular GPU | Check the allocated runtime before installing or loading weights |

Sources: [original TRELLIS](https://github.com/microsoft/TRELLIS), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2), [Colab FAQ](https://research.google.com/colaboratory/faq.html).

TRELLIS.2 takes a single image and produces a mesh with PBR attributes. Its support for open/non-manifold structures is not a watertightness guarantee. The model card lists MIT; retain upstream notices for redistributed code and check rights to reference images separately. [Model card](https://huggingface.co/microsoft/TRELLIS.2-4B), [code license](https://github.com/microsoft/TRELLIS.2/blob/main/LICENSE).

## Reproducible starting point
Verified repository revision: `75fbf0183001ed9876c8dbb35de6b68552ee08bd`.

[Setup at that revision](https://github.com/microsoft/TRELLIS.2/blob/75fbf0183001ed9876c8dbb35de6b68552ee08bd/setup.sh) creates a Python 3.10 environment with PyTorch 2.6.0/CUDA 12.4 when its new-environment option is used. It also compiles CUDA extensions. Do not paste this blindly into an arbitrary Colab Python environment: verify Python, CUDA compiler, driver and package compatibility first. Some subordinate repositories/dependencies are not pinned by the upstream setup; record their resolved revisions and a package lock after a successful trial.

The [official example](https://github.com/microsoft/TRELLIS.2/blob/75fbf0183001ed9876c8dbb35de6b68552ee08bd/example.py) loads `microsoft/TRELLIS.2-4B` and exports GLB with a one-million-face target and 4096 texture size. Those example settings are not a game budget. Its output also uses a WebP extension; inspect material/texture support in the actual target importer before delivery.

## What to make first — project-specific recommendation
Start with one original low-risk static prop, such as a stone relic or barracks storage prop. Use one clean three-quarter reference image of a single item. Avoid a multi-view design sheet as a single generation input. Capture a back view during review: the hidden side was inferred, not measured.

Do not use the first trial for the tower's walk-through interior, cannon destruction states, fitted armor, or anything needing exact contact dimensions. Those tasks require measured geometry and consistent topology across states.

## Trial procedure for the authorized operator
1. Open `TRELLIS_Colab_Preflight.ipynb`. Merely running a paid GPU runtime may consume units; obtain an explicit trial budget before starting it. This research did not start one.
2. Run its read-only checks and save the JSON receipt. It collects GPU model/memory, software versions and available disk space; no secrets, account identifiers or GPU serials.
3. If the GPU is below the documented requirement, stop the runtime rather than attempting an unplanned low-VRAM workaround. A hardware candidate result is not a compatibility pass.
4. In an isolated runtime, follow the pinned upstream setup. Capture build logs and import checks. Do not alter the game PC's Python/CUDA installation.
5. Generate one approved reference using recorded seed and settings. Record wall time, peak allocated VRAM, compute-unit usage and output hashes. Upstream H100 speed numbers are not a Colab completion estimate.
6. Download source image, GLB, receipt and environment information before ending the runtime. Keep private/licensed inputs in private storage.

## Acceptance after generation
Inspect in Blender: scale/orientation, silhouette from all sides, disconnected fragments, winding, degenerate geometry, surface intersections, UVs and texture channels. Author a sensible low-poly/LOD representation, collision and pivot for the intended prop. Bake or repair materials where required. Reimport into the actual Unreal version and inspect at gameplay distance. Compare against the same asset budget used by surrounding props; a successful generator run is not AAA acceptance.

## Delivered / not delivered
Delivered: source-verified feasibility, pinned upstream entry points, project-specific asset suitability assessment, read-only preflight notebook, and a test/acceptance procedure.
Not delivered: working Colab install claim, inference benchmark, generated asset, runtime bill estimate, or Unreal-ready model. Those need a separately authorized and measured trial.
