# #386 Jelly blob enemies: from cartoon red bubbles to wet organic slime (adjustedfilm, 2026-10-31 late). UE 5.3 Python.
#   py "<repo>/handoffs/jellyblob-real-386/setup_realblob386_ue.py" --info              READ-ONLY: the look node's inputs / outputs
#   py ".../setup_realblob386_ue.py" [--dry-run]       NEW M_JellyBlob_Real (copy of M_JellyBlob) + MI_JellyBlob_Real (copy of MI_JellyBlob)
#   py ".../setup_realblob386_ue.py" --preview         two spheres in front of the editor camera: Lookdev386_Old | Lookdev386_New
#   py ".../setup_realblob386_ue.py" --preview-remove
#   py ".../setup_realblob386_ue.py" --swap [--dry-run]   AFTER THE OWNER'S OK: MI_JellyBlob's parent -> M_JellyBlob_Real (backup json)
#   py ".../setup_realblob386_ue.py" --revert            MI_JellyBlob's parent back
# How: the copy keeps the whole vertex part (flight jiggle, splat, column, hatch: LandT HatchT ZShield TScale BornT Green) and every
# wire, incl. World Position Offset (so no hand-wiring). Only the CODE of the look node (JellyBlobPS: emissive + BC / Op / Rf)
# is replaced, and Roughness is wired to its Rf output. The script maps the node's own input names, whatever they are.
# Look (research: handoffs/blob-realism-293/RESEARCH.md): thick mucus membrane, dark desaturated bile-olive to maroon, bruise-dark
# inner masses and darker veins, wet / tacky roughness break-up, near-opaque at the thick centre, thinner at the rim, a dim warm
# transmission at the rim instead of glow, two-sided-safe facing (abs(N.V), the #382 lesson).
import os, sys, json, unreal

A = sys.argv[1:]
DRY = '--dry-run' in A
MODE = next((m for m in ('--info', '--preview-remove', '--preview', '--swap', '--revert') if m in A), 'build')
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\jellyblob-real-386'
D = '/Game/CastleDefender/VFX/JellyBubble'
SRC_M, SRC_MI = D + '/M_JellyBlob', D + '/MI_JellyBlob'
NEW_M, NEW_MI = D + '/M_JellyBlob_Real', D + '/MI_JellyBlob_Real'
BACKUP = os.path.join(HERE, 'realblob386_backup.json')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = ['#386 real jelly blob %s%s' % (MODE, ' (DRY RUN)' if DRY else '')]

