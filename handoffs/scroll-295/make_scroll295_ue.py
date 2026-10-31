# #295 The notice scroll ("NIGHT FALLS", "DAWN", every PushNotice) as a real medieval scroll, not plastic (adjustedfilm, 2026-10-31).
#   py "<repo>/handoffs/scroll-295/make_scroll295_ue.py" --dry-run      (only reports)
#   py "<repo>/handoffs/scroll-295/make_scroll295_ue.py"
# Rebuilds /Game/CastleDefender/UI/Notices/M_NoticeBanner IN PLACE (same asset, same params Roll / Aspect / Fade / Tier), so
# BP_NoticeHUD keeps working with no paste. The old look is first copied to M_NoticeBanner_SteelBackup (to go back: delete
# M_NoticeBanner, rename the backup).
# Look: dyed vellum (umber; red-dyed for Tier 1 "important"), like royal manuscripts written in gold ink on dyed parchment,
# so the HUD's existing warm-gold text stays readable. Mottled stains, fibres, uneven deckled top/bottom edges, darker
# handled edges, a faded iron-gall double rule, the sheet darkening as it curls onto the rollers. Turned walnut rollers
# with dull brass finials. Same roll-out geometry and timing as #31.
import sys, unreal

DRY = '--dry-run' in sys.argv
PATH, NAME = '/Game/CastleDefender/UI/Notices', 'M_NoticeBanner'
FULL, BAK = PATH + '/' + NAME, PATH + '/M_NoticeBanner_SteelBackup'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
log = ['#295 scroll' + (' (DRY RUN, nothing written)' if DRY else '')]

# value noise, written out inline (Custom nodes can't declare functions)
def vnoise(out, px, py, seed):
    return '''float %(o)s; { float2 p = float2(%(x)s, %(y)s) + %(s)s; float2 i = floor(p), f = frac(p); f = f * f * (3.0 - 2.0 * f);
  float a = frac(sin(dot(i, float2(127.1, 311.7))) * 43758.5453), b = frac(sin(dot(i + float2(1, 0), float2(127.1, 311.7))) * 43758.5453);
  float c = frac(sin(dot(i + float2(0, 1), float2(127.1, 311.7))) * 43758.5453), d = frac(sin(dot(i + float2(1, 1), float2(127.1, 311.7))) * 43758.5453);
  %(o)s = lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y); }
''' % {'o': out, 'x': px, 'y': py, 's': seed}

CODE = '''float A = max(Aspect, 1.0);
float x = UV.x * A, y = UV.y;
float cx = A * 0.5;
float hw = lerp(0.45, cx - 0.5, saturate(Roll));
float dx = abs(x - cx);
float aa = 0.02;
''' + vnoise('n1', 'x * 2.5', 'y * 2.5', '3.1') + vnoise('n2', 'x * 9.0', 'y * 9.0', '17.7') \
    + vnoise('nt', 'x * 7.0', '0.0', '41.0') + vnoise('nb', 'x * 7.0', '0.0', '73.0') + '''
float fb = frac(sin(floor(y * 240.0) * 91.7 + floor(x * 5.0) * 13.1) * 43758.5453);
float yt = 0.11 + 0.022 * (nt - 0.5), yb = 0.89 + 0.022 * (nb - 0.5);
float sheet = saturate((hw - dx) / aa) * saturate((y - yt) / aa) * saturate((yb - y) / aa);
float3 vel = lerp(float3(0.19, 0.120, 0.066), float3(0.30, 0.200, 0.112), n1);
vel = lerp(vel, float3(0.25, 0.050, 0.040) * (0.8 + 0.4 * n1), saturate(Tier));
vel *= 0.84 + 0.26 * n2;
vel *= 0.93 + 0.07 * fb;
float edge = min(y - yt, yb - y);
vel *= lerp(0.55, 1.0, saturate(edge / 0.12));
float curl = saturate(1.0 - (hw - dx) / 0.6);
vel *= 1.0 - 0.5 * curl * curl;
float rule = saturate(1.0 - abs(y - 0.20) / 0.008) + saturate(1.0 - abs(y - 0.80) / 0.008);
vel = lerp(vel, vel * 0.55, saturate(rule) * 0.6);
float rodX = abs(dx - hw);
float rodW = 0.12;
float rod = saturate((rodW - rodX) / aa) * saturate((y - 0.03) / aa) * saturate((0.97 - y) / aa);
float shade = sqrt(saturate(1.0 - (rodX / rodW) * (rodX / rodW)));
float grain = frac(y * 14.0 + 3.0 * n2);
float3 wood = float3(0.11, 0.065, 0.035) * (0.8 + 0.4 * grain);
float fin = saturate((abs(y - 0.5) - 0.40) / 0.01);
float3 rodC = lerp(wood, float3(0.30, 0.19, 0.07), fin) * (0.3 + 0.9 * shade);
float3 col = lerp(vel, rodC, rod);
col *= 1.0 - 0.4 * saturate(1.0 - (hw - dx) / 0.3) * sheet * (1.0 - rod);
return float4(col, max(sheet, rod) * saturate(Fade));
'''

if not EAL.does_asset_exist(FULL): raise SystemExit('M_NoticeBanner not found at ' + FULL + ' (#31/#112 must be in first)')
if EAL.does_asset_exist(BAK): log.append('backup already there: ' + BAK)
else:
    log.append('backup ' + FULL + ' -> ' + BAK)
    if not DRY: EAL.duplicate_asset(FULL, BAK)
log.append('rebuild ' + FULL + ' in place (params Roll, Aspect, Fade, Tier)')
if not DRY:
    mat = unreal.load_asset(FULL)
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(mat)
    MEL.delete_all_material_expressions(mat)
    uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -450, 120)
    c.set_editor_property('description', 'Scroll295'); c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    c.set_editor_property('code', CODE)
    ps = [('Roll', 1.0), ('Aspect', 11.9), ('Fade', 1.0), ('Tier', 0.0)]
    ins = []
    for n in ['UV'] + [p for p, _ in ps]:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    c.set_editor_property('inputs', ins)
    MEL.connect_material_expressions(uv, '', c, 'UV')
    for i, (n, v) in enumerate(ps):
        s = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -900, 120 + i * 110)
        s.set_editor_property('parameter_name', n); s.set_editor_property('default_value', v)
        MEL.connect_material_expressions(s, '', c, n)
    rgb = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, 60)
    for ch, on in zip('rgba', (True, True, True, False)): rgb.set_editor_property(ch, on)
    al = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, 200)
    for ch, on in zip('rgba', (False, False, False, True)): al.set_editor_property(ch, on)
    MEL.connect_material_expressions(c, '', rgb, ''); MEL.connect_material_expressions(c, '', al, '')
    MEL.connect_material_property(rgb, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(al, '', unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(mat); EAL.save_asset(FULL)
unreal.log('\n'.join(log))
