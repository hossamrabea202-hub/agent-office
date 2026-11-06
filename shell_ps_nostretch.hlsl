// shared helpers (UE Custom nodes need helper functions inside a struct)
struct JellyFn
{
    float2 h2(float2 p)
    {
        float3 q = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
        q += dot(q, q.yzx + 33.33);
        return frac((q.xx + q.yz) * q.zy);
    }
    float3 h3(float3 p)
    {
        p = frac(p * float3(0.1031, 0.1030, 0.0973));
        p += dot(p, p.yxz + 33.33);
        return frac((p.xxy + p.yxx) * p.zyx);
    }
    // 3D cells: x = F1, y = F2 - F1 (small on membrane walls). Feature points drift with tt.
    float2 vor3(float3 x, float tt)
    {
        float3 i = floor(x); float3 f = frac(x);
        float d1 = 8.0; float d2 = 8.0;
        [unroll] for (int z = -1; z <= 1; z++)
        [unroll] for (int y = -1; y <= 1; y++)
        [unroll] for (int k = -1; k <= 1; k++)
        {
            float3 g = float3(k, y, z);
            float3 o = 0.5 + 0.38 * sin(tt + 6.2831853 * h3(i + g));
            float3 r = g + o - f;
            float d = dot(r, r);
            if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
        }
        d1 = sqrt(d1); return float2(d1, sqrt(d2) - d1);
    }
    // 2D cells, periodic in x with period P (wraps around the tentacle girth without a seam)
    float2 vor2(float2 x, float P, float tt)
    {
        float2 i = floor(x); float2 f = frac(x);
        float d1 = 8.0; float d2 = 8.0;
        [unroll] for (int y = -1; y <= 1; y++)
        [unroll] for (int k = -1; k <= 1; k++)
        {
            float2 g = float2(k, y);
            float2 id = i + g; id.x -= P * floor(id.x / P);
            float2 o = 0.5 + 0.38 * sin(tt + 6.2831853 * h2(id));
            float2 r = g + o - f;
            float d = dot(r, r);
            if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
        }
        d1 = sqrt(d1); return float2(d1, sqrt(d2) - d1);
    }
    // value noise, periodic in x with period P
    float vn(float2 p, float P)
    {
        float2 i = floor(p); float2 f = frac(p);
        float2 u = f * f * (3.0 - 2.0 * f);
        float2 i1 = i + 1.0;
        float x0 = i.x - P * floor(i.x / P); float x1 = i1.x - P * floor(i1.x / P);
        float a = h2(float2(x0, i.y)).x; float b = h2(float2(x1, i.y)).x;
        float c = h2(float2(x0, i1.y)).x; float d = h2(float2(x1, i1.y)).x;
        return lerp(lerp(a, b, u.x), lerp(c, d, u.x), u.y);
    }
};
JellyFn J;

// JellyShellPS v3 "living membrane" (2026-10-26): wet, stretched bio-membrane over a fluid layer. Main output = emissive.
// Extra: BC, Op, Rf. Membrane = cell plates + longitudinal stretch fibres + transverse wrinkles that bunch with the
// heartbeat + contraction ripples running up the spine; all of it bumps a per-pixel normal (surface-gradient bump from
// screen derivatives), so wet glints, thin-film sheen and refraction crawl over the surface instead of a flat haze.
// Inside: blood capillaries pumping on the heartbeat, suspended spores and trapped gas bubbles (view parallax).
// DF softens ground contact, CamD fades the gel when the camera is inside it. +15% visibility vs v2.
float s = SA.x;
float a01 = atan2(SA.z, SA.y) * 0.15915494 + 0.5;
float3 n = normalize(Nw); float3 v = normalize(Vw);
float ndv = saturate(abs(dot(n, v)));
float path = 1.0 / max(ndv, 0.12);
float rim = 1.0 - ndv;
float tip = smoothstep(8500.0, 11800.0, s);
// No-stretch (Master 2026-10-31): where the root flare is thick, 20 cells around the girth are wider than the 220-unit
// cell length, so the cells smear sideways. sU re-paces the spine coordinate there (integral of 220 / girth-cell size),
// identical slope to s (offset only) where the tentacle is thin. Used by every pattern lookup, not by timing / fades.
const float SUT[61] = {0.0, 104.8, 209.5, 314.3, 414.0, 504.9, 596.2, 697.6, 810.8, 938.4, 1075.4, 1214.1, 1355.4, 1499.9, 1647.9, 1799.8, 1956.1, 2117.3, 2282.5, 2450.5, 2622.0, 2798.3, 2979.4, 3165.5, 3357.0, 3554.1, 3754.1, 3954.1, 4154.1, 4354.1, 4554.1, 4754.1, 4954.1, 5154.1, 5354.1, 5554.1, 5754.1, 5954.1, 6154.1, 6354.1, 6554.1, 6754.1, 6954.1, 7154.1, 7354.1, 7554.1, 7754.1, 7954.1, 8154.1, 8354.1, 8554.1, 8754.1, 8954.1, 9154.1, 9354.1, 9554.1, 9754.1, 9954.1, 10154.1, 10354.1, 10554.1};
float sUi = clamp(s / 200.0, 0.0, 59.999); int sUk = (int)sUi;
float sU = lerp(SUT[sUk], SUT[sUk + 1], sUi - sUk) + max(s - 12000.0, 0.0);

