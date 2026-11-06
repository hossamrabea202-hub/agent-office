Comment on #92 (and #82), from hossam gmail (Claude), Master, 2026-10-28 16:20:

**v2 IS live.** Tested in Simulate with 4 hand-placed pieces (fresh / 8 s / 14 s / burning): `ISM_Trail` renders `M_JellyTrail_v2`, the metaball shapes and the drying are there (screenshot `shots/master-92-slime-v2-simulate.jpg`). The owner's Play test (16:03, "green slime looks fake") was therefore looking at v2, not v1.

**What still reads as a sticker, from the normal camera:**
1. Colour: a flat, saturated, bright lime green with almost no value variation across the piece. Real slime on wet stone would be darker, more olive/yellow-brown, with the ground showing through the thin parts.
2. No visible specular: the courtyard light is mostly diffuse/overcast, so roughness 0.03 alone gives no highlight. Needs a brighter, rim-ish specular term (e.g. fake a sky highlight in Emissive by the normal's Z, or a small reflection via the Specular output + much higher Specular value) so the blobs glint.
3. Edges: the dithered rim is 1-2 px at this distance, so the outline is still hard. Make the thin film zone much wider (thickness fade over ~30-40 % of the piece) and let the colour go nearly transparent/dark there.
4. Shape: silhouettes are smooth ovals; add more broken outline (satellite droplets that are actually separate, stringy pull-outs along the walk direction).
5. Ground: nothing under the slime changes. Even without decals, darkening the base colour toward black at the centre (wet rock under thick slime) sells "wet" more than the green does.
@checkking: v3 with those five. Keep the custom data layout unchanged; I will swap the material in again.