LOOK = r'''
float3 n = normalize(_N + float3(0, 0, 1e-4)), v = normalize(_V + float3(0, 0, 1e-4));
float ndv = abs(dot(n, v));                                    // two-sided safe (no F = 1 on back faces)
float3 p = _LP * 0.04;                                         // local cm -> pattern space (engine sphere radius 50 = 2 units)
float t = _T;
// --- value-noise fbm (helpers inline: Custom nodes can't declare free functions)
float big = 0, fine = 0, vn = 0, org = 0;
[unroll] for (int k = 0; k < 4; k++)
{
    float3 q[4] = { p * 0.6 + float3(0, 0, t * 0.05), p * 2.5 - float3(t * 0.08, 0, 0), p * 1.3 + 3.1, p * 0.45 + 7.7 + t * 0.03 };
    float s = 0, amp = 0.5;
    float3 x = q[k];
    [unroll] for (int o = 0; o < 3; o++)
    {
        float3 i = floor(x), f = frac(x); f = f * f * (3.0 - 2.0 * f);
        float n000 = frac(sin(dot(i, float3(127.1, 311.7, 74.7))) * 43758.5453);
        float n100 = frac(sin(dot(i + float3(1, 0, 0), float3(127.1, 311.7, 74.7))) * 43758.5453);
        float n010 = frac(sin(dot(i + float3(0, 1, 0), float3(127.1, 311.7, 74.7))) * 43758.5453);
        float n110 = frac(sin(dot(i + float3(1, 1, 0), float3(127.1, 311.7, 74.7))) * 43758.5453);
        float n001 = frac(sin(dot(i + float3(0, 0, 1), float3(127.1, 311.7, 74.7))) * 43758.5453);
        float n101 = frac(sin(dot(i + float3(1, 0, 1), float3(127.1, 311.7, 74.7))) * 43758.5453);
        float n011 = frac(sin(dot(i + float3(0, 1, 1), float3(127.1, 311.7, 74.7))) * 43758.5453);
        float n111 = frac(sin(dot(i + float3(1, 1, 1), float3(127.1, 311.7, 74.7))) * 43758.5453);
        float nx = lerp(lerp(lerp(n000, n100, f.x), lerp(n010, n110, f.x), f.y), lerp(lerp(n001, n101, f.x), lerp(n011, n111, f.x), f.y), f.z);
        s += nx * amp; amp *= 0.5; x = x * 2.03 + 1.7;
    }
    s /= 0.875;
    if (k == 0) big = s; else if (k == 1) fine = s; else if (k == 2) vn = s; else org = s;
}
float vein = 1.0 - smoothstep(0.0, 0.05, abs(vn - 0.5));       // thin vein lines
float organ = smoothstep(0.48, 0.74, org);                     // dark masses inside (parasite shadows)
float thick = pow(ndv, 0.6);                                   // thick centre, thin rim
float3 bile = float3(0.110, 0.100, 0.035), maroon = float3(0.085, 0.022, 0.020), bruise = float3(0.045, 0.028, 0.035);
float3 base = lerp(bile, maroon, smoothstep(0.35, 0.70, big));
base = lerp(base, _Green * 0.18, 0.15);                        // a hint of the tentacle's shield colour
base = lerp(base, bruise, organ * 0.65 * thick);
base = lerp(base, float3(0.14, 0.020, 0.030), vein * 0.5);
BC = base;
Op = saturate(0.80 + 0.18 * thick - 0.30 * (1.0 - thick) * (1.0 - organ)) * saturate(_DF);
Rf = lerp(0.07, 0.42, smoothstep(0.40, 0.70, fine));           // wet patches vs tacky, drier patches
return float3(0.35, 0.10, 0.06) * (1.0 - thick) * (1.0 - organ) * 0.10 * _Inten;   // dim warm light through the thin rim, no glow
'''
ROLES = [  # alias, type, how to recognise the source expression, default when missing
    ('_N', 'float3', lambda e: isinstance(e, unreal.MaterialExpressionPixelNormalWS), 'float3(0, 0, 1)'),
    ('_V', 'float3', lambda e: isinstance(e, unreal.MaterialExpressionCameraVectorWS), 'float3(0, 0, 1)'),
    ('_T', 'float', lambda e: isinstance(e, unreal.MaterialExpressionTime), '0.0'),
    ('_LP', 'float3', lambda e: isinstance(e, unreal.MaterialExpressionVertexInterpolator), 'float3(0, 0, 0)'),
    ('_DF', 'float', lambda e: isinstance(e, unreal.MaterialExpressionDepthFade), '1.0'),
    ('_Green', 'float3', lambda e: isinstance(e, unreal.MaterialExpressionVectorParameter) and str(e.get_editor_property('parameter_name')) == 'Green', 'float3(0.36, 0.52, 0.27)'),
    ('_Inten', 'float', lambda e: isinstance(e, unreal.MaterialExpressionScalarParameter) and str(e.get_editor_property('parameter_name')) == 'Inten', '1.0')]


def look_node(m):
    """the JellyBlobPS custom node: the one feeding Base Color (its code names JellyBlobPS)."""
    n = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
    if isinstance(n, unreal.MaterialExpressionCustom) and 'JellyBlobPS' in n.get_editor_property('code'): return n
    log.append('WARNING: Base Color is not fed by the JellyBlobPS node (%s)' % (n.get_class().get_name() if n else None))
    return None


def header(m, node):
    """alias lines mapping this node's own input names to the roles the new code uses."""
    names = [str(i.get_editor_property('input_name')) for i in node.get_editor_property('inputs')]
    srcs = MEL.get_inputs_for_material_expression(m, node)
    lines, found = [], {}
    for nm, src in zip(names, srcs):
        for alias, typ, test, _d in ROLES:
            if src is not None and alias not in found and test(src):
                found[alias] = nm; lines.append('%s %s = (%s)(%s)%s;' % (typ, alias, typ, nm, '.xyz' if typ == 'float3' else '.x'))
    for alias, typ, _t, dflt in ROLES:
        if alias not in found: lines.append('%s %s = %s;   // input not found: default' % (typ, alias, dflt))
    log.append('  inputs %s' % names)
    log.append('  mapped %s' % found)
    return '\n'.join(lines)


