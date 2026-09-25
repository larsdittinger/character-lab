"""Check the night elf's independently measured inputs before generating geometry."""
from pathlib import Path
import hashlib,json,math
from PIL import Image

R=Path(__file__).resolve().parents[1]
image=R/'references/elf/turnaround.png'
metadata=json.loads((R/'references/elf/turnaround.json').read_text())
config=json.loads((R/'config/elf-profiles.json').read_text())
rig=json.loads((R/'config/elf-rig.json').read_text())
im=Image.open(image).convert('RGB')
assert im.size==tuple(metadata['dimensions'])==(1536,1024)
fingerprint=hashlib.sha256(image.read_bytes()).hexdigest()
assert fingerprint==metadata['sha256'], 'The reference changed; remeasure before building'
assert config['topY']<config['groundY']<im.height
assert 0<config['frontCenterX']<config['sideOriginX']<config['backCenterX']<im.width
sections=0
for name,part in config['parts'].items():
 rows=part['rows'];assert len(rows)>=4,name
 for row in rows:
  assert len(row)==5 and all(math.isfinite(v) for v in row),name
  y,left,right,front,back=row
  assert config['topY']<=y<=config['groundY'] and 0<left<right<im.width and 0<front<back<im.width,name
 assert all(a[0]<b[0] for a,b in zip(rows,rows[1:])),name
 if part.get('paired'):assert all(row[1]>config['frontCenterX'] for row in rows),name
 sections+=len(rows)
for name,bone in rig['bones'].items():
 assert math.dist(bone['head'],bone['tail'])>.01,name

# These guard observed source ownership at ear, scalp, cloak and background edges.
guards=[('front ear',365,50,True),('front ear fringe',373,50,False),
 ('profile ear',840,40,True),('profile ear fringe',845,40,False),
 ('face',281,100,True),('silver crown',281,30,True),
 ('rear cloak',1253,500,True),('front cuirass',300,300,True),
 ('studio background',550,300,False)]
out=[]
for label,x,y,should_be_material in guards:
 rgb=im.getpixel((x,y));neutral=max(rgb)-min(rgb)<8 and 175<sum(rgb)/3<220
 passed=(not neutral)==should_be_material
 out.append(dict(label=label,xy=[x,y],rgb=rgb,expected='material' if should_be_material else 'background',passed=passed))
 assert passed,label
report=dict(passed=True,sourceSha256=fingerprint,configSha256=hashlib.sha256((R/'config/elf-profiles.json').read_bytes()).hexdigest(),dimensions=im.size,profileTypes=len(config['parts']),measuredSections=sections,guards=out,scope='Input and sampled source ownership; a passing guard is not a visual texture review.')
(R/'review/elf/input-validation.json').write_text(json.dumps(report,indent=2))
(R/'review/elf/projection.json').write_text(json.dumps({
 'passed':all(guard['passed'] for guard in out),
 'sourceSha256':fingerprint,
 'semanticSourceGuards':out,
 'guardCount':len(out),
 'scope':'Checks authored source pixels at known part boundaries. The rendered front, profile, three-quarter and back views remain the visual quality test.'
},indent=2))
print('ELF INPUT PASS',report['profileTypes'],'part types',sections,'sections',len(out),'source guards')
