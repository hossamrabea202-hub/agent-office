"""Read-only UE source inventory for #65/#67/#84; run only by editor operator.

Writes private diagnostic files under Saved/CodexDiagnostics, never saves or
modifies project assets. FBX export is opt-in below and goes to the same private
directory. Do not commit the output folder to the public office repository.
"""
import datetime
import hashlib
import json
import os

EXPORT_FBX = False
KNIGHT = "/Game/ShadowKight/Mesh/ShadowknightUE_SK"
BLUEPRINTS = [
    "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter",
    "/Game/CastleDefender/Characters/Knight/BP_SoldierSword",
    "/Game/CastleDefender/Characters/Knight/BP_SoldierXbow",
]


def path_of(obj):
    return obj.get_path_name() if obj is not None else None


def property_record(obj, names):
    values, unavailable = {}, {}
    for name in names:
        try:
            value = obj.get_editor_property(name)
            if hasattr(value, "get_path_name"):
                value = path_of(value)
            elif value is not None and not isinstance(value, (str, bool, int, float)):
                value = str(value)
            values[name] = value
        except Exception as exc:
            unavailable[name] = str(exc)
    return {"values": values, "unavailable": unavailable}


def parameter_inventory(unreal, material):
    lib = unreal.MaterialEditingLibrary
    result = {}
    is_instance = isinstance(material, unreal.MaterialInstanceConstant)
    for kind in ("scalar", "vector", "texture", "static_switch"):
        entries = []
        try:
            names = getattr(lib, "get_" + kind + "_parameter_names")(material)
            getter = "get_material_instance_" if is_instance else "get_material_default_"
            getter += kind + "_parameter_value"
            for name in names:
                entry = {"name": str(name)}
                try:
                    value = getattr(lib, getter)(material, name)
                    entry["value"] = path_of(value) if hasattr(value, "get_path_name") else str(value)
                except Exception as exc:
                    entry["error"] = str(exc)
                entries.append(entry)
            result[kind] = entries
        except Exception as exc:
            result[kind] = {"error": str(exc)}
    return result


def material_inventory(unreal, material):
    result = {"path": path_of(material), "class": material.get_class().get_name()}
    result["properties"] = property_record(material, ["parent", "blend_mode", "two_sided"])
    result["parameters"] = parameter_inventory(unreal, material)
    try:
        base = material.get_base_material()
        result["base_material"] = path_of(base)
        lib = unreal.MaterialEditingLibrary
        # Graph access differs between engine versions; report failure explicitly.
        if hasattr(lib, "get_material_expressions"):
            expressions = lib.get_material_expressions(base)
        else:
            expressions = base.get_editor_property("expressions")
        result["expressions"] = []
        for expression in expressions:
            class_name = expression.get_class().get_name()
            item = {"path": path_of(expression), "class": class_name}
            if class_name == "MaterialExpressionCustom":
                item["custom"] = property_record(expression, ["code", "description", "inputs"])
            result["expressions"].append(item)
    except Exception as exc:
        result["graph_error"] = str(exc)
    return result


def component_inventory(unreal, component):
    result = {"path": path_of(component), "class": component.get_class().get_name()}
    result["properties"] = property_record(component, [
        "skeletal_mesh", "skeletal_mesh_asset", "static_mesh", "relative_location",
        "relative_rotation", "relative_scale3d", "attach_socket_name", "anim_class",
        "animation_mode", "leader_pose_component", "physics_asset_override",
        "disable_cloth_simulation", "cloth_blend_weight", "override_materials",
    ])
    try:
        result["effective_materials"] = [path_of(m) for m in component.get_materials()]
    except Exception as exc:
        result["materials_error"] = str(exc)
    return result


def export_fbx(unreal, mesh, directory):
    filename = os.path.join(directory, mesh.get_name() + ".fbx")
    options = unreal.FbxExportOption()
    # Unsupported options abort the export, rather than silently change it.
    for name, value in {"ascii": False, "collision": False, "level_of_detail": False, "vertex_color": True,
                        "export_source_mesh": True, "export_morph_targets": True}.items():
        options.set_editor_property(name, value)
    task = unreal.AssetExportTask()
    for name, value in {"object": mesh, "filename": filename, "automated": True,
                        "prompt": False, "replace_identical": False, "selected": False,
                        "options": options, "exporter": unreal.SkeletalMeshExporterFBX()}.items():
        task.set_editor_property(name, value)
    success = bool(unreal.Exporter.run_asset_export_task(task))
    errors = [str(e) for e in task.get_editor_property("errors")]
    if not success or not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        raise RuntimeError("FBX export failed: " + repr(errors))
    with open(filename, "rb") as stream:
        digest = hashlib.sha256(stream.read()).hexdigest()
    return {"file": os.path.basename(filename), "bytes": os.path.getsize(filename),
            "sha256": digest, "exporter_errors": errors}


