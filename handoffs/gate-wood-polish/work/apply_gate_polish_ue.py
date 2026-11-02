# Main gate material polish (i5, 2026-11-02). Materials/textures ONLY: no Blueprint, skeletal mesh geometry, animation,
# socket or trigger is touched.
#   py apply_gate_polish_ue.py --apply <tex_dir>    import v2 textures, back up the gate MI, point it at the v2 textures,
#                                                   give the gate leaf's iron slot a new M_GateIron_Forged
#   py apply_gate_polish_ue.py --revert             restore the MI parameters and the leaf's slot-1 material
# What changes:
#   MI_GateBreach_Scratched_L: WoodORM -> T_GateOak_ORM_v2 (grain roughness), IronColor/IronARM -> forged iron v2
#   SK_GateLeaf_L material slot 1: M_Metal_Steel -> M_GateIron_Forged (same v2 iron maps; M_Metal_Steel is untouched)
import json, os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Props/GateBreach/Polish'
MI = '/Game/CastleDefender/Props/GateBreach/MI_GateBreach_Scratched_L'
REC = os.path.join(HERE, 'gate_polish_record.json')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()


def find(name, cls):
    for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', cls)):
        if str(a.asset_name) == name:
            return unreal.load_asset(str(a.package_name))


def import_tex(path, name, like, srgb):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.destination_name = name; t.automated = True; t.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset(DST + '/' + name)
    tex.set_editor_property('srgb', srgb)
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT if srgb else unreal.TextureCompressionSettings.TC_MASKS)
    for p in ('max_texture_size', 'lod_group', 'mip_gen_settings'):        # same streaming budget as the texture it replaces
        tex.set_editor_property(p, like.get_editor_property(p))
    EAL.save_loaded_asset(tex)
    return tex


