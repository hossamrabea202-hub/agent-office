# i5 #77: spawn a TEMPORARY BP_TradeShowcase far away (z 60000), report the crossbow overlays, render it at XbowUp=(4,4)
# in the editor world only, then destroy it and put XbowUp back to 0. Nothing saved.   arg: <out.png>
import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ML = getattr(unreal, 'KismetMaterialLibrary', None) or unreal.MaterialLibrary
mpc = unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree') if unreal.EditorAssetLibrary.does_asset_exist('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree') else None
if mpc is None:
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    mpc = next(ad.get_asset() for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialParameterCollection')) if ad.asset_name == 'MPC_SkillTree')
cls = unreal.EditorAssetLibrary.load_blueprint_class('/Game/CastleDefender/UI/Trade/BP_TradeShowcase')
a = EAS.spawn_actor_from_class(cls, unreal.Vector(0, 0, 60000), unreal.Rotator(0, 0, 0))
try:
    tgt = None
    for c in a.get_components_by_class(unreal.MeshComponent):
        ov = c.get_editor_property('overlay_material')
        if c.get_name() not in ('ItemXbow',): c.set_visibility(False)
        else: c.set_visibility(True)
        if c.get_name() in ('ItemXbow', 'ItemSov'): print('fresh', c.get_name(), ov.get_name() if ov else '-', c.is_visible()); tgt = tgt or (c if c.is_visible() else None)
    ML.set_vector_parameter_value(w, mpc, 'XbowUp', unreal.LinearColor(4, 4, 0, 0))
    if tgt and len(sys.argv) > 1:
        o = tgt.get_world_location(); f = a.get_actor_forward_vector(); r = a.get_actor_right_vector()
        cam = o + f * 120 + r * 18 + unreal.Vector(0, 0, 12)
        sys.argv = ['capture_shot_ue.py', sys.argv[1]] + ['%.1f' % v for v in (cam.x, cam.y, cam.z, o.x, o.y, o.z)] + ['40']
        exec(compile(open('C:/Users/hossam.rabea/agent-office/handoffs/laptop-i5/capture_shot_ue.py', encoding='utf-8').read(), 'capture_shot_ue.py', 'exec'), {'__name__': '__main__'})
finally:
    ML.set_vector_parameter_value(w, mpc, 'XbowUp', unreal.LinearColor(0, 0, 0, 0)); EAS.destroy_actor(a); print('temp showcase destroyed, XbowUp back to 0')
