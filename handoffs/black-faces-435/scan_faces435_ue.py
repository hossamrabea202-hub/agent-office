# #435 (i5, 2026-11-02): read-only scan for the black faces. Lists every SkeletalMeshComponent template of the hero and
# the soldier BPs with mesh, override materials and per-slot materials, and the texture/scalar params of every MI used.
# Writes scan_report.txt next to this script. Changes nothing.
import os, unreal
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/black-faces-435'
BPS = ['/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter',
       '/Game/CastleDefender/Characters/Knight/BP_SoldierSword', '/Game/CastleDefender/Characters/Knight/BP_SoldierXbow',
       '/Game/CastleDefender/Characters/Knight/BP_SoldierCommander']
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
L, mats = [], {}
for p in BPS:
    bp = unreal.load_asset(p)
    if not bp: L.append('MISSING ' + p); continue
    L.append('== ' + p)
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        d = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
        if not isinstance(o, unreal.SkinnedMeshComponent) and not isinstance(o, unreal.StaticMeshComponent): continue
        mesh = o.get_editor_property('skeletal_mesh_asset') if isinstance(o, unreal.SkeletalMeshComponent) else o.get_editor_property('static_mesh')
        L.append('  %s  %s  mesh=%s visible=%s' % (o.get_name(), o.get_class().get_name(), mesh.get_path_name() if mesh else None, o.get_editor_property('visible')))
        ov = o.get_editor_property('override_materials')
        slots = []
        if isinstance(mesh, unreal.SkeletalMesh): slots = [(m.material_slot_name, m.material_interface) for m in mesh.materials]
        elif isinstance(mesh, unreal.StaticMesh): slots = [(m.material_slot_name, m.material_interface) for m in mesh.static_materials]
        for i, (sn, mi) in enumerate(slots):
            use = ov[i] if i < len(ov) and ov[i] else mi
            L.append('     slot %d %-10s %s%s' % (i, sn, use.get_path_name() if use else None, '  (override)' if i < len(ov) and ov[i] else ''))
            if use: mats[use.get_path_name()] = use
for path, m in sorted(mats.items()):
    L.append('## ' + path + '  ' + m.get_class().get_name())
    if isinstance(m, unreal.MaterialInstance):
        par = m.get_editor_property('parent'); L.append('   parent ' + (par.get_path_name() if par else 'None'))
        for tp in m.get_editor_property('texture_parameter_values'):
            L.append('   tex %s = %s' % (tp.parameter_info.name, tp.parameter_value.get_path_name() if tp.parameter_value else None))
        for sp in m.get_editor_property('scalar_parameter_values'):
            L.append('   sc  %s = %.3f' % (sp.parameter_info.name, sp.parameter_value))
        for vp in m.get_editor_property('vector_parameter_values'):
            c = vp.parameter_value; L.append('   vec %s = (%.3f %.3f %.3f %.3f)' % (vp.parameter_info.name, c.r, c.g, c.b, c.a))
    base = m.get_base_material() if hasattr(m, 'get_base_material') else None
    if base: L.append('   base %s shading=%s blend=%s' % (base.get_path_name(), base.get_editor_property('shading_model'), base.get_editor_property('blend_mode')))
open(os.path.join(HERE, 'scan_report.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(L))
