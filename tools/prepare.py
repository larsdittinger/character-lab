from pathlib import Path
from PIL import Image
import shutil, json
R=Path(__file__).resolve().parents[1]
raw=R/'references/gemini-original.png'
if not raw.exists(): shutil.copy(R/'references/knight-turnaround.png',raw)
im=Image.open(raw)
# Gemini returned a duplicate profile on the right. Preserve raw and remove only that redundant panel.
im.crop((0,0,round(im.width*1420/1907),im.height)).save(R/'references/knight-turnaround.png')
im.resize((1907,1280),Image.Resampling.LANCZOS).save(R/'references/calibration.png')
cal=im.resize((1907,1280),Image.Resampling.LANCZOS)
cal.crop((89,72,899,1215)).save(R/'references/front-calibrated.png')
cal.crop((1050,72,1410,1215)).save(R/'references/side-calibrated.png')
(R/'references/calibration.json').write_text(json.dumps({'originalSize':im.size,'workingSize':[1907,1280],'frontCenterX':494,'sideOriginX':1230,'groundY':1215,'topY':72,'heightMeters':2.5,'duplicateProfileRemoved':True},indent=2))
print('Prepared two-view reference',Image.open(R/'references/knight-turnaround.png').size)
