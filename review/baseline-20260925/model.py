"""Reference-driven lofts. Coordinates are measured on calibration.png, not inherited from forge.
Each profile is (image y, image left, image right, profile front x, profile back x).
Front/profile projections are blended into an ordinary UV atlas; hidden backs are authored.
"""
from pathlib import Path
import math,json
import numpy as np
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parents[1];S=2.5/(1215-72);N=64
FACE=json.loads((R/'config/face.json').read_text())
PROFILES=json.loads((R/'config/profiles.json').read_text())
src=np.array(Image.open(R/'references/calibration.png').convert('RGB'),dtype=float)/255
backsrc=np.array(Image.open(R/'references/knight-back.png').convert('RGB').resize((1280,1907),Image.Resampling.LANCZOS),dtype=float)/255
parts=[];textures=[]
def interp(t,x,y):
 # Shape-preserving cubic Hermite interpolation, no dependency beyond numpy.
 h=np.diff(x);delta=np.diff(y)/h;m=np.zeros_like(y);m[0]=delta[0];m[-1]=delta[-1]
 for k in range(1,len(y)-1):
  if delta[k-1]*delta[k]>0:m[k]=(h[k-1]+h[k])/(h[k-1]/delta[k-1]+h[k]/delta[k])
 i=np.clip(np.searchsorted(x,t)-1,0,len(x)-2);u=(t-x[i])/h[i]
 return (2*u**3-3*u**2+1)*y[i]+(u**3-2*u**2+u)*h[i]*m[i]+(-2*u**3+3*u**2)*y[i+1]+(u**3-u**2)*h[i]*m[i+1]
def sample(x,y,source=src):
 x=np.clip(x,1,source.shape[1]-2);y=np.clip(y,1,source.shape[0]-2);a=x.astype(int);b=y.astype(int);u=(x-a)[...,None];v=(y-b)[...,None]
 return (source[b,a]*(1-u)+source[b,a+1]*u)*(1-v)+(source[b+1,a]*(1-u)+source[b+1,a+1]*u)*v
def smooth(x):
 t=np.clip(x,0,1);return t*t*(3-2*t)
def multiband(a,b,mask):
 def blur(x,r):
  if r==0:return x
  return np.asarray(Image.fromarray(np.uint8(np.clip(x,0,1)*255)).filter(ImageFilter.GaussianBlur(r)),dtype=float)/255
 radii=FACE['pyramidRadii'];aa=[blur(a,r) for r in radii];bb=[blur(b,r) for r in radii];out=np.zeros_like(a)
 for i,r in enumerate(radii):
  la=aa[i]-(aa[i+1] if i+1<len(radii) else 0);lb=bb[i]-(bb[i+1] if i+1<len(radii) else 0)
  m=smooth((mask-.25)/.50) if i<2 else mask
  out+=la*(1-m)+lb*m
 return np.clip(out,0,1)
