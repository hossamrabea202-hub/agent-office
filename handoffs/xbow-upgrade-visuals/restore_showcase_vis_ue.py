# #77 cleanup (i5, 2026-11-01): a failed lookdev run hid TradeShowcase's item meshes in the level. Put every mesh
# component of the placed showcase back to its Blueprint template's visibility (the class default), report each.
import unreal
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
sc = [a for a in acts if a.get_class().get_name().startswith('BP_TradeShowcase')][0]
bp = unreal.load_asset('/Game/CastleDefender/UI/Trade/BP_TradeShowcase')
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
tmpl = {}
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    o = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
    if isinstance(o, unreal.SceneComponent): tmpl[o.get_name().replace('_GEN_VARIABLE', '')] = o.get_editor_property('visible')
for c in sc.get_components_by_class(unreal.MeshComponent):
    want = tmpl.get(c.get_name(), True)
    before = c.is_visible(); c.set_visibility(want)
    print('%-28s was %-5s -> %s' % (c.get_name(), before, want))
