"""Measured reconstruction of the independent copper ranger turnaround.
The calibrated pixel coordinates are specific to references/ranger/turnaround.png.
No runtime generation; all source projections have semantic ownership.
"""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1]
C=json.loads((R/'config/ranger-profiles.json').read_text());S=C['heightMeters']/(C['groundY']-C['topY']);CX=C['frontCenterX'];SIDE=C['sideOriginX'];BACK=C['backCenterX'];N=64
src=np.asarray(Image.open(R/'references/ranger/turnaround.png').convert('RGB'),float)/255
parts=[];textures=[]
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def interp(t,x,y):
 h=np.diff(x);d=np.diff(y)/h;m=np.zeros_like(y);m[0]=d[0];m[-1]=d[-1]
 for k in range(1,len(y)-1):
  if d[k-1]*d[k]>0:m[k]=(h[k-1]+h[k])/(h[k-1]/d[k-1]+h[k]/d[k])
 i=np.clip(np.searchsorted(x,t)-1,0,len(x)-2);u=(t-x[i])/h[i]
 return (2*u**3-3*u**2+1)*y[i]+(u**3-2*u**2+u)*h[i]*m[i]+(-2*u**3+3*u**2)*y[i+1]+(u**3-u**2)*h[i]*m[i+1]
def sample(x,y,source=src):
 x=np.clip(x,1,source.shape[1]-2);y=np.clip(y,1,source.shape[0]-2);a=x.astype(int);b=y.astype(int);u=(x-a)[...,None];v=(y-b)[...,None]
 return (source[b,a]*(1-u)+source[b,a+1]*u)*(1-v)+(source[b+1,a]*(1-u)+source[b+1,a+1]*u)*v
def hair_projection_source():
 # Semantic edge padding uses the nearest observed copper pixel in the same scanline.
 # It never paints studio grey/skin onto scalp; the original image stays untouched.
 out=src.copy()
 for x0,x1 in [(245,385),(685,848),(1150,1290)]:
  patch=src[17:148,x0:x1];valid=(patch[...,0]-patch[...,1]>.13)&(patch[...,1]-patch[...,2]>.035)&(patch[...,2]<.37)
  ys=np.flatnonzero(valid.any(axis=1))
  for y in range(131):
   vy=int(ys[np.argmin(abs(ys-y))]);xs=np.flatnonzero(valid[vy]);grid=np.arange(x1-x0);idx=np.searchsorted(xs,grid);right=xs[np.minimum(idx,len(xs)-1)];left=xs[np.maximum(idx-1,0)];nearest=np.where(abs(grid-left)<abs(grid-right),left,right)
   out[y+17,x0:x1]=patch[vy,nearest]
 return out
hair_source=hair_projection_source()
def sanitize(col,base):
 # Neutral gray studio background never belongs to any anatomical surface.
 gray=(col.max(axis=-1)-col.min(axis=-1)<.10)&(col.min(axis=-1)>.42)
 col[gray]=base;return col

