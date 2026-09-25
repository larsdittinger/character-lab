"""Night elf reconstruction from its own measured front, profile, and rear sheet."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1]
C=json.loads((R/'config/elf-profiles.json').read_text());S=C['heightMeters']/(C['groundY']-C['topY']);CX=C['frontCenterX'];SIDE=C['sideOriginX'];BACK=C['backCenterX'];N=64
src=np.asarray(Image.open(R/'references/elf/turnaround.png').convert('RGB'),float)/255
assert src.shape[:2]==(1024,1536), 'Night elf calibration belongs to its 1536 × 1024 reference'
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
def sanitize(col,base):
 # Neutral gray studio background never belongs to any anatomical surface.
 gray=(col.max(axis=-1)-col.min(axis=-1)<.055)&(col.min(axis=-1)>.74)
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
  relief=(8*np.exp(-(X/8)**2-((Y-96)/18)**2)+7*np.exp(-(X/9)**2-((Y-118)/7)**2)+2*np.exp(-(X/14)**2-((Y-144)/6)**2)-2*np.exp(-((abs(X)-19)/8)**2-((Y-79)/6)**2))*S
  zz+=relief*np.maximum(si,0)[None,:]**6
 pos=np.stack(((xx-CX)*S,np.broadcast_to((C['groundY']-yy[:,None])*S,xx.shape),zz),axis=-1)
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
  rear_y=np.interp(yp,[18,35,75,184],[20,36,76,184])
 front=sanitize(sample(xp,yp),base);rear=sanitize(sample(rear_x,rear_y),base)
 if face:
  # Separate pointed ears own the narrow overlap at either side of the skull.
  for center,fill_x in [(316,303),(246,258)]:
   radius=np.sqrt(((xp-center)/10)**2+((yp-76)/29)**2)
   mask=(1-smooth((radius-.83)/.32))[...,None]
   front=front*(1-mask)+sample(np.full(xp.shape,fill_x),yp)*mask
 zone=cfg.get('zone','body');side=np.broadcast_to(base,front.shape).copy()
 if cfg.get('side',False):
  if face:
   sy=np.interp(yp,[18,50,79,106,135,184],[18,51,77,105,134,184]);side=sanitize(sample(px,sy),base)
   # The visible profile ear is projected only onto its own pointed mesh.
   radius=np.sqrt(((px-780)/39)**2+((sy-77)/38)**2)
   mask=(1-smooth((radius-.82)/.30))[...,None]
   hair_weight=np.maximum(smooth((px-767)/24),1-smooth((sy-57)/15))[...,None]
   skin_fill=sample(np.full(px.shape,740),np.clip(sy+22,90,130))
   hair_fill=sample(np.full(px.shape,815),np.clip(sy+44,112,151))
   fill=skin_fill*(1-hair_weight)+hair_fill*hair_weight
   side=side*(1-mask)+fill*mask
  elif zone=='hair': side=sanitize(sample(np.clip(px,793,838),yp),base)
  elif name.startswith('Pauldron'):
   # Gold-trimmed profile cap is visible only on the shoulder, not the cloak behind it.
   side=sanitize(sample(np.clip(px,735,808),yp),base)
  elif name.startswith('Neck'): side=sanitize(sample(np.clip(px,715,802),yp),base)
  else: side=sanitize(sample(px,yp),base)
 w=smooth((abs(co)-cfg.get('blendStart',.56))/(cfg.get('blendEnd',.86)-cfg.get('blendStart',.56)))[None,:,None]
 color=front*(1-w)+side*w
 if zone=='hair':
  # Rear turnaround owns the hanging silver locks; the profile overlaps the ear.
  color=sample(np.clip(rear_x,1215,1270),np.clip(yp,84,170))
 elif zone=='ear':
  # Front and profile each own their corresponding surface of the real ear mesh.
  front_l=np.interp(yp,[50,59,72,86,99,105],[365,350,328,317,312,313])+1.5
  front_r=np.interp(yp,[50,59,72,86,99,105],[372,369,357,346,327,321])-1.5
  side_l=np.interp(yp,[50,59,72,86,99,105],[833,810,786,767,765,771])+2
  side_r=np.interp(yp,[50,59,72,86,99,105],[843,838,820,799,787,782])-2
  front_ear=sanitize(sample(np.clip(xp,front_l,front_r),yp),base)
  # The generated profile ear sits about ten pixels higher than the front ear.
  profile_ear=sanitize(sample(np.clip(px,side_l,side_r),yp-10),base)
  color=front_ear*(1-w)+profile_ear*w
 if cfg.get('rear',True):
  rw=smooth((-si-.02)/.38)[None,:,None];color=color*(1-rw)+rear*rw
 if name.startswith('Thigh'):
  hidden=smooth((481-yp)/35)[...,None];color=color*(1-hidden)+base[None,None,:]*hidden
 if face:
  # Keep the silver crown inside observed hair pixels in each source view.
  hair_front=sample(np.clip(xp,254,308),np.maximum(yp,29))
  hair_side=sample(np.clip(px,718,807),np.maximum(yp,30))
  hair_rear=sample(np.clip(rear_x,1212,1295),np.maximum(rear_y,29))
  hr=smooth((-si-.02)/.38)[None,:,None]
  hair=(hair_front*(1-w)+hair_side*w)*(1-hr)+hair_rear*hr
  crown=(1-smooth((yp-53)/21))[...,None]
  color=color*(1-crown)+hair*crown
 if zone=='cloak':
  # The cloak sits behind the body: its rear photograph owns both surfaces.
  color=sanitize(sample(np.clip(rear_x,1065,1443),yp),base)
 if zone=='hair':
  color=sanitize(color,base)
 color=np.clip(color,0,1);textures.append(Image.fromarray(np.uint8(color*255)))
 uv=[[i/N,j/(rows-1)] for j in range(rows) for i in range(N+1)]+[[.25,0],[.25,1]]
 parts.append(dict(name=name,vertices=vertices,faces=faces,uv=uv,material='Night elf projection',zone=zone))
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
atlas.save(R/'textures/elf-projection.png');(R/'assets/elf-model.json').write_text(json.dumps(dict(scale=S,parts=parts),separators=(',',':')))
report=dict(parts=len(parts),vertices=sum(len(p['vertices']) for p in parts),atlasSize=atlas.size,scale=S,frontCenter=CX,sideOrigin=SIDE,backCenter=BACK,source='references/elf/turnaround.png; hand measured in config/elf-profiles.json',limitations='Authored unseen cloak and hair surfaces; projected facial detail; no facial deformation or cloth collision.')
(R/'review/elf/construction.json').write_text(json.dumps(report,indent=2));print(report)