def main(unreal):
    # A unique private output directory prevents accidental overwrites.
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    directory = os.path.abspath(os.path.join(
        unreal.Paths.project_saved_dir(), "CodexDiagnostics", "helmet-capes-" + stamp))
    os.makedirs(directory, exist_ok=False)
    report = {"schema": 1, "utc": stamp, "engine": unreal.SystemLibrary.get_engine_version(),
              "project_assets_modified": False, "export_fbx_requested": EXPORT_FBX,
              "assets": [], "blueprint_defaults": [], "level_actors": [], "errors": [],
              "limitations": [
                  "CDO enumeration may omit Blueprint SCS/inherited components; inspect level instances too.",
                  "Cloth configuration/paint weights and physics body geometry need a separate native export.",
                  "Material graph access may be unavailable; provide graph text and custom HLSL in that case.",
                  "An inventory or FBX export is not a repaired mesh or a Play verification."]}
    try:
        assets = unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path("/Game", recursive=True)
        targets = {KNIGHT}
        for asset in assets:
            name = str(asset.asset_name).lower()
            if any(token in name for token in ("cape", "cloak", "helmet", "nohorn")):
                targets.add(str(asset.package_name))
        for asset_path in sorted(targets):
            try:
                obj = unreal.load_asset(asset_path)
                if obj is None:
                    raise RuntimeError("Asset not found")
                item = {"path": path_of(obj), "class": obj.get_class().get_name()}
                if isinstance(obj, unreal.SkeletalMesh):
                    item["properties"] = property_record(obj, ["skeleton", "physics_asset", "mesh_clothing_assets"])
                    item["materials"] = []
                    for index, slot in enumerate(obj.get_editor_property("materials")):
                        material = slot.get_editor_property("material_interface")
                        item["materials"].append({"index": index,
                            "slot": str(slot.get_editor_property("material_slot_name")),
                            "material": path_of(material)})
                        if material is not None:
                            item["materials"][-1]["inventory"] = material_inventory(unreal, material)
                    if EXPORT_FBX:
                        item["fbx"] = export_fbx(unreal, obj, directory)
                elif isinstance(obj, unreal.MaterialInterface):
                    item["material"] = material_inventory(unreal, obj)
                report["assets"].append(item)
            except Exception as exc:
                report["errors"].append({"asset": asset_path, "error": str(exc)})
        for blueprint in BLUEPRINTS:
            try:
                cls = unreal.EditorAssetLibrary.load_blueprint_class(blueprint)
                if cls is None:
                    raise RuntimeError("Blueprint class not found; supply the current path")
                cdo = unreal.get_default_object(cls)
                components = cdo.get_components_by_class(unreal.MeshComponent)
                report["blueprint_defaults"].append({"path": blueprint,
                    "components": [component_inventory(unreal, c) for c in components]})
            except Exception as exc:
                report["errors"].append({"blueprint": blueprint, "error": str(exc)})
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in subsystem.get_all_level_actors():
            name = actor.get_class().get_name()
            if any(token in name for token in ("ThirdPersonCharacter", "SoldierSword", "SoldierXbow")):
                report["level_actors"].append({"class": name, "path": path_of(actor),
                    "components": [component_inventory(unreal, c)
                                   for c in actor.get_components_by_class(unreal.MeshComponent)]})
    except Exception as exc:
        report["errors"].append({"collection": str(exc)})
    report["status"] = "partial" if report["errors"] else "inventory_collected_review_limitations"
    with open(os.path.join(directory, "inventory.json"), "x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    unreal.log("CODEX_HELMET_CAPES_INVENTORY " + directory + " status=" + report["status"])
    return directory, report


if __name__ == "__main__":
    import unreal
    main(unreal)