def loft(name,cfg,mirror=False):
 p=np.array(cfg['rows'],float);assert np.all(np.diff(p[:,0])>0),name
 rows=cfg.get('samples',48);flat=cfg.get('exponent',.8);face=cfg.get('zone')=='face';base=np.array(cfg['color'])/255
 yy=np.linspace(p[0,0],p[-1,0],rows);l,r,f,b=[interp(yy,p[:,0],p[:,i]) for i in range(1,5)]
 tt=np.linspace(0,2*np.pi,N+1);co=np.cos(tt);si=np.sin(tt);si[0]=si[-1]=0
 xx=(l[:,None]+r[:,None])/2+(r-l)[:,None]*co/2
 zpx=(f[:,None]+b[:,None])/2-(b-f)[:,None]*np.sign(si)*abs(si)**flat/2
 zz=(SIDE-zpx)*S
 if face:
  X=xx-CX;Y=yy[:,None]
  relief=(8*np.exp(-(X/8)**2-((Y-108)/19)**2)+7*np.exp(-(X/10)**2-((Y-120)/6)**2)+2*np.exp(-(X/15)**2-((Y-135)/6)**2)-2*np.exp(-((abs(X)-20)/8)**2-((Y-95)/6)**2))*S
  zz+=relief*np.maximum(si,0)[None,:]**6
 pos=np.stack(((xx-CX)*S,np.broadcast_to((C['groundY']-yy[:,None])*S,xx.shape),zz),axis=-1)
 # Model head volume independently of image sampling. Keep facial landmarks and UV
 # coordinates on their measured pixels while widening the rendered cranium.
 head_scale=C.get('headWidthScale',1)
 if face:pos[:,:,0]*=head_scale
 elif cfg.get('zone')=='ear':pos[:,:,0]+=(head_scale-1)*58*S
 elif name.startswith('Neck'):pos[:,:,0]*=1+(head_scale-1)*.5
 if mirror:pos[:,:,0]*=-1
 vertices=pos.reshape(-1,3).tolist();faces=[]
 for j in range(rows-1):
  for i in range(N):
   ids=[j*(N+1)+i,j*(N+1)+i+1,(j+1)*(N+1)+i+1,(j+1)*(N+1)+i]
   if mirror:ids.reverse()
   faces.append(ids)
 for j,reverse in [(0,True),(rows-1,False)]:
  idx=len(vertices);vertices.append(np.mean(pos[j,:-1],axis=0).tolist())
  for i in range(N):
   ids=[idx,j*(N+1)+i,j*(N+1)+i+1]
   if reverse^mirror:ids.reverse()
   faces.append(ids)
 W,H=384,512;theta=np.linspace(0,2*np.pi,W);co=np.cos(theta);si=np.sin(theta)
 ty=np.linspace(p[0,0],p[-1,0],H);l,r,f,b=[interp(ty,p[:,0],p[:,i]) for i in range(1,5)]
 xp=(l[:,None]+r[:,None])/2+(r-l)[:,None]*co/2;yp=np.broadcast_to(ty[:,None],xp.shape);xp=np.clip(xp,l[:,None]+1.5,np.maximum(l[:,None]+1.5,r[:,None]-1.5))
 px=(f[:,None]+b[:,None])/2-(b-f)[:,None]*np.sign(si)*abs(si)**flat/2
 rear_x=BACK-(xp-CX);rear_y=yp
 if face:
  registration=np.asarray(C['rearHeadRegistration'],float)
  back_l=np.interp(yp,registration[:,0],registration[:,1]);back_r=np.interp(yp,registration[:,0],registration[:,2])
  unit=(xp-(l[:,None]+r[:,None])/2)/np.maximum(1,(r-l)[:,None]/2)
  rear_x=(back_l+back_r)/2-unit*(back_r-back_l)/2
  rear_y=np.interp(yp,[17,30,50,160],[20,32,50,160])
 front=sanitize(sample(xp,yp),base);rear=sanitize(sample(rear_x,rear_y),base)
 if name.startswith('Neck'):
  # Pale cloth is valid material, not studio background. Sample the actual collar
  # within its measured neck/cloth silhouette instead of colour-thresholding it.
  front=sample(xp,yp);rear=sample(rear_x,rear_y)
 if face:
  for colors,cutoff in [(front,92),(rear,144)]:
   fallback=np.max(abs(colors-base),axis=-1)<.001
   colors[fallback&(yp<cutoff)]=np.array([.45,.20,.11])
  for center,fill_x in [(365,351),(269,283)]:
   radius=np.sqrt(((xp-center)/13)**2+((yp-108)/23)**2)
   mask=(1-smooth((radius-.85)/.28))[...,None]
   front=front*(1-mask)+sample(np.full(xp.shape,fill_x),yp)*mask
 zone=cfg.get('zone','body');side=np.broadcast_to(base,front.shape).copy()
 if cfg.get('side',False):
  if face:
   sy=np.interp(yp,[17,48,75,95,120,135,160],[17,48,73,94,115,132,158])
   px+=np.interp(yp,[48,75,95,120,135,159],[0,2,10,3,0,0]);side=sanitize(sample(px,sy),base)
   fallback=np.max(abs(side-base),axis=-1)<.001;side[fallback&(yp<86)]=np.array([.45,.20,.11])
   # Ear pixels belong exclusively to the independent ear mesh, never cheek/skull.
   # The underlying anatomical patch uses smooth interpolated skin/hair around the ear,
   # preserving color variation in depth instead of extruding one sampled column.
   radius=np.sqrt(((px-779)/17)**2+((sy-105)/23)**2)
   mask=(1-smooth((radius-.84)/.30))[...,None]
   hair_weight=np.maximum(smooth((px-774)/13),1-smooth((sy-89)/12))[...,None]
   skin_fill=sample(755+(px-779)*.12,np.clip(sy,106,136))
   hair_fill=sample(806+(px-779)*.14,np.clip(sy,76,124),hair_source)
   fill=skin_fill*(1-hair_weight)+hair_fill*hair_weight
   side=side*(1-mask)+fill*mask
  elif zone=='hair':
   side=sanitize(sample(np.maximum(px,800),yp),base)
  elif name.startswith('Neck'):
   # Preserve the diagonal cloth edge through the actual two-dimensional profile;
   # the measured visible domain excludes studio background at its boundary.
   valid_y=[145,153,161,175,190,205]
   valid_left=np.interp(yp,valid_y,[745,749,751,743,731,719])+3
   valid_right=np.interp(yp,valid_y,[804,808,813,820,826,829])-3
   side=sample(np.clip(px,valid_left,valid_right),yp)
  else:side=sanitize(sample(px,yp),base)
 w=smooth((abs(co)-cfg.get('blendStart',.56))/(cfg.get('blendEnd',.86)-cfg.get('blendStart',.56)))[None,:,None]
 color=front*(1-w)+side*w
 if zone=='hair':
  # Rear cap only owns hair pixels; samples never visit ear, face, or neck.
  hair_x=np.clip(px,805,826);color=sanitize(sample(hair_x,np.clip(yp,25,130)),base)
 elif zone=='ear':
  # Front and profile each own their corresponding surface of the real ear mesh.
  front_ear=sample(xp,yp);profile_ear=sample(np.clip(px,770,789),np.clip(yp,91,121))
  color=front_ear*(1-w)+profile_ear*w
 if cfg.get('rear',True):
  rw=smooth((-si-.02)/.38)[None,:,None];color=color*(1-rw)+rear*rw
 if name.startswith('Thigh'):
  # Upper trouser volume is occluded by the tunic in the source; projected leather
  # would create a rectangular painted cap. Authored fabric continues under it.
  hidden=smooth((495-yp)/35)[...,None];color=color*(1-hidden)+base[None,None,:]*hidden
 if zone=='face':
  # One continuous scalp/head mesh prevents overlapping hair caps and forehead seams.
  # The generated rear view owns the whole posterior scalp.
  gray=(color.max(axis=-1)-color.min(axis=-1)<.13)&(color.min(axis=-1)>.30)&(yp<70)
  color[gray]=np.array([.45,.20,.11])
  # Crown/profile silhouettes are subpixel and differ across the generated views.
  # Replace only invalid hair-domain pixels with nearby observed copper strands.
  hair_domain=(yp<52)|((abs(co)[None,:]>.80)&(yp<84))|((si[None,:]<-.05)&(yp<139))
  hf=sample(np.clip(xp,245,384),np.clip(yp,17,147),hair_source)
  hs=sample(np.clip(px,685,847),np.clip(yp,17,147),hair_source)
  hb=sample(np.clip(rear_x,1150,1289),np.clip(rear_y,17,147),hair_source)
  hr=smooth((-si-.02)/.38)[None,:,None];hairfill=(hf*(1-w)+hs*w)*(1-hr)+hb*hr
  color[hair_domain]=hairfill[hair_domain]
 if zone=='hair':
  gray=(color.max(axis=-1)-color.min(axis=-1)<.13)&(color.min(axis=-1)>.30);color[gray]=base
 color=np.clip(color,0,1);textures.append(Image.fromarray(np.uint8(color*255)))
 uv=[[i/N,j/(rows-1)] for j in range(rows) for i in range(N+1)]+[[.25,0],[.25,1]]
 parts.append(dict(name=name,vertices=vertices,faces=faces,uv=uv,material='Ranger projection',zone=zone))
