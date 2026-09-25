"""Download the free official animation archives through itch.io's normal free-download flow.
No login, paid files, third-party mirrors or executable content. Existing archives are reused.
"""
from pathlib import Path
import urllib.request,urllib.parse,http.cookiejar,re,json,hashlib,zipfile,datetime
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'animations/source'
PACKS=[('quaternius-ual1','Quaternius','https://quaternius.itch.io/universal-animation-library'),('quaternius-ual2','Quaternius','https://quaternius.itch.io/universal-animation-library-2'),('kaykit','Kay Lousberg','https://kaylousberg.itch.io/kaykit-character-animations')]
manifest=[]
for key,author,page in PACKS:
 folder=OUT/key;folder.mkdir(parents=True,exist_ok=True);archive=folder/'original.zip'
 if not archive.exists():
  jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));opener.addheaders=[('User-Agent','CharacterLab asset downloader')]
  html=opener.open(page,timeout=60).read().decode();csrf=re.search(r'name="csrf_token" value="([^"]+)"',html).group(1)
  body=urllib.parse.urlencode({'csrf_token':csrf}).encode();req=urllib.request.Request(page+'/download_url',data=body,headers={'Referer':page,'X-Requested-With':'XMLHttpRequest'});download_page=json.load(opener.open(req,timeout=60))['url']
  html=opener.open(download_page,timeout=60).read().decode();ids=re.findall(r'data-upload_id="(\d+)"',html)
  if len(ids)!=1:raise RuntimeError(f'{key}: expected exactly one free archive; found {len(ids)}. Inspect official page before changing downloader.')
  req=urllib.request.Request(page+'/file/'+ids[0]+'?source=game_download&as_props=1',data=b'',headers={'Referer':download_page,'X-Requested-With':'XMLHttpRequest'})
  target=json.load(opener.open(req,timeout=60))['url']
  with opener.open(target,timeout=120) as response: archive.write_bytes(response.read())
  print('DOWNLOADED',key,archive.stat().st_size,flush=True)
 with zipfile.ZipFile(archive) as z:
  for member in z.infolist():
   dest=(folder/member.filename).resolve()
   if not dest.is_relative_to(folder.resolve()):raise RuntimeError('Unsafe archive path')
  z.extractall(folder)
 manifest.append({'id':key,'author':author,'source':page,'license':'CC0-1.0','downloadedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(archive.relative_to(ROOT)),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'files':[str(p.relative_to(ROOT)) for p in folder.rglob('*') if p.is_file() and p!=archive]})
(ROOT/'animations/sources.json').write_text(json.dumps(manifest,indent=2)+'\n');print('All free packs saved.')
