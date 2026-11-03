# #301 W2 (i5, 2026-11-03): the 9 baked kit flights on i9's keep look. NEW assets only, old MIs untouched.
#   py stair_w2_ue.py assets [13 20 31]          import build451/SM_StairBaked451_N<n>_C.png (bake_color.py) as T_..._C and
#                                                make MI_StairBaked451_N<n>_W2: parent M_KeepEntrance_Baked (i9: baked BC/N/AO +
#                                                lime, moss, grime band, cracks, soil), scalars/vectors copied from the keep's
#                                                MI_CastleAshlar, BakedColor = _C, BakedNormal = _N, BakedAO = _M (R = AO). Saved.
#   py stair_w2_ue.py comp --only Stair279_03 --apply | --revert     per-actor override (live A/B only, nothing saved)
#   py stair_w2_ue.py mesh --dry-run | --apply | --revert             mesh slots 0+1 -> _W2 (or back to _Tread/_Body), saved
#   py stair_w2_ue.py where Stair279_03                              print the actor bounds (for the A/B camera)
import sys, unreal
A = sys.argv[1:]; mode = A[0]
BUILD = 'C:/Users/hossam.rabea/agent-office/handoffs/stairs-447/build451/'
DST = '/Game/CastleDefender/Environment/Castle/StairsBaked451'
PARENT = '/Game/CastleDefender/Environment/Castle/KeepEntrance/M_KeepEntrance_Baked'
LOOK = '/Game/CastleDefender/Environment/Castle/KeepMasonry/MI_CastleAshlar'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
NS = [int(x) for x in A[1:] if x.isdigit()] or [13, 20, 31]
ld = lambda n: unreal.load_asset(DST + '/' + n)

if mode == 'assets':
    par, look = unreal.load_asset(PARENT), unreal.load_asset(LOOK)
    print('parent textures', [str(x) for x in MEL.get_texture_parameter_names(par)])
    for n in NS:
        t = unreal.AssetImportTask(); t.filename = BUILD + 'SM_StairBaked451_N%d_C.png' % n; t.destination_path = DST
        t.destination_name = 'T_StairBaked451_N%d_C' % n; t.automated = True; t.replace_existing = True; t.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        tc = ld('T_StairBaked451_N%d_C' % n); tc.set_editor_property('srgb', True)
        name = 'MI_StairBaked451_N%d_W2' % n
        mi = ld(name) if EAL.does_asset_exist(DST + '/' + name) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, par)
        have_s, have_v = set(str(x) for x in MEL.get_scalar_parameter_names(par)), set(str(x) for x in MEL.get_vector_parameter_names(par))
        cs = [x for x in MEL.get_scalar_parameter_names(look) if str(x) in have_s]
        cv = [x for x in MEL.get_vector_parameter_names(look) if str(x) in have_v]
        for x in cs: MEL.set_material_instance_scalar_parameter_value(mi, x, MEL.get_material_instance_scalar_parameter_value(look, x))
        for x in cv: MEL.set_material_instance_vector_parameter_value(mi, x, MEL.get_material_instance_vector_parameter_value(look, x))
        for p, tex in (('BakedColor', tc), ('BakedNormal', ld('T_StairBaked451_N%d_N' % n)), ('BakedAO', ld('T_StairBaked451_N%d_M' % n))):
            MEL.set_material_instance_texture_parameter_value(mi, p, tex)   # returns False even when set: read back
            got = MEL.get_material_instance_texture_parameter_value(mi, p); print('  ', name, p, got.get_name() if got else None)
        MEL.update_material_instance(mi)
        for a in (tc, mi): EAL.save_loaded_asset(a)
        print('W2 OK', name, 'copied from keep look:', [str(x) for x in cs + cv])
    raise SystemExit

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if mode in ('comp', 'where'):
    only = (A[A.index('--only') + 1] if '--only' in A else A[1]).split(',')
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() not in only: continue
        c = a.get_component_by_class(unreal.StaticMeshComponent); m = c.get_editor_property('static_mesh')
        if mode == 'where':
            o, e = a.get_actor_bounds(False); print('WHERE', a.get_actor_label(), m.get_name(), 'origin', o, 'extent', e); continue
        n = m.get_name().split('_N')[-1]
        for i in (0, 1): c.set_material(i, ld('MI_StairBaked451_N%s_W2' % n) if '--apply' in A else None)
        print('COMP', a.get_actor_label(), m.get_name(), 'apply' if '--apply' in A else 'revert')
    raise SystemExit

if mode == 'mesh':
    for n in NS:
        m = ld('SM_StairBaked451_N%d' % n)
        new = [ld('MI_StairBaked451_N%d_W2' % n)] * 2 if '--revert' not in A else [ld('MI_StairBaked451_N%d_Tread' % n), ld('MI_StairBaked451_N%d_Body' % n)]
        print('MESH', m.get_name(), [s.material_interface.get_name() for s in m.static_materials], '->', [x.get_name() for x in new])
        if '--dry-run' in A: continue
        for i, mi in enumerate(new): m.set_material(i, mi)
        EAL.save_loaded_asset(m)
    raise SystemExit