for name,cfg in C['parts'].items():
 if cfg.get('paired'):
  # Measurements use image-right, which is anatomical LEFT in a front view.
  loft(name+' L',cfg);loft(name+' R',cfg,True)
 else:loft(name,cfg)
cols=5;cw,ch=400,528;atlas=Image.new('RGB',(cols*cw,math.ceil(len(parts)/cols)*ch),(75,43,36))
for k,(part,tex) in enumerate(zip(parts,textures)):
 x=(k%cols)*cw;y=(k//cols)*ch;atlas.paste(tex,(x+8,y+8))
 atlas.paste(tex.crop((0,0,1,512)).resize((8,512)),(x,y+8));atlas.paste(tex.crop((383,0,384,512)).resize((8,512)),(x+392,y+8))
 atlas.paste(atlas.crop((x,y+8,x+cw,y+9)).resize((cw,8)),(x,y));atlas.paste(atlas.crop((x,y+519,x+cw,y+520)).resize((cw,8)),(x,y+520))
 part['uv']=[[(x+8+u*383)/atlas.width,1-(y+8+v*511)/atlas.height] for u,v in part['uv']]
atlas.save(R/'textures/ranger-projection.png');(R/'assets/ranger-model.json').write_text(json.dumps(dict(scale=S,parts=parts),separators=(',',':')))
report=dict(parts=len(parts),vertices=sum(len(p['vertices']) for p in parts),atlasSize=atlas.size,scale=S,frontCenter=CX,sideOrigin=SIDE,backCenter=BACK,source='Independent new generated reference; individual silhouette measurements in config/ranger-profiles.json',limitations='Manually authored unseen surfaces; image-projected skin/hair; no facial deformation.')
(R/'review/ranger/construction.json').write_text(json.dumps(report,indent=2));print(report)
