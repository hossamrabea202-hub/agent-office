# Shop v2: fresh shop copy SM_Emberoath_Kit2 at build scale 0.014 (~95 cm overall) and point BPC_WeaponKit's Emberoath row
# at it. (A second build-scale change on SM_Emberoath_Kit did not rebuild; a fresh duplicate's first change does.)
import unreal
EAL = unreal.EditorAssetLibrary; sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
K2 = '/Game/CastleDefender/Weapons/Emberoath/SM_Emberoath_Kit2'
if not EAL.does_asset_exist(K2): EAL.duplicate_asset('/Game/CastleDefender/Weapons/Emberoath/SM_Emberoath', K2)
km = unreal.load_asset(K2)
bs = sme.get_lod_build_settings(km, 0); bs.set_editor_property('build_scale3d', unreal.Vector(0.014, 0.014, 0.014)); sme.set_lod_build_settings(km, 0, bs)
EAL.save_asset(K2, only_if_is_dirty=False)
P = '/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit'
bp = unreal.load_asset(P); cdo = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(bp))
names = list(cdo.get_editor_property('Names')); meshes = list(cdo.get_editor_property('Meshes'))
meshes[names.index('Emberoath')] = km; cdo.set_editor_property('Meshes', meshes)
unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_asset(P, only_if_is_dirty=False)
b = km.get_bounding_box(); unreal.log('i5 kit2: z %.3f..%.3f, row %d -> %s' % (b.min.z, b.max.z, names.index('Emberoath'), km.get_name()))
