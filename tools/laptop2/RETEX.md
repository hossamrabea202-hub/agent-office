# retex.py: photoreal retexture of an existing game prop (knowledge-base standard)

For props we didn't build ourselves (licensed meshes, older assets): it keeps the prop's own design (BaseColor layout,
normal map) and rebuilds the surface physically. Steps:
1. Classify texels into metal, gold, wood and other, using the original BaseColor and metallic.
2. Recalibrate into PBR ranges: non-metal 30–240 sRGB, bare metal at calibrated reflectance, metallic strictly 0/1.
3. Render the original's dark metal as a patchy non-metal oxide over bright metal, rubbed bare at the edges.
4. Add the wear: wood grain, scratches, cavity grime, up-facing dust and 3-scale roughness.
5. Bake new BaseColor, ORM and Normal (the original normal plus micro detail) on the same UVs.

```
blender -b --factory-startup -P retex.py -- <mesh.fbx> <BaseColor> <ORM|-> <Normal_OpenGL|-> <out_dir> [4096] [grain axis x|y|z]
```

It needs `matlib.py` and `shieldmat.py` next to it (copies are in `retex_lib/`). Run `pbr_check.py` on the output.
Licensed inputs and outputs stay in private folders, never in this repo.
