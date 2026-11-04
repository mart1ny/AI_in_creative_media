from pathlib import Path
import json,sys,hashlib,statistics
import numpy as np
from PIL import Image
from scipy import ndimage
R=Path(__file__).resolve().parents[1];A=R/'artifacts'
for mode in ['A','B']:
 records=json.loads((A/f'{mode}_per_seed.json').read_text());assert [x['seed'] for x in records]==list(range(101,106))
 for x in records:
  im=Image.open(A/f'{mode}_{x["seed"]}.png');assert im.size==(512,512)
  arr=np.asarray(im.convert('RGB'),dtype=float)/255;y=arr@np.array([.299,.587,.114])
  assert abs(y.std()-x['contrast'])<1e-10
  edge=np.hypot(ndimage.sobel(y,axis=0),ndimage.sobel(y,axis=1)).mean()/8
  assert abs(edge-x['edge'])<1e-10
records=[json.loads((A/f'{mode}_per_seed.json').read_text()) for mode in ['A','B']]
rows=json.loads((A/'comparison.json').read_text())['rows']
for r in rows:
 def pick(x):return x['sims'][3] if r[0]=='clip_target' else x['sims'][0] if r[0]=='clip_subject' else x[r[0]]
 a,b=[[pick(x) for x in xs] for xs in records];delta=np.mean(b)-np.mean(a);s=np.std(a,ddof=1)
 assert np.allclose(r[1:6],[np.mean(a),s,np.mean(b),delta,abs(delta)/s]);assert r[6]==bool(abs(delta)>2*s)
sys.path.insert(0,str(R/'src'));import lab09_llm as L
for m in ['zero','few','step']:
 paths=[R/'answers'/f'ctx1_{m}_r{i}.txt' for i in range(1,4)];saved=json.loads((R/'reports/llm_scores.json').read_text())[m]
 for key in ['k1','k2','k3']:assert saved[key]==statistics.mean(L.score_file(p,1)[key] for p in paths)
 assert saved['k4']==L.stability(paths)
print('PASS: 10 PNG, per-seed edge/contrast, summary statistics, nine answers and K1-K4. CLIP embeddings are not independently recomputed.')
