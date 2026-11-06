# #553 commander window stroke: creates M_CC_Stroke (UI material, new asset, nothing else touched). Safe to re-run.
#   py stroke_material_ue.py --dry-run | --apply     (--dir <folder>: i5 lab; --png <folder>: writes lookdev frames, needs a GUI editor)
# One quad = panel + motion stroke, 1300 x 900 target px (window 1220 x 820 + 40 px margin). Scalars: T (real seconds, because the
# game is paused while the window is up) and Open (0..1 draw-on, the stroke runs from the top centre down both sides).
import sys, unreal
A = sys.argv[1:]
FOLDER = A[A.index('--dir') + 1] if '--dir' in A else '/Game/CastleDefender/UI/Barracks/Commander'
NAME = 'M_CC_Stroke'; PATH = FOLDER + '/' + NAME
E, M, AT = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetToolsHelpers.get_asset_tools()
HLSL = r'''
float asp = 1300.0 / 900.0, px = 1.0 / 900.0;
float2 p = (UV - 0.5) * float2(asp, 1.0);
float2 hs = float2(asp * 0.5, 0.5) - 40.0 * px;
float r = 14.0 * px;
float2 q = abs(p) - hs + r;
float d = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
float W = hs.x * 2.0, H = hs.y * 2.0, per = 2.0 * (W + H);
float2 e = p + hs;
float dx = min(e.x, W - e.x), dy = min(e.y, H - e.y), s;
if (dy < dx) s = e.y < H * 0.5 ? e.x : W + H + (W - e.x);
else         s = e.x > W * 0.5 ? W + e.y : W + H + W + (H - e.y);
s /= per;
float top = (W * 0.5) / per;
float ease = Open * Open * (3.0 - 2.0 * Open);
float along = abs(frac(s - top + 0.5) - 0.5) * 2.0;
float drawn = smoothstep(0.0, 0.01, ease * 1.02 - along);
float head = exp(-abs(ease * 1.02 - along) * 40.0) * (1.0 - smoothstep(0.85, 1.0, Open));
float lineM = smoothstep(1.7 * px, 0.7 * px, abs(d));
float hair = smoothstep(1.0 * px, 0.2 * px, abs(d + 8.0 * px)) * 0.28;
float glow = exp(-abs(d) / (9.0 * px)) * 0.28;
float comet = 0.0;
for (int i = 0; i < 3; i++) { float ph = frac(s - T * 0.055 - float(i) / 3.0); comet += (pow(ph, 30.0) + 0.35 * pow(ph, 6.0)) * smoothstep(1.0, 0.975, ph); }
float shim = 0.72 + 0.28 * sin(s * per * 55.0 + T * 1.3) * sin(s * per * 21.0 - T * 0.7);
float2 c = abs(e / float2(W, H) - 0.5) * 2.0;
float corner = pow(saturate(max(c.x, c.y)), 3.0) * pow(saturate(min(c.x, c.y)), 8.0);
float3 gold = float3(0.86, 0.60, 0.26), hot = float3(1.25, 1.0, 0.66);
float3 stroke = gold * (lineM * shim + hair + glow * (0.6 + 0.4 * sin(T * 0.9))) + hot * (lineM + glow * 0.5) * saturate(comet) * 0.9 + hot * corner * lineM * 0.9;
stroke = stroke * drawn + hot * head * (lineM * 1.4 + glow * 1.6);
float inside = smoothstep(px, -px, d);
float2 n = UV * float2(1300.0, 900.0);
float grain = frac(sin(dot(floor(n), float2(12.9898, 78.233))) * 43758.5453);
float vig = saturate(length((UV - 0.5) * float2(1.15, 1.25)) * 1.5);
float sheen = pow(saturate(1.0 - abs(frac((UV.x + UV.y * 0.6) * 0.5 - T * 0.018) - 0.5) * 7.0), 3.0) * 0.012;
float3 fill = lerp(float3(0.075, 0.062, 0.050), float3(0.026, 0.021, 0.017), vig) + (grain - 0.5) * 0.006 + gold * sheen;
float fa = saturate(Open * 4.0);
float sa = saturate(max(max(lineM, hair) * drawn, (glow * drawn + head * glow) * 1.4));
float a = max(inside * 0.93 * fa, sa);
float3 rgb = lerp(fill, stroke, saturate(sa * 1.2)) + stroke * inside * 0.35;
return float4(rgb, a);
'''
if '--apply' not in A:
    print('STROKE would create', PATH, 'exists now:', E.does_asset_exist(PATH)); raise SystemExit
E.make_directory(FOLDER)
if E.does_asset_exist(PATH): mat = unreal.load_asset(PATH); M.delete_all_material_expressions(mat)
else: mat = AT.create_asset(NAME, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_UI)
mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
def add(cls, x, y): return M.create_material_expression(mat, cls, x, y)
cu = add(unreal.MaterialExpressionCustom, -300, 0)
cu.set_editor_property('code', HLSL)
cu.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
cu.set_editor_property('description', 'CC stroke')
ci = []
for nm in ('UV', 'T', 'Open'):
    i = unreal.CustomInput(); i.set_editor_property('input_name', nm); ci.append(i)
cu.set_editor_property('inputs', ci)
uv = add(unreal.MaterialExpressionTextureCoordinate, -700, -100)
t = add(unreal.MaterialExpressionScalarParameter, -700, 0); t.set_editor_property('parameter_name', 'T'); t.set_editor_property('default_value', 2.0)
o = add(unreal.MaterialExpressionScalarParameter, -700, 120); o.set_editor_property('parameter_name', 'Open'); o.set_editor_property('default_value', 1.0)
print('STROKE links', M.connect_material_expressions(uv, '', cu, 'UV'), M.connect_material_expressions(t, '', cu, 'T'), M.connect_material_expressions(o, '', cu, 'Open'))
rgb = add(unreal.MaterialExpressionComponentMask, 0, -100)
for ch, v in (('r', True), ('g', True), ('b', True), ('a', False)): rgb.set_editor_property(ch, v)
al = add(unreal.MaterialExpressionComponentMask, 0, 100)
for ch, v in (('r', False), ('g', False), ('b', False), ('a', True)): al.set_editor_property(ch, v)
print('STROKE masks', M.connect_material_expressions(cu, '', rgb, ''), M.connect_material_expressions(cu, '', al, ''))
print('STROKE outs', M.connect_material_property(rgb, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR), M.connect_material_property(al, '', unreal.MaterialProperty.MP_OPACITY))
M.recompile_material(mat); E.save_asset(PATH, only_if_is_dirty=False)
print('STROKE saved', PATH)
