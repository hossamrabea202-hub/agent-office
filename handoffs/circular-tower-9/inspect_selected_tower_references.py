"""UE 5.3 reference inspection, for the Master Agent to review and run.

Reads selected actors only. Writes a new timestamped JSON in project Saved.
Does not spawn, delete, move, select, modify, import, export meshes, or save assets.
"""
import datetime
import json
from pathlib import Path
import unreal


def vector(value):
    return {"x": float(value.x), "y": float(value.y), "z": float(value.z)}


def rotation(value):
    return {"roll": float(value.roll), "pitch": float(value.pitch), "yaw": float(value.yaw)}


def property_or_note(obj, name):
    try:
        value = obj.get_editor_property(name)
        if isinstance(value, (bool, int, float, str)) or value is None:
            return value
        return str(value)
    except Exception as exc:
        return {"unavailable": str(exc)}


def component_record(comp):
    record = {"name": comp.get_name(), "class": comp.get_class().get_path_name()}
    if isinstance(comp, unreal.PrimitiveComponent):
        record["collision_enabled"] = str(comp.get_collision_enabled())
        record["collision_profile"] = str(comp.get_collision_profile_name())
        record["mobility"] = property_or_note(comp, "mobility")
    if isinstance(comp, unreal.SceneComponent):
        record["relative_location_cm"] = vector(comp.get_editor_property("relative_location"))
        record["relative_rotation_degrees"] = rotation(comp.get_editor_property("relative_rotation"))
        record["relative_scale"] = vector(comp.get_editor_property("relative_scale3d"))
    if isinstance(comp, unreal.StaticMeshComponent):
        mesh = comp.get_editor_property("static_mesh")
        record["static_mesh"] = mesh.get_path_name() if mesh else None
        if isinstance(comp, unreal.InstancedStaticMeshComponent):
            record["instance_count"] = int(comp.get_instance_count())
            record["note"] = "Individual instance transforms are not included. Request them if this component constructs the castle."
    if isinstance(comp, unreal.CapsuleComponent):
        record["capsule_radius_cm"] = property_or_note(comp, "capsule_radius")
        record["capsule_half_height_cm"] = property_or_note(comp, "capsule_half_height")
    return record


def actor_record(actor):
    origin, extent = actor.get_actor_bounds(False, True)
    record = {
        "label": actor.get_actor_label(),
        "path": actor.get_path_name(),
        "class": actor.get_class().get_path_name(),
        "location_cm": vector(actor.get_actor_location()),
        "rotation_degrees": rotation(actor.get_actor_rotation()),
        "scale": vector(actor.get_actor_scale3d()),
        "bounds_center_cm": vector(origin),
        "bounds_half_extent_cm": vector(extent),
        "components": [],
    }
    for comp in actor.get_components_by_class(unreal.ActorComponent):
        try:
            record["components"].append(component_record(comp))
        except Exception as exc:
            record["components"].append({"name": comp.get_name(), "inspection_error": str(exc)})
    return record


def main():
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors())
    if not actors:
        raise RuntimeError("Select the existing tower, adjacent walls/walkways/stairs and cannon reference actors first.")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    result = {
        "schema": "codex.tower09.reference-inventory.v1",
        "created_utc": timestamp.isoformat(),
        "editor_world": world.get_path_name() if world else None,
        "units": "centimeters; rotation fields explicitly named",
        "scope": "Selected actors only; no actor or asset mutation. Not a complete dependency, collision or navigation audit.",
        "actors": [actor_record(actor) for actor in actors],
        "manual_measurements_needed": [
            "Existing square tower outer footprint and desired retained height",
            "Wall-walk elevations, clear widths, connection angles and portal clearances",
            "Actual soldier/hero capsules and navigation-agent settings",
            "Cannon bounds, crew/recoil envelope and Blueprint placement dependencies",
            "Current level/sublevel/external-actor organization and reference screenshots",
        ],
    }
    folder = Path(unreal.Paths.project_saved_dir()) / "CodexTower09"
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / ("reference_manifest_" + timestamp.strftime("%Y%m%dT%H%M%S_%fZ") + ".json")
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    unreal.log("Tower #9 read-only reference inventory: " + str(output))


if __name__ == "__main__":
    main()

