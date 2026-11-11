from pathlib import Path
import json,hashlib
import numpy as np
from scipy import ndimage
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'artifacts';data=json.loads((A/'per_seed.json').read_text());summary=json.loads((A/'summary.json').read_text())
for model,recs in data.items():
 assert [x['seed'] for x in recs]==list(range(101,106))
 for rec in recs:
  im=Image.open(A/f'{model}_s{rec["seed"]}.png');assert im.size==((512,512) if model=='turbo' else (256,256))
  x=np.asarray(im.convert('RGB').resize((256,256)),dtype=float)/255;y=.299*x[...,0]+.587*x[...,1]+.114*x[...,2]
  assert abs(y.std()-rec['contrast'])<1e-10
  assert abs(np.hypot(ndimage.sobel(y,axis=0),ndimage.sobel(y,axis=1)).mean()/8-rec['edge'])<1e-10
  assert rec['seconds']>0
for row in summary['rows']:
 m=row[0];a=np.array([x[m] for x in data['turbo']]);b=np.array([x[m] for x in data['amused']]);s=a.std(ddof=1);d=b.mean()-a.mean()
 assert np.allclose(row[1:6],[a.mean(),s,b.mean(),d,abs(d)/s]);assert row[6]==bool(abs(d)>2*s)
assert hashlib.sha256((R/'src/execute_lr10.py').read_bytes()).hexdigest()==json.loads((A/'passport.json').read_text())['source_sha256']
print('PASS: source SHA256, 10 PNG, per-seed edge/contrast, five summary metrics. CLIP and elapsed time not independently rerun.')
