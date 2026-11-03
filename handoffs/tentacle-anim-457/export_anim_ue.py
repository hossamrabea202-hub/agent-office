# #457 (i5): read-only FBX export of the tentacle rig + 2 clips for analysis in Blender. Aborts in PIE.
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/tentacle-anim-457/src/'
R = '/Game/CastleDefender/Environment/Tentacles/Rig/'
sk = unreal.load_asset(R + 'SK_CorruptedTentacle_01')
print('bones', sk.get_editor_property('skeleton').get_name())
for n in ('SK_CorruptedTentacle_01_Anim_Ripple', 'SK_CorruptedTentacle_01_Anim_Ripple_Sway030'):
    a = unreal.load_asset(R + n)
    print(n, 'len', a.get_editor_property('sequence_length'), 'frames', a.get_editor_property('number_of_sampled_keys') if False else '')
    e = unreal.AssetExportTask(); e.object = a; e.filename = OUT + n + '.fbx'; e.automated = True; e.prompt = False; e.replace_identical = True
    e.exporter = unreal.AnimSequenceExporterFBX()
    o = unreal.FbxExportOption(); o.set_editor_property('export_preview_mesh', True); e.options = o
    print('  export', unreal.Exporter.run_asset_export_task(e))
