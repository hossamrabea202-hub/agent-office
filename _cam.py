import unreal, sys
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
p = {'up': (unreal.Vector(359-700, -2502-250, -95+250), unreal.Rotator(0, -15, 20)),
     'down': (unreal.Vector(-1000, -2401, -4950), unreal.Rotator(0, -5, 0)),
     'cham': (unreal.Vector(1200, -2401, -4900), unreal.Rotator(0, -5, 180))}[sys.argv[1]]
UES.set_level_viewport_camera_info(p[0], p[1])
