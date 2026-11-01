# Shop v2: set SM_Emberoath_Kit's build scale (the shop copy only). 0.014 -> ~95 cm overall, arming-sword length.
import unreal
km = unreal.load_asset('/Game/CastleDefender/Weapons/Emberoath/SM_Emberoath_Kit'); sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
bs = sme.get_lod_build_settings(km, 0); bs.set_editor_property('build_scale3d', unreal.Vector(0.014, 0.014, 0.014)); sme.set_lod_build_settings(km, 0, bs)
unreal.EditorAssetLibrary.save_asset(km.get_path_name().split('.')[0], only_if_is_dirty=False)
b = b = km.get_bounding_box(); unreal.log('i5 kitscale: Emberoath_Kit z %.2f..%.2f' % (b.min.z, b.max.z))
