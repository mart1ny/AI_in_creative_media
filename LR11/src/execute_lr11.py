from pathlib import Path
import sys,json,time,platform,hashlib,datetime,os
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import lab11_lib as L
import torch,numpy as np
from PIL import Image
A=R/'artifacts';A.mkdir(exist_ok=True)
kind,ca,cb=L.variant_settings(3)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
passport=dict(started=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),torch=torch.__version__,numpy=np.__version__,threads=torch.get_num_threads(),device=str(L.DEVICE),variant=3,kind=kind,A=ca,B=cb,seeds=list(L.SEEDS),source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'src').glob('*.py')})
dump(A/'passport.json',passport)
X=L.L.dataset(kind)[0][:ca['n_train']]; records=[]
def sheet(x,path):
 x=x.detach().permute(0,2,3,1).numpy();rows=[np.concatenate(x[i:i+8],axis=1) for i in range(0,len(x),8)];im=Image.fromarray((np.concatenate(rows)*255).clip(0,255).astype('uint8'));im.resize((768,96*len(rows)),Image.Resampling.NEAREST).save(path)
for seed in L.SEEDS:
 for name,cfg in [('A',ca),('B',cb)]:
  def snap(step,g):
   sheet(L.sample(g,32,7),A/f'{name}_s{seed}_step{step}.png')
  t=time.perf_counter();g,h=L.train_gan(X,cfg,seed,snapshots=(100,300,700,1500) if seed==101 else (),on_snapshot=snap if seed==101 else None);elapsed=time.perf_counter()-t
  m=L.metrics(g,kind,seed);m['seconds']=elapsed
  records.append(dict(regime=name,seed=seed,metrics=m));dump(A/'per_seed.json',records);dump(A/f'history_{name}_{seed}.json',h)
  if seed==101:sheet(L.sample(g,32,1000+seed),A/f'{name}_32.png')
  print(name,seed,m,flush=True)
a={m:[r['metrics'][m] for r in records if r['regime']=='A'] for m in L.METRICS};b={m:[r['metrics'][m] for r in records if r['regime']=='B'] for m in L.METRICS}
dump(A/'summary.json',dict(variant=3,rows=L.summarize(a,b)))
print('COMPLETE',flush=True)
