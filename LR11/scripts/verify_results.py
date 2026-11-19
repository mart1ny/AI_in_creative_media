from pathlib import Path
import hashlib,json,numpy as np
from PIL import Image
import nbformat
r=Path(__file__).resolve().parents[1];a=r/'artifacts'
p=json.loads((a/'passport.json').read_text());data=json.loads((a/'per_seed.json').read_text());s=json.loads((a/'summary.json').read_text())
assert len(data)==10
assert set((x['regime'],x['seed']) for x in data)==set((n,i) for n in ['A','B'] for i in range(101,106))
for f,h in p['source_sha256'].items():assert hashlib.sha256((r/'src'/f).read_bytes()).hexdigest()==h
for row in s['rows']:
 k,ma,sd,mb,d,q,flag=row
 av=np.array([x['metrics'][k] for x in data if x['regime']=='A']);bv=np.array([x['metrics'][k] for x in data if x['regime']=='B'])
 assert np.isfinite(av).all() and np.isfinite(bv).all()
 assert np.allclose([ma,sd,mb,d,q],[av.mean(),av.std(ddof=1),bv.mean(),bv.mean()-av.mean(),abs(bv.mean()-av.mean())/av.std(ddof=1)])
 assert flag==bool(abs(d)>2*sd)
for n in ['A','B']:
 for seed in range(101,106):
  h=json.loads((a/f'history_{n}_{seed}.json').read_text());assert all(len(v)==150 for v in h.values())
 for step in [100,300,700,1500]:Image.open(a/f'{n}_s101_step{step}.png').verify()
 Image.open(a/f'{n}_32.png').verify()
n=nbformat.read(r/'notebooks/LR11_3.ipynb',as_version=4);nbformat.validate(n)
assert all(not any(o.output_type=='error' for o in c.outputs) for c in n.cells if c.cell_type=='code')
assert sum(o.output_type=='display_data' for c in n.cells if c.cell_type=='code' for o in c.outputs)==2
print('PASS: 10 run records; code hashes; recomputed summary; 10 complete histories; PNG integrity; executed analysis notebook. Training and metrics not independently rerun by verifier.')
