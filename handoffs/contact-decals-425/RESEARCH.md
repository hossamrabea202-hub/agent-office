# #425 Contact stains under wall-mounted props: research (i5, 2026-11-02)

Owner's order: "when any thing attached to stones on the castle walls it cant just pop out of stones it needs decals
batch on top of the area that the prop will hanged on."

## What real walls show (physical causes, knowledge base rule 3: every dirt layer has a cause)

| Layer | Cause | Where | Values used |
|---|---|---|---|
| Soot plume | Incomplete combustion; smoke rises with the hot plume and deposits carbon on cooler stone | Above the flame, densest just above it, widening and fading upward, streaked vertically by convection | Charcoal albedo 0.02-0.035 linear, roughness 0.95 (INDUSTRY_SECRETS 1.1: charcoal 0.02, R 1.0) |
| Contact grime | Hands, rain splash, soot settling on the ledge the bracket forms | A halo around the mounting plate, darkest at the contact line | Dry soil 0.15 darkened by soot, about 0.05 linear |
| Rust run-off | Water runs over the iron, carries iron oxide down (gravity) | Below the bracket only; uneven lengths per run | Rust 0.18 / 0.057 / 0.017 linear, metallic 0, roughness 1.0 (INDUSTRY_SECRETS 1.1) |
| Restraint | "Restraint over grunge" (playbook rule 3); wall streaks stay subtle (Lagarde, KNOWLEDGE_LOG rain notes) | | Max opacity 0.6-0.7 |

## How studios do it (sources)

- Grime in contact areas is placed where it is physically logical (corners, contact points), with decals tying the scene
  together; vertex paint or mask blends are the alternative
  ([80.lv, Silent Hill environment](https://80.lv/articles/building-scary-silent-hill-environment),
  [Unreal forum, gritty edges](https://forums.unrealengine.com/t/ao-is-cool-but-how-to-get-gritty-edges/17820)).
- UE DBuffer decals are the standard tool for local dirt on top of a base surface
  ([Epic, decal materials](https://dev.epicgames.com/documentation/ja-jp/unreal-engine/decal-materials-in-unreal-engine));
  overlapping DBuffer decals don't blend (INDUSTRY_SECRETS 4.2).
- Soot/leak decals fade to transparent at the edges so the square never shows on a wall
  ([Fab soot & leak decal pack](https://www.fab.com/listings/823bc036-df2a-4f6f-a644-bab8eac213b4)).
- No published AAA breakdown describes "soot above torches, grime under brackets" as a named workflow; the design above
  follows the physics and the office knowledge base.

## Finding that changed the plan

About half of the castle walls behind the props (30 of 58 props; Castle_*Curtain, GateTowers, KeepTurret, DoorCuts, the
Nanite cubes) have **Receives Decals = off**. No decal (ours or the existing moss / crack decals) can land there, and that
flag is the owner's to change (2026-10-30 decal rule). So the batch uses **stain cards**: a thin unlit *Modulate* plane
0.4 cm off the wall with the same procedural masks, which multiplies the wall by stain/WallAlbedo. The DBuffer decal
versions are built too (M_ContactSoot425 / M_ContactMount425) for walls that do receive decals.
