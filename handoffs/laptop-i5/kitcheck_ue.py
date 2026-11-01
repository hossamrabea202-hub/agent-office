import unreal
km = unreal.load_asset('/Game/CastleDefender/Weapons/Emberoath/SM_Emberoath_Kit'); sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
b = km.get_bounding_box(); bs = sme.get_lod_build_settings(km, 0)
unreal.log('i5 kitcheck: z %.3f..%.3f build_scale %s' % (b.min.z, b.max.z, bs.get_editor_property('build_scale3d')))
