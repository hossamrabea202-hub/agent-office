# i5 #77 Play check without the GUI: in the RUNNING PIE world only (nothing saved), read or set the XbowUp MPC value.
#   py ".../pie_xbow77_ue.py"            print XbowUp in the PIE world
#   py ".../pie_xbow77_ue.py" 4 4        set XbowUp = (4, 4) (Noble LV, Sovereign LV) in the PIE world
import sys, unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if not w: raise SystemExit('no PIE world: run pie_ue.py start first')
reg = unreal.AssetRegistryHelpers.get_asset_registry()
mpc = next(ad.get_asset() for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialParameterCollection'))
           if any(str(v.get_editor_property('parameter_name')) == 'XbowUp' for v in ad.get_asset().get_editor_property('vector_parameters')))
ML = getattr(unreal, 'KismetMaterialLibrary', None) or unreal.MaterialLibrary
if len(sys.argv) >= 3:
    ML.set_vector_parameter_value(w, mpc, 'XbowUp', unreal.LinearColor(float(sys.argv[1]), float(sys.argv[2]), 0, 0))
print(mpc.get_name(), 'XbowUp =', ML.get_vector_parameter_value(w, mpc, 'XbowUp'))
