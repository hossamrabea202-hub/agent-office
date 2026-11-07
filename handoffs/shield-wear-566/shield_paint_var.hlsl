struct FShieldLib {
  float h21(float2 p) { p = frac(p * float2(233.34, 851.73)); p += dot(p, p + 23.45); return frac(p.x * p.y); }
  float vn(float2 p) {
    float2 i = floor(p), f = frac(p);
    float2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    return lerp(lerp(h21(i), h21(i + float2(1, 0)), u.x), lerp(h21(i + float2(0, 1)), h21(i + float2(1, 1)), u.x), u.y);
  }
  float fbm(float2 p) { float s = 0.0, a = 0.5; for (int k = 0; k < 5; k++) { s += a * vn(p); p = p * 2.03 + float2(17.1, 9.2); a *= 0.5; } return s / 0.97; }
  float scratches(float2 p, float seed) {
    float s = 0.0;
    for (int k = 0; k < 4; k++) {
      float ang = h21(float2(seed, k * 1.37)) * 3.14159;
      float2 d = float2(cos(ang), sin(ang));
      float2 q = p * (1.3 + k * 0.7) + seed * 3.1;
      float l = abs(frac(dot(q, float2(-d.y, d.x)) * 5.0 + vn(q * 1.7) * 0.8) - 0.5);
      float m = smoothstep(0.62, 0.78, vn(q * 0.9 + k * 4.3));
      s = max(s, (1.0 - smoothstep(0.0, 0.028, l)) * m);
    }
    return s;
  }
  // #566: a sword or axe cut: a tapered groove through the paint into the wood (uv in cm on the shield face)
  float cut(float2 uv, float seed, float c) {
    float a = 0.6 + (h21(float2(c * 1.9, seed * 3.3)) - 0.5) * 1.6;
    float2 dir = float2(cos(a), sin(a));
    float2 c0 = float2((h21(float2(seed, c + 5.1)) - 0.5) * 34.0, 8.0 - h21(float2(seed, c + 8.3)) * 34.0);
    float2 d = uv - c0;
    float along = dot(d, dir), across = dot(d, float2(-dir.y, dir.x));
    float len = 7.0 + h21(float2(c, seed + 2.2)) * 13.0;
    float w = 0.65 * saturate(1.0 - abs(along) / len);
    across += (vn(float2(along * 0.9, c * 3.0 + seed)) - 0.5) * 0.22;
    return (1.0 - smoothstep(w * 0.35, w + 0.02, abs(across))) * step(abs(along), len);
  }
  float3 bump(float h, float3 P, float3 N, float k) {
    float3 dpdx = ddx(P), dpdy = ddy(P);
    float dhx = ddx(h), dhy = ddy(h);
    float3 r1 = cross(dpdy, N), r2 = cross(N, dpdx);
    float det = dot(dpdx, r1);
    float3 g = sign(det) * (dhx * r1 + dhy * r2) / max(abs(det), 1e-8);
    return normalize(N - g * k);
  }
};
FShieldLib L;
// ---- #566 per-soldier variation -------------------------------------------------------------------
// Seed: WearSeed >= 0 is used as is (exactly 0 = the original M_Shield_Paint_AAA look).
// WearSeed < 0 (default -1) = automatic: hashed from the random Tint (0.55..1.15 per channel) and the random
// Wear (0..0.3) that BP_SoldierSword already sets on each soldier's dynamic instance, so every soldier gets his
// own shield with no new Blueprint nodes. (The old shader received Wear but never used it.)
float s0 = (Seed >= 0.0) ? Seed : frac(sin(dot(Tint, float3(12.9898, 78.233, 37.719)) + Wear * 91.7) * 43758.5453) * 0.999 + 0.001;
float sv = (s0 > 0.0) ? 1.0 : 0.0;
float r1 = L.h21(float2(s0, 0.11)), r2 = L.h21(float2(s0, 0.37)), r3 = L.h21(float2(s0, 0.73));
float r4 = L.h21(float2(s0, 0.91)), r5 = L.h21(float2(s0, 1.29));
float2 o = (float2(r1, r2) - 0.5) * 240.0 * sv;                 // moves the chip, dirt and paint-grain layout
float wearV = lerp(1.0, lerp(0.55, 1.4, r3), sv) + Wear * 1.5;   // how beaten this shield is (new to veteran)
float dirtV = lerp(1.0, lerp(0.6, 1.45, r4), sv);                // how dirty
float fade = sv * r5 * r5 * 0.3;                                 // sun bleach of the paint
float scrSeed = 1.7 + s0 * 37.0 * sv;                            // different scratch directions and places
// ---- the original shield, with the seed threaded through -------------------------------------------
float2 uv = LP.yz;
float t = saturate(-LP.z / 38.0);
float hw = 27.0 * (1.0 - pow(t, 1.9) * 0.97);
float edgeD = min(hw - abs(LP.y), 35.0 - LP.z);
float n1 = L.fbm((uv + o) * 0.11), n2 = L.fbm((uv + o) * 0.55 + 3.1), n3 = L.fbm((uv + o) * 2.3 + 7.7);
float seam = smoothstep(0.93, 0.99, abs(frac(LP.y / 9.0 + 0.5) - 0.5) * 2.0);
float3 wood = Texture2DSample(W, WSampler, float2(LP.y * 0.017, LP.z * 0.007)).rgb;
// edges chip first (impacts land on the rim), and a more beaten shield chips further in
float chipEdge = 1.0 - smoothstep(1.5, 1.5 + 7.0 * wearV, edgeD + (n2 - 0.5) * 9.0);
float chipT = (wearV - 1.0) * 0.09;
float chip = saturate(chipEdge * smoothstep(0.30, 0.50, n3) + smoothstep(0.76 - chipT, 0.80 - chipT, n2 * 0.55 + n3 * 0.62));
float scr = L.scratches(uv * 0.045 + o * 0.01, scrSeed);
scr = max(scr, L.scratches(uv * 0.07 + o * 0.013 + 5.3, scrSeed + 11.0) * saturate((wearV - 1.0) * 1.6));
float cuts = 0.0;
for (int c = 0; c < 3; c++) {
  float hc = L.h21(float2(s0 * 7.3, c * 2.71));
  float on = sv * step(hc, 0.15 + 0.35 * wearV - c * 0.22);
  cuts = max(cuts, L.cut(uv, s0, c) * on);
}
cuts *= step(0.8, edgeD);
float brush = L.vn(float2(LP.y * 0.8, LP.z * 0.045)) * 0.55 + L.vn(float2(LP.y * 2.4, LP.z * 0.11)) * 0.45;
float3 paint = float3(0.022, 0.058, 0.205) * (0.8 + brush * 0.38) * (0.88 + n1 * 0.28);
paint = lerp(paint, dot(paint, float3(0.3333, 0.3333, 0.3333)) * 1.25 + 0.012, fade);
paint = lerp(paint, paint * 0.6 + float3(0.018, 0.015, 0.011), smoothstep(0.55, 0.82, n1) * 0.55);
float dirt = saturate(saturate((1.0 - smoothstep(0.0, 9.0, edgeD)) * 0.55 + t * 0.4) * (0.55 + n2 * 0.7) * dirtV);
paint = lerp(paint, float3(0.032, 0.026, 0.019), dirt * 0.55);
paint *= 1.0 - seam * 0.55;
float3 col = lerp(paint, wood * 0.5, chip);
col = lerp(col, float3(0.30, 0.28, 0.25) * 0.75, scr * (1.0 - chip) * 0.65);
col = lerp(col, wood * 0.42, cuts);
Rough = lerp(lerp(lerp(0.34 + n2 * 0.16 + dirt * 0.25, 0.86, chip), 0.62, scr), 0.8, cuts);
float h = (1.0 - chip) * 0.6 - seam * 0.9 + brush * 0.07 - scr * 0.3 + n3 * 0.06 + dot(wood, 0.33) * chip * 0.4 - cuts * 0.9;
Nrm = L.bump(h * 0.07, P, N, 1.0);
Metal = 0.0;
return col;