def loft(name,profile,base,side=True,mirror=False,flatten=.70,face=False,back=False,rows=65):
 p=np.array(profile,float);yy=np.linspace(p[0,0],p[-1,0],rows);channels=[interp(yy,p[:,0],p[:,i]) for i in range(1,5)];left,right,pfront,pback=channels
 # Theta 0 at the rightmost extent, pi/2 faces the front camera.
 tt=np.linspace(0,2*np.pi,N+1);ct=np.cos(tt);st=np.sin(tt);st[0]=st[-1]=0
 xx=(left[:,None]+right[:,None])/2+(right-left)[:,None]/2*ct
 front=(1230-pfront)*S;rear=(1230-pback)*S
 zz=(front[:,None]+rear[:,None])/2+(front-rear)[:,None]/2*np.sign(st)*np.abs(st)**flatten
 if face:
  # Nose bridge, tip, cheeks and lips: geometric relief in front of the facial plane.
  X=xx-494;Y=yy[:,None]
  relief=(13*np.exp(-(X/11)**2-((Y-178)/30)**2)+9*np.exp(-(X/14)**2-((Y-194)/10)**2)+3*np.exp(-(X/24)**2-((Y-216)/9)**2)-3*np.exp(-((np.abs(X)-23)/13)**2-((Y-165)/9)**2))*S
  zz+=relief*np.maximum(st,0)[None,:]**6
 pos=np.stack(((xx-494)*S,np.broadcast_to((1215-yy[:,None])*S,xx.shape),zz),axis=-1)
 if mirror:pos[:,:,0]*=-1
 vertices=pos.reshape(-1,3).tolist();faces=[];uv=[]
 for j in range(rows-1):
  for i in range(N):
   ids=[j*(N+1)+i,j*(N+1)+i+1,(j+1)*(N+1)+i+1,(j+1)*(N+1)+i]
   if mirror:ids.reverse()
   faces.append(ids)
 # Closed pole caps use a shared boundary ring, UV seams remain separately indexed.
 for j,reverse in [(0,True),(rows-1,False)]:
  c=np.mean(pos[j,:-1],axis=0);idx=len(vertices);vertices.append(c.tolist())
  for i in range(N):
   f=[idx,j*(N+1)+i,j*(N+1)+i+1]
   if reverse^mirror:f.reverse()
   faces.append(f)
 # Bake atlas patch at higher sampling density than the mesh.
 W=512;H=768;ty=np.linspace(p[0,0],p[-1,0],H);a,b,c,d=[interp(ty,p[:,0],p[:,i]) for i in range(1,5)];theta=np.linspace(0,2*np.pi,W);co=np.cos(theta);si=np.sin(theta)
 xp=(a[:,None]+b[:,None])/2+(b-a)[:,None]/2*co
 yp=np.broadcast_to(ty[:,None],xp.shape)
 # Inset at silhouette boundaries so white studio backdrop never enters UVs.
 xp=np.clip(xp,a[:,None]+2,np.maximum(a[:,None]+2,b[:,None]-2))
 col=sample(xp,yp)
 # Profile projection is appropriate only when that part is visible in the side reference.
 profileX=(c[:,None]+d[:,None])/2-(d-c)[:,None]/2*np.sign(si)*np.abs(si)**flatten
 if face:
  profileX+=np.interp(yp,FACE['depthWarpY'],FACE['sidePixelOffset'])
  sidecol=sample(profileX,np.interp(yp,FACE['frontY'],FACE['sideY']))
 else:sidecol=sample(profileX,yp)
 basecol=np.array(base)/255
 bad=np.min(col,axis=-1)>.82;col[bad]=basecol
 sidebad=np.min(sidecol,axis=-1)>.82;sidecol[sidebad]=basecol
 w=smooth((np.abs(co)-.65)/.30)[None,:,None]*(1 if side else 0)
 if face:
  w=smooth((np.abs(co)-FACE['blendStart'])/(FACE['blendEnd']-FACE['blendStart']))[None,:,None]
  col=multiband(col,sidecol,w)
 else:col=col*(1-w)+sidecol*w
 # No second face/chest painted onto the back. Hidden surfaces get hand-authored material color.
 rearweight=smooth((-si-.01)/.35)[None,:,None]
 shade=(.88+.12*np.cos((yp-p[0,0])/max(1,p[-1,0]-p[0,0])*np.pi)+.035*np.cos(xp*.09))[...,None]
 rearcolor=basecol[None,None,:]*shade
 by=np.interp(yp,[72,118,182,250,322,402,455,550,603,787,818,976,1092,1215],[86,156,246,355,458,568,645,779,862,1143,1190,1422,1680,1830])
 rearcolor=sample(644+(494-xp)*1.45,by,backsrc)
 badback=np.min(rearcolor,axis=-1)>.73;rearcolor[badback]=basecol
 if name=='Hair at rear of skull':
  # Side cap shares the facial profile source; rear projection takes over only behind the skull.
  col=sample(np.maximum(profileX,1240),yp) # Hair cap must not project a second ear onto its overlapping surface.
 col=col*(1-rearweight)+rearcolor*rearweight
 if 'hair' in name.lower():
  # Hair silhouette antialiasing from the white studio backdrop must not become white crown marks.
  halo=(col.min(axis=-1)>.38)&((col.max(axis=-1)-col.min(axis=-1))<.22)
  col[halo]=np.array([.29,.16,.085])
 col=np.clip(col*1.035,0,1)
 textures.append(Image.fromarray((col*255).astype('uint8')))
 for j in range(rows):
  for i in range(N+1):uv.append([i/N,j/(rows-1)])
 uv.extend([[.25,0],[.25,1]])
 parts.append(dict(name=name,vertices=vertices,faces=faces,uv=uv,material='Reference paint',projection='front/profile blended' if side else 'front/painted reverse'))

