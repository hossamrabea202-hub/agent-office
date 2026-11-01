# Save only the current level (i5 helper). Multi-User records it in the session.
import unreal
ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.log('i5 save_current_level: %s' % ok)
