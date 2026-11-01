# #397 Weapon kit, AAA polish: research (TGA, 2026-11-01)

The owner asked for AAA polish of the models, materials and textures of checkking's 25-weapon kit (`assets/checkking/Weapons`), following the office rules.

This note covers three things:
- what real forged steel, iron, ash, oak, leather and brass look like;
- what our knowledge base already says;
- the **recipe** that follows from both.

Each item is marked **[measured]**, **[KB]** (our knowledge base), **[maker]** (smiths' and makers' practice) or **[inference]**.

## 1. What the surfaces are, physically

### Blades (forged, then ground and polished)
- **Process:**
  - a blade was ground coarse after forging, then smoothed with finer and finer abrasives toward a mirror finish;
  - flats were hand-stoned to take out the grinding marks;
  - fullers were cleaned "to a fine satin";
  - **[maker / experimental archaeology]** — EXARC's reconstruction of a medieval polishing bench ([EXARC](https://exarc.net/ark:/88735/10484)), and a myArmoury maker thread ([myArmoury](https://myarmoury.com/talk/viewtopic.php?p=86260)).
- **Survivals:** surviving blades are mostly corroded, so the "new" finish is reconstructed. Hammer marks can remain visible under the polish ([Springer metallography study](https://link.springer.com/article/10.1007/S13632-024-01064-3), [AskHistorians](https://lr.ggtyler.dev/r/AskHistorians/comments/g4ozos/to_what_degree_could_ancientmedieval_smiths_reach)).
- **What this means for us:**
  - the flats are **satin**, with faint grind lines **along** the blade;
  - the edge bevel is a **separate, brighter band** (a secondary bevel, where the sharpening stone works);
  - fullers are satin and collect grime;
  - a dead-flat mirror reads as a modern replica.

### Axe, halberd and mace heads (forged, edge ground)
- Hand-forged heads keep **forge scale**: oxide that flakes off in patches, and flakes the hammer pressed in as shallow pits. The cutting edge alone is **ground and polished** ([Outdoors SE answer on forge scale](https://outdoors.codidact.com/posts/51054)).
- Makers sell exactly that look: "rustic forged finish, mirror on the very blade", "natural finish, hand-ground beveled edges, polished cutting edge", "black finish, polished edge" ([BeaverCraft](https://beavercrafttools.com/products/ax5_head-hand-forged-axe-head-with-leather-sheath), [Hoffman Blacksmithing via BladeHQ](https://www.bladehq.com/item--Hoffman-Blacksmithing-20-Wasatch--37117)) **[maker]**.
- **What this means for us:** **forge scale next to the polished edge.** This is the card's own ask. The scale is a dark **non-metal** oxide film, and the ground strip is bright metal, with a wavy grinding boundary between them.

### Hafts
- **Ash** is the usual polearm haft wood ([myArmoury](https://myarmoury.com/talk/viewtopic.20766.html), citing Waldman, *Hafted Weapons in Medieval and Renaissance Europe*).
- **Linseed oil darkens and yellows it over time** ([Roman Army Talk](https://www.romanarmytalk.com/rat/showthread.php?tid=15304), [AZB](https://forums.azbilliards.com/goto/post?id=3073890), [conservation list](https://cool.culturalheritage.org/byform/mailing-lists/cdl/2001/1103.html)). Surviving hafts look "darkish brown" **[maker]**.
- **What this means for us:**
  - oiled ash is **mid amber-brown**, not pale;
  - grain runs along the haft;
  - hand zones are **darker and smoother** (oil, sweat, polish);
  - the butt end is dirtier and rougher.

### Leather grips
- Wear is never uniform **[Polycount]**: avoid uniform wear, and keep the leather's value distinct from the wood next to it ([Polycount](https://polycount.com/discussion/comment/2316141)).
- **What this means for us:** a dark brown wrap with ridges where the turns overlap; darker and smoother where the palm sits; cracked and dry at the ends.

### Brass and bronze fittings
- **[KB]** brass ≈ 0.91, 0.78, 0.42 linear [UNVERIFIED stand-in for bronze].
- Polished high points, with tarnish (non-metal) in recesses.

## 2. Numbers we use (calibrated)
| Surface | Albedo | Roughness | Metal | Source |
|---|---|---|---|---|
| Ground and polished steel (blade flats) | 0.56, 0.565, 0.578 linear ≈ 198 sRGB | 0.16–0.30, streaked along the blade | 1 | iron F0 0.562/0.565/0.578 ([AMU course table](https://wp.faculty.wmi.amu.edu.pl/CGP2.pdf)); KB iron 0.53–0.58 [measured / KB] |
| Edge bevel (stoned) | 0.60 linear | 0.10–0.16 | 1 | polished metal 0.08–0.18 ([Tripo roughness guide](https://www.tripo3d.ai/blog/roughness-map)) [artist] |
| Satin fuller | 0.54 linear | 0.30–0.38 | 1 | brushed metal 0.25–0.40 ([same](https://www.tripo3d.ai/blog/roughness-map)) |
| Forge scale (Fe₃O₄ film) | ≈ 0.035–0.05 linear (50–62 sRGB), blue-black | 0.55–0.75 | **0** | KB dark dielectrics 35–50 sRGB [inference] |
| Rust in pits | sRGB 118, 68, 35 | 1.0 | **0** | KB [measured] |
| Forged iron fittings (guard, pommel, langets) | 0.50–0.54 linear | 0.30–0.55, hammered | 1, with scale patches 0 | KB iron; metallic only 0 / 1 |
| Oiled ash | sRGB ≈ 128, 96, 64 (hand zones ×0.8) | 0.55–0.68, hands 0.38 | 0 | KB wood 0.12–0.16 weathered, 0.35–0.42 fresh; oiled sits between [inference] |
| Oak | sRGB ≈ 100, 72, 50, open pores | 0.6–0.75 | 0 | KB |
| Leather grip | sRGB ≈ 66, 44, 30; sweat zone 46, 31, 22 | 0.65–0.75; palm 0.42 | 0 | KB black leather 35 sRGB floor |
| Brass | 0.91, 0.78, 0.42 linear ×0.95 | 0.22–0.35; tarnish 0.7 | 1 / tarnish 0 | KB |

The non-metal floor is 30 sRGB (KB §1.2). Metallic is strictly 0 or 1, and `pbr_check` is run on every texture.

## 3. The recipe (applied to the 5 most-seen weapons first)
Our rule numbers are in brackets.
1. **Real sections, real bevels (models).** Every blade gets a **secondary edge bevel**: a visible grind line about 3–4 mm from the edge, steeper than the flats. Fullers keep checkking's real groove. Axe and halberd heads get the same ground strip along the cutting edge.
2. **One steel, three finishes.** Ground flats (satin, grind streaks along the length), a stoned edge (brighter, smoother), and forge scale on forged bodies. The scale is non-metal, with a wavy boundary at the ground strip. [§1.1 values, rule 2 roughness carries realism]
3. **Wear has causes** [rule 3]:
   - **edges:** polish where they rub;
   - **cavities and junctions:** grime and rust (guard to blade, eye to haft, fuller bottom);
   - **ground end of polearms:** dirt;
   - **contact zones on grips and hafts:** darker, smoother, polished.
4. **Roughness is never flat** [rule 2]: grind streaks (stretched noise along the weapon), large smudges and scratch lines (rougher on flats, polished on the edge).
5. **Wood reads as wood:** grain bands along the haft, pore streaks, ray flecks on oak, oiled amber, hand polish, and a dirty butt.
6. **Leather reads as a wrap:** the wrap ridges stay in the geometry, plus sweat darkening and polish in the palm and dry, rough ends.
7. **Values first, then judge only under the locked grey ball** [rule 1]. Lookdev uses locked exposure, an 18 % grey ball and a chrome ball, and the *before* and *after* are rendered in the **same** rig.
8. **Texture budget (#260):** authored at 2K, shipped capped at 1K in UE. Normal BC5, ORM Masks.

## 4. Not found / open
- No public breakdown of a AAA studio's medieval weapon texturing (Warhorse / KCD) turned up. KCD's authenticity work is about combat and replicas ([PlayStation Blog](https://blog.playstation.com/?p=195878), [Royal Armouries × KCD2](https://royalarmouries.org/entertainment-and-ip/recent-projects/ign-x-kingdom-come-deliverance-ii)). The recipe above is built from makers' and conservators' sources, plus our KB.
- No measured albedo for forge scale or for aged oiled ash: these are inferences, to be checked in lookdev.
