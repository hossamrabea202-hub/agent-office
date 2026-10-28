// Custom node inputs: UV(float2), Style, Tint(float3), Strength, Show.
// UV.x follows the circle; UV.y follows the height of the shallow ribbon.
float style=clamp(floor(Style+0.5),0,7);
float3 color=float3(0.35,0.38,0.34);
if(style>=0.5&&style<1.5)color=float3(0.21,0.46,0.64);
if(style>=1.5&&style<2.5)color=float3(0.56,0.47,0.23);
if(style>=2.5&&style<3.5)color=float3(0.48,0.53,0.47);
if(style>=3.5&&style<4.5)color=float3(0.25,0.49,0.30);
if(style>=4.5&&style<5.5)color=float3(0.60,0.34,0.17);
if(style>=5.5&&style<6.5)color=float3(0.59,0.24,0.20);
if(style>=6.5)color=float3(0.42,0.33,0.58);
float pattern=1;
if(style<0.5)pattern=1-smoothstep(0.45,0.55,frac(UV.x*16));
if(style>=1.5&&style<2.5)pattern=1-smoothstep(0.80,0.87,frac(UV.x*4));
if(style>=2.5&&style<3.5)pattern=1-smoothstep(0.60,0.68,frac(UV.x*8));
if(style>=3.5&&style<4.5)pattern=1-smoothstep(0.40,0.52,frac(UV.x*20));
if(style>=5.5&&style<6.5)pattern=1-smoothstep(0.80,0.88,frac(UV.x*2));
if(style>=6.5)pattern=1-smoothstep(0.80,0.87,frac(UV.x*4));
float band=pow(saturate(1-abs(UV.y-0.42)*2.2),2);
float coverage=band*pattern*saturate(Show);
return float4(color*Tint*max(Strength,0),coverage*0.36);
