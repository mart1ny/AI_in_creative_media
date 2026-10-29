"""Independent validation of actual Colab artifacts using NumPy and Pillow."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'artifacts'
def read(f):return json.loads((A/f).read_text())
def close(x,y,tol=3e-5):assert math.isclose(x,y,rel_tol=tol,abs_tol=tol),(x,y)
def psnr(mse):return float(np.mean(10*np.log10(1/np.maximum(mse,1e-10))))
passport=read('passport.json');records=read('records.json');summary=read('summary.json');classified=read('classification.json')
for name,expect in read('run_manifest.json').items():
 payload=(A/name).read_bytes();assert hashlib.sha256(payload).hexdigest()==expect['sha256'] and len(payload)==expect['bytes'],name
assert len(records)==10 and {(r['condition'],r['seed']) for r in records}=={(c,s) for c in ['A','B'] for s in range(101,106)}
assert [k for k in passport['settings_A'] if passport['settings_A'][k]!=passport['settings_B'][k]]==['arch']
data=np.load(A/'dataset.npz');train=data['train'];test=data['test'];assert train.shape==(4096,3,32,32) and test.shape==(1024,3,32,32)
mean=np.mean(train,axis=0,keepdims=True,dtype=np.float64);stored=np.load(A/'mean_train.npy');assert np.allclose(mean,stored,atol=2e-6)
mse=((stored.astype(float)-test.astype(float))**2).reshape(1024,-1).mean(1)
close(psnr(mse),read('baseline.json')['psnr'])
conv_params=(3*16*16+16)+(16*32*16+32)+(32*64*16+64)+(1024*8+8)+(8*1024+1024)+(64*32*16+32)+(32*16*16+16)+(16*3*16+3)
dense_params=(3072*256+256)+(256*8+8)+(8*256+256)+(256*3072+3072)
assert conv_params==101035 and dense_params==1580552
for r in records:
 errors=np.load(A/r['errors']);p_te=psnr(errors['mse_test']);p_tr=psnr(errors['mse_train'])
 assert errors['mse_test'].shape==errors['mse_train'].shape==(1024,)
 close(p_te,r['metrics']['psnr']);close(p_tr-p_te,r['metrics']['gap'])
 close(r['metrics']['params'],(conv_params if r['condition']=='A' else dense_params)/1000)
 if r['seed']==101:
  pred=np.load(A/f"{r['condition']}_101_predictions.npy");assert pred.shape==(8,3,32,32)
  mse8=((pred.astype(float)-test[:8].astype(float))**2).reshape(8,-1).mean(1)
  assert np.allclose(mse8,errors['mse_test'][:8],rtol=2e-5,atol=1e-9)
for metric,a,s,b,d,ratio,sig in summary['rows']:
 aa=np.array([r['metrics'][metric] for r in records if r['condition']=='A']);bb=np.array([r['metrics'][metric] for r in records if r['condition']=='B'])
 for x,y in zip([aa.mean(),aa.std(ddof=1),bb.mean(),bb.mean()-aa.mean()],[a,s,b,d]):close(float(x),y,1e-10)
 assert (math.isinf(ratio) if s==0 else math.isclose(abs(d)/s,ratio))
 assert bool(abs(d)>2*s)==sig
 row=next(r for r in classified if r['metric']==metric)
 tol={'psnr':1.,'gap':.1}.get(metric,.2*abs(a));direction=d if metric=='psnr' else -d
 close(row['tolerance'],tol,1e-10)
 label='нейтрально' if abs(d)<=tol else 'улучшение' if direction>0 else 'ухудшение'
 assert row['label']==label and row['criteria_disagree']==(bool(sig)!=(abs(d)>tol))
for row in read('diagnostic_summary.json'):
 vals=[r['metrics']['psnr'] for r in read('diagnostic.json') if r['settings']['d']==row['d']]
 assert vals==row['values'];close(float(np.mean(vals)),row['mean']);close(float(np.std(vals,ddof=1)),row['s'])
rows=[test[:8],np.load(A/'A_101_predictions.npy'),np.load(A/'B_101_predictions.npy')]
grid=np.concatenate([np.concatenate(list(r.transpose(0,2,3,1)),axis=1) for r in rows],axis=0)
expected=Image.fromarray((grid*255).round().astype('uint8')).resize((1024,384),Image.Resampling.NEAREST)
assert np.array_equal(np.asarray(expected),np.asarray(Image.open(A/'comparison.png')))
pre=json.loads((R/'reports/pre_run_record.json').read_text())
assert hashlib.sha256((R/'data/hypothesis.md').read_bytes()).hexdigest()==pre['hypothesis_sha256']
assert datetime.fromisoformat(pre['recorded_at']).astimezone(timezone.utc)<datetime.fromisoformat(passport['started_utc'])
for f,sha in passport['source_sha256'].items():
 assert all(hashlib.sha256((R/folder/f).read_bytes()).hexdigest()==sha for folder in ['input','src','artifacts'])
nb=json.loads((R/'notebooks/LR07_3.ipynb').read_text());codes=[c for c in nb['cells'] if c['cell_type']=='code']
assert all(c.get('execution_count') is not None for c in codes)
assert not any(o.get('output_type')=='error' for c in codes for o in c.get('outputs',[]))
streams=''.join(''.join(o.get('text',[])) for c in codes for o in c.get('outputs',[]) if o.get('output_type')=='stream')
assert 'COMPLETE; ARCHIVE' in streams
result=dict(result='PASS',checks=['run manifest and all hashes','five seeds and only architecture changed','baseline from train evaluated on test','per-image test/train PSNR and gap','parameter counts from layer formulas','means, sample s, delta, ratios, 2s and tolerances','diagnostic d series','seed101 reconstruction errors and pixel-exact comparison sheet','hypothesis before run, unchanged teacher source','notebook fully executed without errors'],limitations='No local GPU retraining; all-seed PSNR aggregated from actual saved per-image errors; full pixel reconstructions independently checked for first eight test scenes at seed101')
(R/'reports/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
