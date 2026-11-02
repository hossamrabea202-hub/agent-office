# i5 #77 LV4 look without PIE: set XbowUp on the EDITOR world's MPC instance only (the asset's default is not touched,
# nothing saved), then render the TradeShowcase crossbows with capture_shot_ue.py.
#   py ".../xbow77_editor_ue.py" <noble> <sovereign> <out.png>     e.g. 4 4 C:/.../pie77_lv4.png ; 0 0 to put it back
import sys, unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
reg = unreal.AssetRegistryHelpers.get_asset_registry()
mpc = next(ad.get_asset() for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialParameterCollection'))
           if any(str(v.get_editor_property('parameter_name')) == 'XbowUp' for v in ad.get_asset().get_editor_property('vector_parameters')))
ML = getattr(unreal, 'KismetMaterialLibrary', None) or unreal.MaterialLibrary
ML.set_vector_parameter_value(w, mpc, 'XbowUp', unreal.LinearColor(float(sys.argv[1]), float(sys.argv[2]), 0, 0))
print(mpc.get_name(), 'XbowUp (editor world) =', ML.get_vector_parameter_value(w, mpc, 'XbowUp'))
sc = next((x for x in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if 'TradeShowcase' in x.get_class().get_name()), None)
if sc and len(sys.argv) > 3:
    o, e = sc.get_actor_bounds(False); f = sc.get_actor_forward_vector(); r = sc.get_actor_right_vector()
    xb = [c for c in sc.get_components_by_class(unreal.MeshComponent) if c.get_editor_property('overlay_material') and 'XbowElectric' in c.get_editor_property('overlay_material').get_name() and c.is_visible()]
    if xb: o = xb[0].get_world_location(); print('aim at', xb[0].get_name(), [c.get_name() for c in xb])
    dist = float(sys.argv[4]) if len(sys.argv) > 4 else 220.0
    cam = o + f * dist + r * (dist * 0.15) + unreal.Vector(0, 0, dist * 0.1)
    print('showcase', sc.get_actor_label(), 'center', o, 'extent', e)
    sys.argv = ['capture_shot_ue.py', sys.argv[3]] + ['%.1f' % v for v in (cam.x, cam.y, cam.z, o.x, o.y, o.z)] + ['45']
    exec(compile(open('C:/Users/hossam.rabea/agent-office/handoffs/laptop-i5/capture_shot_ue.py', encoding='utf-8').read(), 'capture_shot_ue.py', 'exec'), {'__name__': '__main__'})
