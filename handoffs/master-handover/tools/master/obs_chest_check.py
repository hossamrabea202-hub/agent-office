import unreal, traceback
FIX = False
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = []
try:
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    hits = [a for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == 'BP_ThirdPersonCharacter']
    bp = unreal.load_asset(str(hits[0].package_name)); out.append('hero ' + str(hits[0].package_name))
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    MEL = unreal.MaterialEditingLibrary
    def desc(m):
        s = m.get_path_name()
        if isinstance(m, unreal.MaterialInstanceConstant):
            s += ' parent=%s' % (m.get_editor_property('parent').get_name() if m.get_editor_property('parent') else None)
            s += ' ArmorMode=%s' % MEL.get_material_instance_scalar_parameter_value(m, 'ArmorMode')
            s += ' overrides=%s' % [(str(p.parameter_info.name), p.parameter_value) for p in m.get_editor_property('scalar_parameter_values')]
        return s
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
        if isinstance(o, unreal.MeshComponent):
            n = o.get_name()
            if any(k in n for k in ('Obsidian', 'Remnant', 'Knight', 'Cape', 'Cloak', 'Mesh')):
                out.append('%s visible=%s hiddenInGame=%s' % (n, o.is_visible(), o.get_editor_property('hidden_in_game')))
                for i, m in enumerate(o.get_materials()):
                    out.append('   [%d] %s' % (i, desc(m) if m else None))
    for p in ['/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/M_ObsidianSovereign', '/Game/CastleDefender/Characters/Knight/Materials/AAA/M_HeroArmor_AAA']:
        m = unreal.load_asset(p)
        names = []
        for e in m.get_editor_property('expressions') if hasattr(m, 'get_editor_property') else []:
            pass
        sc = MEL.get_scalar_parameter_names(m)
        out.append('%s scalarParams=%s ArmorMode default=%s' % (p, list(sc), MEL.get_scalar_parameter_default(m, 'ArmorMode') if 'ArmorMode' in [str(x) for x in sc] else 'n/a'))
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
