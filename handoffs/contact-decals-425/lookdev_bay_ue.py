# #425 calibrated lookdev bay (i5): a TEMPORARY test corner 200 m above the castle, under the cloud layer, deleted again by "clean".
#   py lookdev_bay_ue.py spawn            castle-wall slab (MI_Castle_StoneWall_World, the real wall), SM_IronTorch copy,
#                                         1800 K point light (INDUSTRY_SECRETS rule 6), 0.18 grey ball; all tagged LD425
#   py lookdev_bay_ue.py cards            + the #425 stain cards on the bay torch (place_contact425_ue.spawn)
#   py lookdev_bay_ue.py shot <name>      locked-exposure render (lookdev_cap, EV 1.5) -> contact-decals-425/ld_<name>.png
#   py lookdev_bay_ue.py clean            deletes every LD425 / CD425 actor of the bay
import sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425/'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
O = unreal.Vector(3000, 3000, 20000)
mode = sys.argv[1]


def tag(a, label):
    a.tags = [unreal.Name('LD425')]; a.set_folder_path('LD425_Lookdev'); a.set_actor_label(label); return a


def mesh(path, at, rot, scale, mat, label):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, at, rot)
    a.static_mesh_component.set_static_mesh(unreal.load_asset(path))
    if mat: a.static_mesh_component.set_material(0, mat)
    a.set_actor_scale3d(scale); return tag(a, label)


def grey():
    p = '/Game/CastleDefender/Environment/ContactDecals425/M_LD_Grey18_425'
    if EAL.does_asset_exist(p): return unreal.load_asset(p)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_LD_Grey18_425', p.rsplit('/', 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, 0); c.set_editor_property('constant', unreal.LinearColor(0.18, 0.18, 0.18, 1))
    r = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 200); r.set_editor_property('r', 0.5)
    MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR); MEL.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m); EAL.save_asset(p); return m


def bay_torch():
    return next(x for x in EAS.get_all_level_actors() if x.get_actor_label() == 'LD425_Torch')


if mode == 'spawn':
    wall = unreal.load_asset('/Game/CastleDefender/Environment/Castle/MI_Castle_StoneWall_World') if EAL.does_asset_exist('/Game/CastleDefender/Environment/Castle/MI_Castle_StoneWall_World') else None
    if wall is None:
        src = next(x for x in EAS.get_all_level_actors() if x.get_actor_label() == 'SM_Cube_Nanite_12')
        wall = src.static_mesh_component.get_material(0)
    mesh('/Engine/BasicShapes/Cube', O + unreal.Vector(50, 0, 150), unreal.Rotator(0, 0, 0), unreal.Vector(1.0, 4.0, 4.0), wall, 'LD425_Wall')      # face at x = 0
    src_t = next(x for x in EAS.get_all_level_actors() if x.get_actor_label() == 'WallTorch_Iron_15')
    t = EAS.duplicate_actor(src_t); t.set_actor_location(O + unreal.Vector(0, 0, 140) + (src_t.get_actor_location() - src_t.get_actor_location()), False, False)
    t.set_actor_rotation(src_t.get_actor_rotation(), False); tag(t, 'LD425_Torch')
    # put the torch's back on the wall face (x = 0): shift by its bounds
    o, e = t.get_actor_bounds(False); t.set_actor_location(t.get_actor_location() + unreal.Vector(-(o.x + e.x) + O.x, 0, 0), False, False)
    lt = tag(EAS.spawn_actor_from_class(unreal.PointLight, O + unreal.Vector(-18, 0, 185), unreal.Rotator(0, 0, 0)), 'LD425_TorchLight')
    lc = lt.point_light_component
    lc.set_editor_property('use_temperature', True); lc.set_editor_property('temperature', 1800.0)
    lc.set_intensity(12.0); lc.set_attenuation_radius(900.0); lc.set_editor_property('source_radius', 4.0)
    mesh('/Engine/BasicShapes/Sphere', O + unreal.Vector(-60, 70, 40), unreal.Rotator(0, 0, 0), unreal.Vector(0.25, 0.25, 0.25), grey(), 'LD425_Grey18')
    print('bay spawned at', O, 'torch bounds', t.get_actor_bounds(False), 'wall', [x.get_actor_bounds(False) for x in EAS.get_all_level_actors() if x.get_actor_label() == 'LD425_Wall'])
elif mode == 'cards':
    g = {'__name__': 'x'}; exec(open(H + 'place_contact425_ue.py', encoding='utf-8').read().split("if '--remove' in args")[0], g)
    t = bay_torch(); o, e, hit = g['wall_hit'](t)
    print('bay wall hit', hit and hit[0]); print('cards', len(g['spawn']((t, ('SM_IronTorch', 'Iron', True), o, e, hit, True))))
elif mode == 'shot':
    sys.path.insert(0, H[:-1]); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
    o, e = bay_torch().get_actor_bounds(False)
    lookdev_cap.shot(H + 'ld_%s.png' % sys.argv[2], o + unreal.Vector(-230, 70, 20), o + unreal.Vector(0, 0, 30), float(sys.argv[3]) if len(sys.argv) > 3 else 1.5, 55)
elif mode == 'clean':
    gone = [x for x in EAS.get_all_level_actors() if {'LD425', 'CD425'} & {str(t) for t in x.tags} and abs(x.get_actor_location().z - O.z) < 2000]
    for x in gone: EAS.destroy_actor(x)
    print('cleaned', len(gone))
