"""Optional Gemini image request. Rebuilding the supplied model never calls this tool."""
import argparse, base64, datetime, io, json, os, re, urllib.request
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--prompt-file',type=Path,default=R/'config/turnaround-prompt.txt')
p.add_argument('--name',default='new-turnaround')
p.add_argument('--model',default='gemini-3.1-flash-image')
p.add_argument('--size',choices=['1K','2K','4K'],default='2K')
p.add_argument('--reference',type=Path,action='append',default=[])
p.add_argument('--dry-run',action='store_true')
a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+',a.name):p.error('name must be a simple filename stem')
out=R/'references'/(a.name+'.png')
if out.exists():p.error('Output already exists; choose another --name to preserve calibration')
parts=[{'text':a.prompt_file.read_text()}]
for ref in a.reference:
    im=Image.open(ref);b=io.BytesIO();im.save(b,format='PNG')
    parts.append({'inlineData':{'mimeType':'image/png','data':base64.b64encode(b.getvalue()).decode()}})
payload={'contents':[{'role':'user','parts':parts}], 'generationConfig':{'responseModalities':['TEXT','IMAGE'],'imageConfig':{'imageSize':a.size,'aspectRatio':'3:2'}}}
if a.dry_run:
    print(json.dumps({'model':a.model,'size':a.size,'output':str(out),'referenceCount':len(a.reference),'promptCharacters':len(parts[0]['text']),'networkRequests':0},indent=2));raise SystemExit()
key=os.environ.get('GEMINI_API_KEY')
if not key and (R/'.env').exists():
    for line in (R/'.env').read_text().splitlines():
        if line.strip().startswith('GEMINI_API_KEY='):key=line.split('=',1)[1].strip().strip('"\'')
if not key:raise SystemExit('Set GEMINI_API_KEY or put it in this project’s .env')
url='https://generativelanguage.googleapis.com/v1beta/models/'+a.model+':generateContent'
req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key})
# One request; no automatic retries that could incur unreviewed duplicate costs.
with urllib.request.urlopen(req,timeout=240) as r:data=json.load(r)
images=[part['inlineData'] for c in data.get('candidates',[]) for part in c.get('content',{}).get('parts',[]) if 'inlineData' in part]
if not images:raise SystemExit('No image returned. Response metadata: '+str(data.get('promptFeedback',{})))
Image.open(io.BytesIO(base64.b64decode(images[0]['data']))).save(out)
metadata={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':a.model,'size':a.size,'prompt':parts[0]['text'],'references':[str(x.name) for x in a.reference],'usageMetadata':data.get('usageMetadata'),'actualBilledUsd':None,'returnedImages':len(images)}
out.with_suffix('.json').write_text(json.dumps(metadata,indent=2))
print('Saved',out,'; API usage metadata saved beside it. Invoice cost is not asserted.')