float bt = frac(T * 0.75 - s * 0.00004);
float hb = exp(-pow((bt - 0.08) * 22.0, 2.0)) + 0.55 * exp(-pow((bt - 0.24) * 22.0, 2.0));
float p1 = frac(T * 0.021); float p2 = frac(T * 0.021 + 0.47);
float e1 = (s - lerp(-600.0, 11600.0, p1)) / 520.0; float e2 = (s - lerp(-600.0, 11600.0, p2)) / 520.0;
float band = exp(-e1 * e1) + exp(-e2 * e2);

// 1) membrane cell plates: 20 cells around the girth (periodic, no seam), ~5 m along the spine
float2 uv = float2(a01 * 20.0, sU / 220.0);
uv.y += 0.30 * sin(uv.x * 0.9424778 + T * 0.21) + 0.15 * sin(uv.y * 2.3 - T * 0.17);
float wx = J.vn(float2(a01 * 8.0, sU / 400.0 + T * 0.03), 8.0);
uv += float2(1.4, 0.8) * (wx - 0.5);
float2 c = J.vor2(uv, 20.0, T * 0.35);
float aw = fwidth(c.y);
float wv = 0.5 + 0.5 * sin(s * 0.0031 + a01 * 12.566371 + T * 0.3);
float wv2 = 0.5 + 0.5 * sin(s * 0.0017 - a01 * 18.849556 - T * 0.23);
float wall = (1.0 - smoothstep(0.008, lerp(0.025, 0.06, wv) + aw * 1.5, c.y)) * saturate(1.0 - aw * 2.5) * lerp(0.2, 1.0, wv2 * wv2);
float aw2 = fwidth(c.x);
float nuc = (1.0 - smoothstep(0.06, 0.12 + aw2, c.x)) * saturate(1.0 - aw2 * 3.0) * wv2;

// 2) blood capillaries inside the gel (warped along s only, keeps the girth period); pulses run up them
float wn = J.vn(float2(a01 * 12.0, sU / 300.0 - T * 0.05), 12.0);
float wn2 = J.vn(float2(a01 * 22.0, sU / 140.0 + T * 0.04), 22.0);
float2 uv2 = float2(a01 * 32.0 + (wn2 - 0.5) * 1.3, sU / 130.0 + (wn - 0.5) * 1.6 + (wn2 - 0.5) * 0.9);   // two warps: organic, no straight cell edges
float2 c2 = J.vor2(uv2, 32.0, T * 0.6);
float aw3 = fwidth(c2.y);
float vein = (1.0 - smoothstep(0.0, 0.065 + aw3 * 1.5, c2.y)) * saturate(1.0 - aw3 * 2.0) * (0.45 + 0.55 * wn);
float vmask = smoothstep(0.28, 0.72, J.vn(float2(a01 * 7.0, sU / 520.0), 7.0));      // vessels cluster in patches, not an even net
vein *= lerp(0.2, 1.0, vmask);
float vcore = (1.0 - smoothstep(0.0, 0.025 + aw3, c2.y)) * saturate(1.0 - aw3 * 2.0) * vmask;   // bright lumen down the vessel middle
float flow = pow(saturate(0.5 + 0.5 * sin(s * 0.0045 - T * 2.6 + c2.x * 4.0 + wn * 6.0)), 6.0);

