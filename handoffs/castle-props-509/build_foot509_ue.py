# #509 step 6a (i5 checkking, 2026-11-05): the wall-foot stain card. UE 5.8 editor Python, safe to re-run.   [--dry-run] [--temp]
# Makes, ALL NEW, in /Game/CastleDefender/Environment/CastleWeather504 (next to #504's cards, same family, nothing live touched):
#   M_FootCard509        rain SPLASH-BACK (rain hits the ground and throws soil 30-50 cm up the wall: a speckled, ragged band) +
#                        MOSS clumps on the lowest course (it stays damp longest at the foot, rising damp + splash)
#   MI_Foot509_Sun / _Shade   less moss on faces the sun dries, more on the faces turned away (as #504's lichen)
# Same #504 method: unlit MODULATE card, instanced, per-instance seed, works on walls with Receives Decals off.
# Physical order (KB rule 3): soil splash first, moss over it. Values: wet soil ~0.10 (INDUSTRY_SECRETS 1.1 soil 0.15 dry,
# splash is damp), moss 0.05-0.16 green (campmat moss). Restraint: only on stone that has NO base band of its own (see the placer).
import sys, unreal
SRC = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-weather-504/build_weather504_ue.py'
code = open(SRC, encoding='utf-8').read()
g = {'__name__': 'foot509'}
exec(compile(code[:code.index('if not DRY and not TEMP and not EAL.does_directory_exist(DST)')], SRC, 'exec'), g)   # #504's helpers + noise
if '--temp' in sys.argv: g['DST'] = '/Game/_i5tmpWS509'
FOOT = '''float hb = p.y + 0.5;
float xw = p.x;
float edge = SplashH * (0.7 + 0.6 * fb);
float splash = 1.0 - smoothstep(edge * 0.55, edge, hb);
float2 qs = float2(xw * 46.0, hb * 46.0) + S;
float sp = step(0.62, H21(floor(qs))) * (1.0 - smoothstep(edge, edge * 1.7, hb));
float mud = saturate(splash * (0.55 + 0.45 * fb) + sp * 0.45) * Mud;
float mz = 1.0 - smoothstep(MossH * 0.25, MossH, hb + (fb - 0.5) * 0.35);
float mc = smoothstep(0.42, 0.66, fb + 0.3 * (H21(floor(float2(xw * 9.0, hb * 9.0) + S)) - 0.5));
float moss = mz * mc * Moss;
float sides = saturate((0.5 - abs(xw)) * 6.0) * saturate(hb * 25.0);
float3 mudc = float3(0.11, 0.085, 0.06);
float3 mossc = lerp(float3(0.05, 0.09, 0.025), float3(0.10, 0.16, 0.045), fb);
float a = saturate(max(mud, moss) * sides) * MaxOpacity;
float3 col = lerp(mudc, mossc, saturate(moss / max(mud + moss, 0.001)));
'''
g['card_material']('M_FootCard509', FOOT, [('SplashH', 0.45), ('MossH', 0.8), ('Mud', 0.8), ('Moss', 0.5), ('MaxOpacity', 0.72)], 1.0)
MEL, EAL = g['MEL'], g['EAL']
for n, vals in (('MI_Foot509_Sun', {'Moss': 0.2}), ('MI_Foot509_Shade', {'Moss': 0.75, 'Mud': 0.6})):
    mi, made = g['fresh'](n, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if not mi: continue
    MEL.set_material_instance_parent(mi, unreal.load_asset(g['DST'] + '/M_FootCard509'))
    for k, v in vals.items(): MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    g['SAVE'](g['DST'] + '/' + n)
print('\n'.join(g['log']))
