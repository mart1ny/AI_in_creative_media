"""Independent verification of downloaded results: NumPy, SciPy, Pillow."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math
import numpy as np
from scipy import ndimage
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'artifacts'
def read(f):return json.loads((A/f).read_text())
def luma(img):
 x=np.asarray(img.convert('RGB'),dtype=np.float64)/255
 return .299*x[...,0]+.587*x[...,1]+.114*x[...,2]
def spatial(img):
 y=luma(img)
 return dict(edge=float(np.mean(np.hypot(ndimage.sobel(y,axis=0),ndimage.sobel(y,axis=1))/8)),contrast=float(np.std(y)))
records=read('records.json');passport=read('passport.json');summary=read('summary.json');classified=read('classification.json')
assert len(records)==10
assert {(x['condition'],x['seed']) for x in records}=={(c,s) for c in ['A','B'] for s in range(101,106)}
assert [k for k in passport['settings_A'] if passport['settings_A'][k]!=passport['settings_B'][k]]==['size']
for r in records:
 p=A/r['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
 with Image.open(p) as img:
  side=512 if r['condition']=='A' else 768
  assert img.size==(side,side)
  for k,v in spatial(img).items():assert math.isclose(v,r['metrics'][k],rel_tol=1e-10,abs_tol=1e-12)
for metric,ma,s,mb,d,ratio,sig in summary['rows']:
 aa=np.array([r['metrics'][metric] for r in records if r['condition']=='A']);bb=np.array([r['metrics'][metric] for r in records if r['condition']=='B'])
 actual=[float(aa.mean()),float(aa.std(ddof=1)),float(bb.mean()),float(bb.mean()-aa.mean())]
 assert all(math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12) for x,y in zip(actual,[ma,s,mb,d]))
 assert math.isclose(abs(d)/s,ratio) and bool(abs(d)>2*s)==sig
 row=next(r for r in classified if r['metric']==metric)
 tol=1. if metric=='clip' else {'edge':.1,'contrast':.1,'seconds':.2}[metric]*abs(ma)
 practical=abs(d)>tol;direction=-d if metric=='seconds' else d
 label='нейтрально' if not practical else 'улучшение' if direction>0 else 'ухудшение'
 assert math.isclose(row['tolerance'],tol) and row['label']==label
 assert row['criteria_disagree']==(bool(sig)!=practical)
normalized=read('normalized_512.json')
for rec in normalized['records']:
 image=Image.open(A/f"{rec['condition']}_{rec['seed']}/result.png").convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
 for k,v in spatial(image).items():assert math.isclose(v,rec[k],rel_tol=1e-10,abs_tol=1e-12)
g=read('guidance_check.json');assert g['equal_0_1'] and [x['cfg_active'] for x in g['records']]==[False,False,True]
for r in g['records']:assert hashlib.sha256((A/r['file']).read_bytes()).hexdigest()==r['sha256']
x=np.asarray(Image.open(A/'guidance_0.png'),dtype=float);y=np.asarray(Image.open(A/'guidance_1.png'),dtype=float);assert np.array_equal(x,y)
z=np.asarray(Image.open(A/'guidance_3.png'),dtype=float);psnr=10*math.log10(255**2/np.mean((x-z)**2));assert math.isclose(psnr,g['psnr_0_3'])
pre=json.loads((R/'reports/pre_run_record.json').read_text())
assert datetime.fromisoformat(pre['recorded_at']).astimezone(timezone.utc)<datetime.fromisoformat(passport['started_utc'])
assert hashlib.sha256((R/'data/hypothesis.md').read_bytes()).hexdigest()==pre['hypothesis_sha256']
for f,sha in passport['source_sha256'].items():
 assert all(hashlib.sha256((R/folder/f).read_bytes()).hexdigest()==sha for folder in ['input','src','artifacts'])
nb=json.loads((R/'notebooks/LR06_3.ipynb').read_text());codes=[c for c in nb['cells'] if c['cell_type']=='code']
assert all(c.get('execution_count') is not None for c in codes)
assert not any(o.get('output_type')=='error' for c in codes for o in c.get('outputs',[]))
streams=''.join(''.join(o.get('text',[])) for c in codes for o in c.get('outputs',[]) if o.get('output_type')=='stream')
assert 'COMPLETE; ARCHIVE' in streams
res=dict(result='PASS',checks=['10 images and SHA-256','one changed factor','spatial metrics independently recomputed','means, sample s, delta, ratio, 2s and tolerances','common-scale spatial control','guidance 0/1 equality and 3 control','pre-run hypothesis and unchanged teacher scripts','all code cells executed without errors'],limitation='CLIP embeddings not independently recomputed locally; original CLIP outputs retained')
(R/'reports/verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(json.dumps(res,ensure_ascii=False,indent=2))