// 3) spores suspended in the fluid, drifting up; grazing views shift them (fake depth inside the layer)
float2 uv3 = float2(a01 * 30.0, sU / 70.0 - T * 0.35 + (path - 1.0) * 0.35);
float2 c3 = J.vor2(uv3, 30.0, T * 0.9);
float aw4 = fwidth(c3.x);
float spore = (1.0 - smoothstep(0.03, 0.09 + aw4, c3.x)) * saturate(1.0 - aw4 * 4.0) * smoothstep(0.45, 0.75, J.vn(uv3 * 0.5, 15.0));
// trapped gas bubbles: thin bright rings, slow rise, deeper parallax than the spores
float2 uv4 = float2(a01 * 56.0, sU / 38.0 - T * 0.12 + (path - 1.0) * 0.6);
float2 c4 = J.vor2(uv4, 56.0, T * 0.15);
float aw5 = fwidth(c4.x);
float bmask = smoothstep(0.66, 0.85, J.vn(float2(a01 * 9.0, sU / 160.0), 9.0)) * saturate(1.0 - aw5 * 4.0);
float brad = 0.04 + 0.09 * J.vn(uv4 * 2.0, 112.0);                  // every bubble a different size
float bubR = exp(-pow((c4.x - brad) / (0.012 + 0.15 * brad + aw5), 2.0)) * bmask * 0.6;
float bubC = (1.0 - smoothstep(0.0, 0.35 * brad + aw5, c4.x)) * bmask;   // bright core where the bubble catches light

// 4) membrane surface relief (cm): stretch fibres along the spine, wrinkles across it that bunch on each heartbeat,
//    contraction ripples travelling up, raised cell ridges. Fades out where it would alias.
float fibF = saturate(1.0 - fwidth(a01 * 140.0) * 1.2);
float fib = (J.vn(float2(a01 * 140.0, sU / 1100.0), 140.0) - 0.5) * fibF;
float wkF = saturate(1.0 - fwidth(s / 24.0) * 0.8);
float wm = smoothstep(0.35, 0.8, J.vn(float2(a01 * 6.0, sU / 700.0 + T * 0.02), 6.0));
float wrk = sin(sU / 24.0 + J.vn(float2(a01 * 16.0, sU / 300.0), 16.0) * 9.0 + 1.2 * sin(a01 * 25.132741)) * wm * (0.55 + 0.45 * hb) * wkF;
float ripF = saturate(1.0 - fwidth(s / 60.0) * 0.8);
float rip = sin((s - T * 320.0) / 60.0) * (0.25 + 0.75 * saturate(band)) * ripF;
float h = 1.6 * fib + 0.9 * wrk + 0.7 * rip + 2.2 * wall + 0.5 * bubC;
float3 Pw = GetTranslatedWorldPosition(Parameters);
float3 dpx = ddx(Pw); float3 dpy = ddy(Pw);
float3 r1 = cross(dpy, n); float3 r2 = cross(n, dpx);
float det = dot(dpx, r1);
float3 sg = sign(det) * (ddx(h) * r1 + ddy(h) * r2);
float3 nb = normalize(abs(det) * n - sg);
if (any(isnan(nb))) nb = n;
float ndvb = saturate(abs(dot(nb, v)));
float relief = saturate(length(nb - n) * 3.0);

// 5) shield state (BP_TentacleVitals writes ShieldLost/ShieldHit on this MID): the gel tears open in patches as it
//    loses HP (glowing torn rims), flashes on every hit, and when empty bursts and melts away over 1.6 s.
float shf = saturate(1.0 - SLost / max(SMax, 1.0));
float since = T - SHit;
float flash = (since >= 0.0) ? exp(-since * 5.0) : 0.0;
float tearN = J.vn(float2(a01 * 10.0, sU / 260.0), 10.0) * 0.75 + J.vn(float2(a01 * 30.0, sU / 90.0), 30.0) * 0.25;
float tearT = shf * 1.1 - 0.05;
float hole = smoothstep(tearT - 0.025, tearT + 0.025, tearN);
float tornRim = saturate(1.0 - abs(tearN - tearT) / 0.05) * step(0.001, 1.0 - shf);
float gone = (shf <= 0.0001) ? saturate(since / 1.6) : 0.0;
float keep = 1.0 - hole;

// uneven membrane thickness: thick/thin patches drifting slowly
float thick = 0.65 + 0.7 * J.vn(float2(a01 * 5.0, sU / 650.0 + T * 0.012), 5.0);
float act = 1.0 + 0.6 * hb;
float pathC = min(path, 2.4);
// thick-gel edge: a darker absorbing band where the line of sight runs through the whole jelly depth, then a thin wet
// highlight right at the silhouette - how thick clear gel reads (instead of a milky haze)
float depthBand = exp(-pow((rim - 0.74) / 0.11, 2.0));
float edgeLine = smoothstep(0.93, 0.995, rim);
float dens = (0.156 * pathC) * thick + 0.039 + wall * (0.07 + 0.015 * pathC) + vein * 0.30 + spore * 0.10 + nuc * 0.05 + band * 0.06
           + rim * rim * 0.06 + depthBand * 0.16 + bubR * 0.10 + relief * 0.06;
