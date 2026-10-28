"""Offline failure-path checks. These do not validate Unreal API execution."""
import importlib.util
import pathlib
import tempfile
import types
import unittest

SPEC = importlib.util.spec_from_file_location("collector", pathlib.Path(__file__).with_name("collect_sources_ue.py"))
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


class Tests(unittest.TestCase):
    def test_missing_property_is_recorded(self):
        def read(name):
            if name == "present":
                return 3
            raise AttributeError(name)
        result = collector.property_record(types.SimpleNamespace(get_editor_property=read), ["present", "absent"])
        self.assertEqual(result["values"], {"present": 3})
        self.assertIn("absent", result["unavailable"])

    def test_failed_collection_still_writes_explicit_partial_report(self):
        with tempfile.TemporaryDirectory() as directory:
            def fail():
                raise RuntimeError("registry unavailable")
            unreal = types.SimpleNamespace(
                Paths=types.SimpleNamespace(project_saved_dir=lambda: directory),
                SystemLibrary=types.SimpleNamespace(get_engine_version=lambda: "offline fixture"),
                AssetRegistryHelpers=types.SimpleNamespace(get_asset_registry=fail),
                log=lambda message: None,
            )
            first, report = collector.main(unreal)
            second, _ = collector.main(unreal)
            self.assertNotEqual(first, second)
            self.assertEqual(report["status"], "partial")
            self.assertFalse(report["project_assets_modified"])
            self.assertFalse(report["export_fbx_requested"])
            self.assertIn("registry unavailable", report["errors"][0]["collection"])
            self.assertTrue(pathlib.Path(first, "inventory.json").is_file())

    def test_exporter_success_without_bytes_is_rejected(self):
        class FakeObject:
            def set_editor_property(self, name, value):
                pass
            def get_editor_property(self, name):
                return []
        unreal = types.SimpleNamespace(FbxExportOption=FakeObject, AssetExportTask=FakeObject,
            SkeletalMeshExporterFBX=FakeObject,
            Exporter=types.SimpleNamespace(run_asset_export_task=lambda task: True))
        mesh = types.SimpleNamespace(get_name=lambda: "missing")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "FBX export failed"):
                collector.export_fbx(unreal, mesh, directory)


if __name__ == "__main__":
    unittest.main(verbosity=2)