def forged_material(d_tex, arm_tex):
    path = DST + '/M_GateIron_Forged'
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_GateIron_Forged', DST, unreal.Material, unreal.MaterialFactoryNew())
    tc = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    til = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1100, 0)
    til.set_editor_property('parameter_name', 'Tiling'); til.set_editor_property('default_value', 1.0)
    uv = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -700, 0)
    MEL.connect_material_expressions(tc, '', uv, 'A'); MEL.connect_material_expressions(til, '', uv, 'B')
    def samp(tex, y, kind):
        s = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -450, y)
        s.set_editor_property('texture', tex); s.set_editor_property('sampler_type', kind)
        MEL.connect_material_expressions(uv, '', s, 'UVs')
        return s
    d = samp(d_tex, -200, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR); d.set_editor_property('parameter_name', 'IronColor')
    a = samp(arm_tex, 100, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS); a.set_editor_property('parameter_name', 'IronARM')
    n = samp(find('T_Metal_Steel_N', 'Texture2D'), 400, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL); n.set_editor_property('parameter_name', 'IronNormal')
    MEL.connect_material_property(d, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(a, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(a, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(a, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(n, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    mat.set_editor_property('used_with_skeletal_mesh', True)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat


EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
GATE_MAT = '/Game/CastleDefender/Props/GateBreach/M_GateBreach_Scratched'
# Iron in the gate shader: was near-black (0.035 linear) AND fully metallic = black plastic. Now blackened mill-scale oxide
# (dielectric, ~0.037 linear, matte-satin 0.72-0.9) mottled by the forge-scale texture (IronColor / IronARM inputs, which the
# shader had but never sampled), with bright bare metal (0.5 linear, metallic 1, rough 0.35) only on rubbed corners.
# Rust unchanged. Same inputs/outputs, so GateDamage / mud / skinning logic is untouched.
IRON_OLD = """float3 ironC=float3(0.035,0.034,0.033)*(0.85+0.3*grit);
float3 rustC=lerp(float3(0.10,0.045,0.022),float3(0.16,0.075,0.035),grit);
c=lerp(c,lerp(ironC,rustC,rust),iron);
rough=lerp(rough,lerp(0.55+0.1*grit,0.85,rust),iron);
Metal=iron*(1.0-rust);"""
IRON_NEW = """float3 ip=P/40.0;                                                  // forge scale, tri-planar like the wood (pre-skinned: no swimming)
float3 iv=Texture2DSample(ITex,ITexSampler,ip.yz).rgb*n.x+Texture2DSample(ITex,ITexSampler,ip.xz).rgb*n.y+Texture2DSample(ITex,ITexSampler,ip.xy).rgb*n.z;
float4 ia=Texture2DSample(IARM,IARMSampler,ip.yz)*n.x+Texture2DSample(IARM,IARMSampler,ip.xz)*n.y+Texture2DSample(IARM,IARMSampler,ip.xy)*n.z;
float mott=lerp(1.0,clamp(dot(iv,float3(0.3,0.59,0.11))/0.040,0.8,1.2),0.6);
float3 ironC=float3(0.037,0.036,0.034)*(0.85+0.3*grit)*mott;         // mill-scale oxide: dielectric
float3 rustC=lerp(float3(0.10,0.045,0.022),float3(0.16,0.075,0.035),grit);
float bare=saturate((max(saturate((t-0.85)*6.0)*side, saturate(1.0-t*6.0)*side*0.6)-0.35)*2.5)*saturate(grit*1.6-0.2)*(1.0-rust);
float3 bareC=float3(0.50,0.49,0.47)*(0.88+0.24*grit);                // rubbed bare wrought iron
c=lerp(c,lerp(lerp(ironC,rustC,rust),bareC,bare),iron);
rough=lerp(rough,lerp(lerp(lerp(0.78+0.10*grit,ia.g,0.25),0.85,rust),0.35,bare),iron);
Metal=iron*bare;"""


def gate_custom_node(path=GATE_MAT):
    mat = unreal.load_asset(path)
    seen, todo = set(), [MEL.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)]
    while todo:
        n = todo.pop()
        if n is None or n.get_name() in seen:
            continue
        seen.add(n.get_name())
        if isinstance(n, unreal.MaterialExpressionCustom) and 'ironC' in n.get_editor_property('code'):
            return mat, n
        todo += list(MEL.get_inputs_for_material_expression(mat, n))
    return mat, None


def patch_iron(new):
    """Rebuild the shader code from the untouched backup each time (idempotent: re-running never stacks edits)."""
    mat, node = gate_custom_node()
    _, bnode = gate_custom_node(GATE_MAT + '_BACKUP_polish')
    original = bnode.get_editor_property('code')
    if IRON_OLD not in original:
        print('iron code: backup does not hold the expected original block - nothing changed'); return
    node.set_editor_property('code', original.replace(IRON_OLD, IRON_NEW) if new else original)
    MEL.recompile_material(mat); EAL.save_loaded_asset(mat)
    print('iron code', 'patched' if new else 'restored', 'in', mat.get_name())


def leaves():
    return [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == 'BP_GateBreachLeaf_C']


def apply(tex_dir):
    mi = unreal.load_asset(MI)
    old = {'params': {}, 'slot1': {}}
    for n in ('WoodORM', 'IronColor', 'IronARM'):
        t = MEL.get_material_instance_texture_parameter_value(mi, n); old['params'][n] = t.get_path_name() if t else None
    for a in leaves():
        c = a.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        old['slot1'][a.get_path_name()] = c.get_material(1).get_path_name()
    if not os.path.exists(REC):
        json.dump(old, open(REC, 'w'), indent=1)
    if not EAL.does_asset_exist(MI + '_BACKUP_polish'):
        EAL.duplicate_asset(MI, MI + '_BACKUP_polish')
    if not EAL.does_asset_exist(GATE_MAT + '_BACKUP_polish'):
        EAL.duplicate_asset(GATE_MAT, GATE_MAT + '_BACKUP_polish')
    patch_iron(True)
    oak = import_tex(os.path.join(tex_dir, 'T_GateOak_ORM_v2.png'), 'T_GateOak_ORM_v2', find('T_GateOak_ORM', 'Texture2D'), False)
    ird = import_tex(os.path.join(tex_dir, 'T_GateIron_D_v2.png'), 'T_GateIron_D_v2', find('T_Metal_Steel_D', 'Texture2D'), True)
    ira = import_tex(os.path.join(tex_dir, 'T_GateIron_ARM_v2.png'), 'T_GateIron_ARM_v2', find('T_GateIron_ARM', 'Texture2D'), False)
    MEL.set_material_instance_texture_parameter_value(mi, 'WoodORM', oak)
    MEL.set_material_instance_texture_parameter_value(mi, 'IronColor', ird)
    MEL.set_material_instance_texture_parameter_value(mi, 'IronARM', ira)
    MEL.update_material_instance(mi); EAL.save_loaded_asset(mi)
    forged = forged_material(ird, ira)
    # per placed leaf (the Blueprint itself is not edited): slot 1 override -> forged iron. Level change: i9 saves the map.
    for a in leaves():
        a.get_components_by_class(unreal.SkeletalMeshComponent)[0].set_material(1, forged)
    print('gate polish applied: MI textures', [t.get_name() for t in (oak, ird, ira)], '| leaf slot1 ->', forged.get_name(),
          'on', len(leaves()), 'placed leaves | backup', MI + '_BACKUP_polish', '| old values in', REC)


def revert():
    old = json.load(open(REC))
    patch_iron(False)
    mi = unreal.load_asset(MI)
    for n, p in old['params'].items():
        if p:
            MEL.set_material_instance_texture_parameter_value(mi, n, unreal.load_asset(p))
    MEL.update_material_instance(mi); EAL.save_loaded_asset(mi)
    for a in leaves():
        p = old['slot1'].get(a.get_path_name())
        if p:
            a.get_components_by_class(unreal.SkeletalMeshComponent)[0].set_material(1, unreal.load_asset(p))
    print('gate polish reverted (MI params + leaf slot 1). New textures/material left in', DST)


def leaves_only():
    """On the Master after unzipping the assets: only the per-actor slot-1 override (the rest ships in the zip)."""
    forged = unreal.load_asset(DST + '/M_GateIron_Forged')
    old = {'params': {}, 'slot1': {}}
    for a in leaves():
        c = a.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        old['slot1'][a.get_path_name()] = c.get_material(1).get_path_name()
        c.set_material(1, forged)
    if not os.path.exists(REC):
        json.dump(old, open(REC, 'w'), indent=1)
    print('leaf slot1 -> M_GateIron_Forged on', len(leaves()), 'placed leaves. SAVE THE MAP. (--revert restores)')


if '--revert' in sys.argv:
    revert()
elif '--leaves' in sys.argv:
    leaves_only()
elif '--apply' in sys.argv:
    apply(sys.argv[sys.argv.index('--apply') + 1])
else:
    print('usage: --apply <tex_dir> | --revert')
