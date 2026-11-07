# Blender python: blender -b --factory-startup -P analyze.py -- BC.png ORM.png
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--')+1:]
def load(p):
    im = bpy.data.images.load(p); im.colorspace_settings.name='Non-Color'; w,h=im.size
    x=np.empty(w*h*4,np.float32); im.pixels.foreach_get(x); return x.reshape(h,w,4)[...,:3]
bc, orm = load(a[0]), load(a[1])
used = (bc.max(-1)>0.002)|(orm.max(-1)>0.002)
def lum(c):
    lin=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4); Y=lin@np.array([.2126,.7152,.0722])
    return np.where(Y<=0.0031308,12.92*Y,1.055*Y**(1/2.4)-0.055)*255
import colorsys
mx=bc.max(-1); mn=bc.min(-1); sat=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0)
r,g,b=bc[...,0],bc[...,1],bc[...,2]
hue=(np.degrees(np.arctan2(np.sqrt(3)*(g-b),2*r-g-b))%360)
L=lum(bc); M=orm[...,2]; R=orm[...,1]; AO=orm[...,0]
print('used %.1f%%'%(used.mean()*100))
print('metal hist (used)', np.histogram(M[used],bins=10,range=(0,1))[0])
# regions
reg={}
reg['steel']   = used&(M>0.5)&((hue>180)&(hue<260)|(sat<0.15))
reg['brass_m'] = used&(M>0.5)&(hue>20)&(hue<60)&(sat>=0.15)
reg['darkwood']= used&(M<=0.5)&((hue<20)|(hue>340))&(sat>0.4)
reg['tanwood'] = used&(M<=0.5)&(hue>=20)&(hue<60)&(sat>0.35)
reg['bone']    = used&(sat<=0.35)&(hue>=20)&(hue<70)&(L>120)&(M<=0.5)
reg['greyNM']  = used&(M<=0.5)&((hue>180)&(hue<260)|(sat<0.15))
tot=0
for k,m in reg.items():
    n=m.sum(); tot+=n
    if n==0: print(k,'0'); continue
    p=lambda x:np.percentile(x[m],[5,50,95]).round(2)
    print(k,'%.1f%%'%(n/used.sum()*100),'L',p(L).round(0),'sat',p(sat),'hue',p(hue).round(0),'R',p(R),'M',p(M),'AO',p(AO),'rgb50',np.median(bc[m],0).round(3))
print('classified %.1f%%'%(tot/used.sum()*100))
mid=used&(M>0.1)&(M<0.9); print('mid-metal %.1f%%'%(mid.sum()/used.sum()*100),'their hue50',np.median(hue[mid]),'L50',np.median(L[mid]))
