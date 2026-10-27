# Task 9 â€” enlarged round cannon tower

Status: design and reference acquisition. No fitted tower mesh or Unreal integration has been delivered yet.

## Owner requirements

- Use four existing square-tower footprints arranged 2 Ã— 2 as the area reference for one enlarged circular tower.
- Soldiers must walk through each tower to the adjoining walls freely, in both directions.
- Provide a cannon position on the upper deck.
- Use a production asset workflow with architectural reference, deliberate modular construction, materials, collision, LODs and measured validation.
- Preserve the current castle during development.

## Footprint interpretation

For an existing square footprint of side `s`, the reference area is `4sÂ²`. A circle of equal area has external diameter `4s / sqrt(pi)`, approximately `2.257s`. These are footprint measurements, not instructions to multiply the tower height. Final dimensions depend on the measured existing assets. Do not scale an existing tower actor fourfold in every axis.

The illustration is a generated explanatory model, not a photograph of the project or a buildable/fitted design. The illustrated one/two-tower options do not establish placement. Task #9 originally names two front tower replacements; final instance count and positions must be resolved against the actual castle layout before placement.

## Circulation proposal

1. A continuous floor at the existing wall-walk elevation connects the adjoining wall routes through the tower. Connection angles, floor heights and portal sizes come from the actual castle; do not assume the walls meet at 90 or 180 degrees.
2. Soldier routes work in both directions without a jump, closed door, cannon interaction, ledge step or stair detour. Doorway heads and turns accommodate the actual soldier capsule and navigation-agent settings.
3. A separate stair bay serves the cannon deck. Its entrance, supporting structure and landing stay outside the through-route.
4. Keep cannon placement, recoil/crew space, ammunition props and the roof stair landing clear of the soldier route and usable parapet circulation.
5. Size passages from measured actor capsules and intended crowd flow. Do not certify a width from a generic human mannequin. Test two-way traffic with actual soldiers, turns and groups, not just the hero.
6. Floors, portals and stair collision must preserve their openings. A single convex hull around the whole tower would obstruct the interior; collision needs an intentional modular decomposition.

## Development and integration boundary

Author assets separately under a new versioned name. The modeling PC does not edit the current castle. Obtain the current reference manifest and screenshots first. The Master Agent alone operates the Unreal editor under repository rules.

Before any proposed integration, the Master records the current level and affected actor paths/transforms and creates a recoverable project backup. Candidate placement is evaluated in a separately named duplicate level, with new asset/package names. The duplicate must include or isolate external actors and referenced sublevels appropriately; merely duplicating the persistent level is not proof that shared sublevel edits are isolated. Preserve the original tower actors, cannon setup, walls and dependencies. Any eventual live-level replacement needs an explicit reviewed integration step naming the exact affected actors; this document is not that approval.

## Acceptance gates

- Compare architectural proportions and masonry against real references and the project's existing castle palette; approval is visual as well as numeric.
- Verify measured dimensions, wall-port alignment and useful cannon/crew space.
- Inspect high/low meshes, silhouette and texel density. Use reusable stone materials and trim detail appropriately; create unique surfaces only where they contribute. Document triangle/material/texture budgets before final production.
- Inspect the exported mesh and collision independently; verify normals, UVs, material channels, light leaks, supported floors and portal openings.
- In the duplicate level, verify the actual soldier navigation mesh spans both wall connections and the interior floor. Test soldiers Aâ†’B and Bâ†’A simultaneously, the roof route, crowded turns and cannon operation.
- Check hero movement, visibility, camera and parapet collision. Verify existing wall routes and cannon behavior still work outside the candidate tower.
- Measure the candidate's rendering, collision and navigation costs against the same baseline scene and view; specify the target hardware/performance budget rather than claiming AAA from polygon count.
- Confirm original level/assets/actors are unchanged by the review work. Do not close task #9 until project-PC integration and acceptance results are recorded.

## Needed from the project PC

Select the existing front/corner towers, adjoining walls, wall walks/stairs, intended cannon and relevant navigation bounds, then run the supplied **read-only** inspection helper. It writes a timestamped JSON file under the project's Saved/CodexTower09 folder and does not export licensed meshes or save project assets. Add overview/front/side screenshots, deck and opening measurements, and soldier capsule/navigation settings. Keep licensed source content private.

The helper has been syntax-checked locally, not executed in Unreal. Its output is a reference inventory, not proof of connectivity or complete dependency isolation.

## Engine references

- [Epic UE 5.3 EditorActorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorActorSubsystem?application_version=5.3)
- [Epic UE 5.3 Actor API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Actor?application_version=5.3)
- [Epic UE 5.3 UnrealEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/UnrealEditorSubsystem?application_version=5.3)
- [Epic UE 5.3 navigation overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/basic-navigation-in-unreal-engine?application_version=5.3): navigation is generated from collision geometry; a visually open route alone is insufficient.