if MODE == '--info':
    m = unreal.load_asset(SRC_M)
    node = look_node(m)
    if node:
        log.append('look node %s, outputs: main %s + %s' % (node.get_name(), node.get_editor_property('output_type'),
                   [(str(o.get_editor_property('output_name')), str(o.get_editor_property('output_type'))) for o in node.get_editor_property('additional_outputs')]))
        header(m, node)
    mi = unreal.load_asset(SRC_MI)
    log.append('MI_JellyBlob parent: %s' % mi.get_editor_property('parent').get_path_name())

elif MODE == 'build':
    log.append('copy %s -> %s, new look code, Roughness <- Rf; %s -> %s' % (SRC_M, NEW_M, SRC_MI, NEW_MI))
    if not DRY:
        for p in (NEW_MI, NEW_M):
            if EAL.does_asset_exist(p): EAL.delete_asset(p)      # our own copies only: rebuilt from the live ones each run
        m = EAL.duplicate_asset(SRC_M, NEW_M)
        node = look_node(m)
        if not node: raise SystemExit('look node not found: run --info and post the output on #386')
        node.set_editor_property('code', '// JellyBlobPS #386 REAL: wet organic slime (adjustedfilm)\n' + header(m, node) + LOOK)
        node.set_editor_property('description', 'JellyBlobPS_Real386')
        try: MEL.connect_material_property(node, 'Rf', unreal.MaterialProperty.MP_ROUGHNESS); log.append('  Roughness <- Rf (wet / tacky break-up)')
        except Exception as e: log.append('  (Roughness stays the scalar: %s)' % e)
        MEL.recompile_material(m); EAL.save_asset(NEW_M)
        mi = EAL.duplicate_asset(SRC_MI, NEW_MI)                 # keeps every value set on MI_JellyBlob
        MEL.set_material_instance_parent(mi, m)
        for k, v in (('Specular', 0.5), ('Roughness', 0.25)):
            try: MEL.set_material_instance_scalar_parameter_value(mi, k, v)
            except Exception: pass
        EAL.save_asset(NEW_MI)
        log.append('  built. Next: --preview for the owner, then --swap after the OK.')

elif MODE == '--preview':
    cam = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_level_viewport_camera_info()
    loc, rot = cam[0], cam[1]
    fwd, right = unreal.MathLibrary.get_forward_vector(rot), unreal.MathLibrary.get_right_vector(rot)
    sphere = unreal.load_asset('/Engine/BasicShapes/Sphere')
    for i, (label, mat) in enumerate((('Lookdev386_Old', SRC_MI), ('Lookdev386_New', NEW_MI))):
        at = loc + fwd * 400.0 + right * (-90.0 if i == 0 else 90.0)
        log.append('%s at %s (%s)' % (label, at, mat.split('/')[-1]))
        if DRY: continue
        for a in [x for x in EAS.get_all_level_actors() if x.get_actor_label() == label]: EAS.destroy_actor(a)
        a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, at, unreal.Rotator(0, 0, 0))
        a.set_actor_label(label); a.static_mesh_component.set_static_mesh(sphere)
        a.static_mesh_component.set_material(0, unreal.load_asset(mat))
    log.append('Screenshot both (day light), post with tools/shot.js --card 386, then --preview-remove.')

elif MODE == '--preview-remove':
    for a in [x for x in EAS.get_all_level_actors() if x.get_actor_label().startswith('Lookdev386_')]:
        log.append('remove ' + a.get_actor_label())
        if not DRY: EAS.destroy_actor(a)

elif MODE in ('--swap', '--revert'):
    mi = unreal.load_asset(SRC_MI)
    cur = mi.get_editor_property('parent').get_path_name()
    if MODE == '--swap':
        if not EAL.does_asset_exist(NEW_M): log.append('M_JellyBlob_Real missing: build first')
        elif cur.startswith(NEW_M): log.append('already swapped')
        else:
            log.append('MI_JellyBlob parent %s -> M_JellyBlob_Real' % cur)
            if not DRY:
                json.dump({'parent': cur}, open(BACKUP, 'w')); MEL.set_material_instance_parent(mi, unreal.load_asset(NEW_M)); EAL.save_asset(SRC_MI)
    else:
        if not os.path.exists(BACKUP): log.append('no backup: nothing to revert')
        else:
            old = json.load(open(BACKUP))['parent']; log.append('MI_JellyBlob parent back to ' + old)
            if not DRY: MEL.set_material_instance_parent(mi, unreal.load_asset(old)); EAL.save_asset(SRC_MI); os.remove(BACKUP)

out = '\n'.join(log)
open(os.path.join(HERE, 'realblob386_%s.txt' % MODE.strip('-')), 'w').write(out)
unreal.log(out); print(out)
