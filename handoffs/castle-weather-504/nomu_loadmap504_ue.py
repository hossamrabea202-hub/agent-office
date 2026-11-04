import unreal
# i5: purge the *_DEADPACKAGE leftovers of the join-time hot reloads first, then open the map (2026-11-02 crash fix).
unreal.SystemLibrary.collect_garbage()
print("load_level", unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/ThirdPerson/Maps/ThirdPersonMap"))
