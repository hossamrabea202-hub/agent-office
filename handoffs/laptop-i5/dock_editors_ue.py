# i5 helper: open asset editors as tabs in the main window (floating editor windows stopped taking input on i5, 2026-11-01).
import unreal
s = unreal.get_default_object(unreal.EditorStyleSettings)
old = s.get_editor_property('asset_editor_open_location')
s.set_editor_property('asset_editor_open_location', unreal.AssetEditorOpenLocation.MAIN_WINDOW)
unreal.log('i5 dock: asset_editor_open_location %s -> %s' % (old, s.get_editor_property('asset_editor_open_location')))
