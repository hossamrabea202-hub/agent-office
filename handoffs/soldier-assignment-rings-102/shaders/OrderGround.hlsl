// Custom node inputs: UV(float2), Style(float), Tint(float3), Strength(float), Show(float).
// Returns linear RGB + coverage alpha. Style IDs are semantic, NOT game order codes.
struct FOrderMarks102
{
    float Line(float2 p, float2 a, float2 b, float w)
    {
        float2 ab=b-a;
        float t=saturate(dot(p-a,ab)/max(dot(ab,ab),0.00001));
        return 1-smoothstep(w,w+0.04,length(p-a-t*ab));
    }
    float Shield(float2 p)
    {
        float m=Line(p,float2(-0.5,-0.55),float2(0.5,-0.55),0.08);
        m=max(m,Line(p,float2(-0.5,-0.55),float2(-0.43,0.20),0.08));
        m=max(m,Line(p,float2(0.5,-0.55),float2(0.43,0.20),0.08));
        m=max(m,Line(p,float2(-0.43,0.20),float2(0,0.65),0.08));
        return max(m,Line(p,float2(0.43,0.20),float2(0,0.65),0.08));
    }
    float Icon(float2 p, float s)
    {
        if(s<0.5) return max(max(1-smoothstep(0.12,0.17,length(p-float2(-0.5,0))),1-smoothstep(0.12,0.17,length(p))),1-smoothstep(0.12,0.17,length(p-float2(0.5,0))));
        if(s<1.5) // follow: double chevron
        {
            float m=max(Line(p,float2(-0.5,0),float2(0,-0.5),0.09),Line(p,float2(0,-0.5),float2(0.5,0),0.09));
            return max(m,max(Line(p,float2(-0.5,0.5),float2(0,0),0.09),Line(p,float2(0,0),float2(0.5,0.5),0.09)));
        }
        if(s<2.5) return Shield(p);
        if(s<3.5) return 1-smoothstep(0.075,0.11,abs(max(abs(p.x),abs(p.y))-0.48));
        if(s<4.5) // patrol: broken circular route with arrow
        {
            float arc=(1-smoothstep(0.08,0.12,abs(length(p)-0.5)))*step(-0.2,p.x);
            return max(arc,max(Line(p,float2(-0.1,-0.49),float2(0.2,-0.7),0.08),Line(p,float2(-0.1,-0.49),float2(0.2,-0.25),0.08)));
        }
        if(s<5.5) // cannon crew: target/aiming mark
        {
            float m=1-smoothstep(0.055,0.09,abs(length(p)-0.36));
            m=max(m,Line(p,float2(-0.7,0),float2(0.7,0),0.055));
            return max(m,Line(p,float2(0,-0.7),float2(0,0.7),0.055));
        }
        if(s<6.5) // strike team: crossed blades
        {
            float m=max(Line(p,float2(-0.55,-0.6),float2(0.5,0.6),0.075),Line(p,float2(0.55,-0.6),float2(-0.5,0.6),0.075));
            m=max(m,Line(p,float2(-0.6,0.25),float2(-0.15,0.6),0.075));
            return max(m,Line(p,float2(0.6,0.25),float2(0.15,0.6),0.075));
        }
        return max(Shield(p*1.5+float2(0.4,0)),Shield(p*1.5-float2(0.4,0)));
    }
    float Pattern(float a,float s)
    {
        if(s<0.5) return 1-smoothstep(0.45,0.55,frac(a*16));
        if(s<1.5) return 1;
        if(s<2.5) return 1-smoothstep(0.80,0.87,frac(a*4));
        if(s<3.5) return 1-smoothstep(0.60,0.68,frac(a*8));
        if(s<4.5) return 1-smoothstep(0.40,0.52,frac(a*20));
        if(s<5.5) return 1;
        if(s<6.5) return 1-smoothstep(0.80,0.88,frac(a*2));
        return 1-smoothstep(0.80,0.87,frac(a*4));
    }
    float3 Color(float s)
    {
        if(s<0.5) return float3(0.35,0.38,0.34);
        if(s<1.5) return float3(0.21,0.46,0.64);
        if(s<2.5) return float3(0.56,0.47,0.23);
        if(s<3.5) return float3(0.48,0.53,0.47);
        if(s<4.5) return float3(0.25,0.49,0.30);
        if(s<5.5) return float3(0.60,0.34,0.17);
        if(s<6.5) return float3(0.59,0.24,0.20);
        return float3(0.42,0.33,0.58);
    }
};
FOrderMarks102 marks;
float style=clamp(floor(Style+0.5),0,7);
float2 p=(UV-0.5)*2;
float r=length(p);
float aa=max(fwidth(r),0.001);
float a=frac(atan2(p.y,p.x)/6.28318530718+1);
float ring=(1-smoothstep(0.020,0.020+aa,abs(r-0.78)))*marks.Pattern(a,style);
float fine=(1-smoothstep(0.006,0.006+aa,abs(r-0.73)))*0.20;
float icon=marks.Icon((UV-float2(0.5,0.82))/0.075,style);
float mask=saturate(max(max(ring,fine),icon))*saturate(Strength)*saturate(Show);
return float4(marks.Color(style)*Tint,mask);