teal=[36,76,81];steel=[62,84,97];brown=[89,52,32];hair=[67,40,25];gold=[158,119,62]
# Torso profile measured between collar, breastplate, belt and hips.
loft('Torso · shaped breastplate',PROFILES['Torso · shaped breastplate'],teal,side=False,flatten=.5)
loft('Neck inside collar',PROFILES['Neck inside collar'],brown,side=False)
loft('Face · nose cheek and jaw relief',PROFILES['Face · nose cheek and jaw relief'],[133,83,51],side=True,flatten=FACE['crossSectionExponent'],face=True,rows=100)
loft('Sculpted hair',PROFILES['Sculpted hair'],hair,side=True,flatten=.65,rows=42)
# Additional back hair cap retains volume below the fringe without painting hair over the face.
loft('Hair at rear of skull',PROFILES['Hair at rear of skull'],hair,side=False,flatten=.8)
for mirror,tag in [(False,'R'),(True,'L')]:
 loft('Pauldron '+tag,PROFILES['Pauldron'],teal,side=True,mirror=mirror,flatten=.65,rows=70)
 loft('Upper arm '+tag,PROFILES['Upper arm'],teal,side=False,mirror=mirror)
 loft('Bracer '+tag,PROFILES['Bracer'],brown,side=True,mirror=mirror,flatten=.62)
 loft('Gauntlet palm '+tag,PROFILES['Gauntlet palm'],brown,side=True,mirror=mirror,flatten=.7)
 loft('Thumb '+tag,PROFILES['Thumb'],brown,side=False,mirror=mirror,rows=24)
 loft('Thigh '+tag,PROFILES['Thigh'],steel,side=False,mirror=mirror)
 loft('Hanging hip plate '+tag,PROFILES['Hanging hip plate'],steel,side=False,mirror=mirror,flatten=.45)
 loft('Knee armor '+tag,PROFILES['Knee armor'],steel,side=True,mirror=mirror,flatten=.55)
 loft('Greave '+tag,PROFILES['Greave'],steel,side=True,mirror=mirror,flatten=.64)
 loft('Armored boot '+tag,PROFILES['Armored boot'],steel,side=True,mirror=mirror,flatten=.53)
# Cloth panel: thin but actually three dimensional, front and reverse separated.
loft('Teal tabard',PROFILES['Teal tabard'],teal,side=False,flatten=.28)
loft('Rear teal tabard',PROFILES['Rear teal tabard'],teal,side=False,flatten=.28)

def relief(name,points,center,depths,bulge):
 # An actual raised armor detail, with projected color sampled from the source image.
 pts=np.array(points,float);cx,cy=center;x0,y0=pts.min(axis=0);x1,y1=pts.max(axis=0);n=len(pts)
 z=np.array(depths,float);verts=[[(x-494)*S,(1215-y)*S,d] for (x,y),d in zip(pts,z)]
 verts.append([(cx-494)*S,(1215-cy)*S,float(np.mean(z)+bulge)])
 verts.extend([[(x-494)*S,(1215-y)*S,d-.012] for (x,y),d in zip(pts,z)])
 verts.append([(cx-494)*S,(1215-cy)*S,float(np.mean(z)-.012)])
 faces=[]
 for i in range(n):
  j=(i+1)%n;faces.extend([[n,i,j],[2*n+1,n+1+j,n+1+i],[i,n+1+i,n+1+j,j]])
 uv=[[(x-x0)/(x1-x0),(y-y0)/(y1-y0)] for x,y in pts];uv.append([(cx-x0)/(x1-x0),(cy-y0)/(y1-y0)]);uv=uv+uv
 xx,yy=np.meshgrid(np.linspace(x0,x1,512),np.linspace(y0,y1,768));textures.append(Image.fromarray((np.clip(sample(xx,yy),0,1)*255).astype('uint8')))
 parts.append(dict(name=name,vertices=verts,faces=faces,uv=uv,material='Reference paint',projection='front relief'))
relief('Raised golden diamond crest',[(494,322),(449,389),(496,463),(538,389)],(494,389),[.274,.365,.327,.365],.065)
relief('Raised belt buckle',[(464,551),(517,551),(536,565),(536,609),(517,624),(461,620),(447,600),(447,571)],(493,586),[.280]*8,.025)

# Pack ordinary rectangular UV islands with padding. Color from original projections is baked offline.
cols=5;cellW=528;cellH=784;rows=math.ceil(len(parts)/cols);atlas=Image.new('RGB',(cols*cellW,rows*cellH),(48,67,68))
for k,(part,tex) in enumerate(zip(parts,textures)):
 x=(k%cols)*cellW;y=(k//cols)*cellH;atlas.paste(tex,(x+8,y+8))
 # Pixel gutters avoid seams in mip maps.
 atlas.paste(tex.crop((0,0,1,768)).resize((8,768)),(x,y+8));atlas.paste(tex.crop((511,0,512,768)).resize((8,768)),(x+520,y+8))
 atlas.paste(atlas.crop((x,y+8,x+528,y+9)).resize((528,8)),(x,y));atlas.paste(atlas.crop((x,y+775,x+528,y+776)).resize((528,8)),(x,y+776))
 part['uv']=[[(x+8+u*511)/atlas.width,1-(y+8+v*767)/atlas.height] for u,v in part['uv']]
atlas.save(R/'textures/knight-projection.png')
(R/'assets/model.json').write_text(json.dumps({'scale':S,'parts':parts},separators=(',',':')))
summary={'parts':len(parts),'vertices':sum(len(p['vertices']) for p in parts),'atlasSize':atlas.size,'construction':'individually traced front silhouettes, profile-calibrated depth, closed loft meshes','texture':'front/profile projection with supplementary Gemini back view, baked into one UV atlas'}
(R/'review/construction.json').write_text(json.dumps(summary,indent=2));print(summary)