dens *= lerp(1.0, 0.6, tip);
dens = dens * keep + tornRim * 0.35 + flash * 0.12;
float face = smoothstep(0.2, 0.55, saturate(length(SA.yz) * 2.0 - 1.0));   // 0 on spike blades (see JellyShellVS)
Op = saturate(1.1 * (1.0 - exp(-dens * 1.6))) * DF * saturate((CamD - 60.0) / 300.0) * (1.0 - gone) * face;

float lum = dot(Green, float3(0.3, 0.59, 0.11));
float3 deep = lerp(lum.xxx, Green, 1.05) * 0.35;                    // absorbing gel: thicker = darker, more saturated
float3 vessel = lerp(deep, float3(0.30, 0.05, 0.04), 0.4);           // capillary blood, pulled toward the tier colour
// gel body: a tier-tinted scattering volume (light diffuses inside it) so it reads as dense jelly, not clear glass
BC = lerp(lerp(Green * 0.24, Green * 0.34, saturate(thick - 0.65)), deep * 0.30, saturate(rim * 1.2));
BC = lerp(BC, deep * 0.18, depthBand * 0.7);
BC = lerp(BC, vessel * 0.45, saturate(vein * 0.8));                 // blood absorbs: vessels read dark, never pale
BC *= lerp(1.12, 0.85, saturate(thick - 0.65));
// refraction: wrinkles and ripples distort what is behind the membrane (the main "transparent skin" cue)
Rf = 1.0 + (0.40 * rim + 0.06 * depthBand + 0.06 * wall + 0.04 * band + 0.03 + 0.05 * relief + 0.015 * h) * keep * (1.0 - gone);

float3 glow = max(lerp(lum.xxx, Green, 0.9) * 1.1, 0.0);
float3 em = Green * wall * (0.04 + 0.05 * band) * act * keep;          // cell seams: mostly seen as relief in the glints, faint glow only
em += deep * 0.05 * pow(rim, 2.0) * keep;
em += glow * tornRim * 1.2 + glow * flash * (0.25 + wall * 1.5);
em += lerp(glow, vessel * 2.2, 0.45) * (vein * (0.10 + 0.55 * flow + 0.22 * hb) + vcore * (0.12 + 0.6 * flow)) * keep;   // blood pumped up the capillaries
em += glow * nuc * (0.03 + 0.06 * hb) * keep;
em += glow * spore * 0.12 * keep;
em += glow * band * 0.035 * pathC * keep;
em += Green * 0.016 * pathC * thick * act * keep;                      // inner scatter glow, stronger where the gel is thick
em *= Inten * (1.0 - gone) * (1.0 + 2.0 * gone * (1.0 - gone)) * face;

// wet surface on the bumped normal: tight sun/sky glints that crawl over wrinkles, a soft broad sheen, fresnel sky
// reflection broken up by the relief (no clean outline), faint thin-film interference on the stretched skin
float3 L = normalize(float3(0.25, 0.15, 1.0));
float3 rv = reflect(-v, nb);
float rl = saturate(dot(rv, L));
float glint = pow(rl, 90.0);
float broad = pow(rl, 7.0);
float F = 0.02 + 0.98 * pow(1.0 - ndvb, 5.0);
float3 film = 0.85 + 0.15 * cos(6.2831853 * (thick * 1.6 + ndvb * 0.9 + float3(0.0, 0.33, 0.67)));
float3 wet = film * float3(0.72, 0.74, 0.70) * (glint * 0.45 + broad * 0.035 + F * 0.06 * (0.35 + 0.65 * relief));
wet += float3(0.85, 0.88, 0.85) * bubR * (0.08 + 0.5 * glint) + float3(1.0, 1.0, 0.95) * bubC * broad * 0.25;
wet += float3(0.75, 0.78, 0.74) * edgeLine * (0.025 + 0.10 * broad) * (0.5 + 0.5 * relief);
em += deep * depthBand * 0.06 * Inten * keep;                         // light trapped in the thick gel, tier tinted
em += wet * keep * face * (1.0 - gone);
return em;

