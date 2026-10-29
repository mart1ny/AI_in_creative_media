"""Independent NumPy/Pillow audit of authentic Engee CPU outputs."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'artifacts'
def read(f):return json.loads((A/f).read_text())
def close(x,y,tol=3e-5):assert math.isclose(float(x),float(y),rel_tol=tol,abs_tol=tol),(x,y)
def psnr(mse):return float(np.mean(10*np.log10(1/np.maximum(mse,1e-10))))
p=read('passport.json');records=read('records.json');summary=read('summary.json');classified=read('classification.json');diagnostic=read('diagnostic.json')
assert p['environment']=='Engee CPU' and not p['cuda']
for f,m in read('run_manifest.json').items():
 payload=(A/f).read_bytes();assert len(payload)==m['bytes'] and hashlib.sha256(payload).hexdigest()==m['sha256'],f
assert len(records)==10 and {(r['condition'],r['seed']) for r in records}=={(c,s) for c in ['A','B'] for s in range(101,106)}
assert [k for k in p['settings_A'] if p['settings_A'][k]!=p['settings_B'][k]]==['d']
data=np.load(A/'dataset.npz');tr=data['train'];te=data['test'];ftr=data['factors_train'];fte=data['factors_test']
assert tr.shape==(4096,3,32,32) and te.shape==(1024,3,32,32) and fte.shape==(1024,3)
pairs=np.load(A/'interpolation_pairs.npz');rng=np.random.default_rng(11)
assert np.array_equal(pairs['ia'],rng.integers(0,1024,200));assert np.array_equal(pairs['ib'],rng.integers(0,1024,200))
for r in records:
 ar=np.load(A/r['audit']);m=r['metrics'];mu=ar['mu_test'].astype(float);lv=ar['lv_test'].astype(float)
 assert ar['recon_mse'].shape==(1024,) and ar['interp_mse'].shape==(3,200) and ar['sample_min_mse'].shape==(256,)
 close(psnr(ar['recon_mse']),m['recon']);close(np.mean([psnr(a) for a in ar['interp_mse']]),m['interp']);close(psnr(ar['sample_min_mse']),m['sample'])
 X=np.column_stack([ar['mu_train'].astype(float),np.ones(4096)])
 W=np.linalg.solve(X.T@X+1e-6*np.eye(X.shape[1]),X.T@ftr.astype(float))
 pred=np.column_stack([mu,np.ones(1024)])@W
 assert np.allclose(pred,ar['factor_predictions'],rtol=1e-4,atol=1e-4)
 r2=1-np.sum((pred-fte.astype(float))**2,axis=0)/np.sum((fte.astype(float)-fte.astype(float).mean(0))**2,axis=0)
 close(float(r2.mean()),m['r2'],1e-4)
 dr=next(x for x in diagnostic if x['condition']==r['condition'] and x['seed']==r['seed'])
 kl=np.mean(-.5*(1+lv-mu**2-np.exp(lv)),axis=0)
 assert np.allclose(kl,dr['kl_axis'],rtol=1e-4,atol=2e-5)
 assert np.allclose(mu.std(0,ddof=1),dr['mu_std'],rtol=1e-4,atol=2e-5)
 assert int((kl>.05).sum())==dr['active']
 if r['seed']==101:
  pixels=np.load(A/f"{r['condition']}_101_pixels.npz")
  actual=((pixels['reconstruction'].astype(float)-te[:8].astype(float))**2).reshape(8,-1).mean(1)
  assert np.allclose(actual,ar['recon_mse'][:8],rtol=3e-5,atol=2e-7)
  for i,sample in enumerate(pixels['samples']):
   dist=((sample.astype(float)-te.astype(float))**2).reshape(1024,-1).mean(1)
   close(float(dist.min()),ar['sample_min_mse'][i],2e-6)
   assert np.array_equal(pixels['sample_nn'][i],te[ar['sample_nn_indices'][i]])
for metric,a,s,b,d,ratio,sig in summary['rows']:
 aa=np.array([r['metrics'][metric] for r in records if r['condition']=='A']);bb=np.array([r['metrics'][metric] for r in records if r['condition']=='B'])
 for x,y in zip([aa.mean(),aa.std(ddof=1),bb.mean(),bb.mean()-aa.mean()],[a,s,b,d]):close(x,y,1e-10)
 assert math.isclose(abs(d)/s,ratio) and bool(abs(d)>2*s)==sig
 row=next(r for r in classified if r['metric']==metric);tol=.05 if metric=='r2' else 1.
 assert row['tolerance']==tol and row['label']==('нейтрально' if abs(d)<=tol else 'улучшение' if d>0 else 'ухудшение')
 assert row['criteria_disagree']==(bool(sig)!=(abs(d)>tol))
pix=np.load(A/'comparison_pixels.npz')
def strip(x):return np.concatenate(list(x.transpose(0,2,3,1)),axis=1)
expected=Image.fromarray((np.concatenate([strip(x) for x in pix['rows']],axis=0)*255).round().astype('uint8')).resize((1024,512),Image.Resampling.NEAREST)
assert np.array_equal(np.asarray(expected),np.asarray(Image.open(A/'comparison.png')))
pre=json.loads((R/'reports/pre_run_record.json').read_text())
assert hashlib.sha256((R/'data/hypothesis.md').read_bytes()).hexdigest()==pre['hypothesis_sha256']
assert datetime.fromisoformat(pre['recorded_at']).astimezone(timezone.utc)<datetime.fromisoformat(p['started_utc'])
for f,sha in p['source_sha256'].items():
 assert all(hashlib.sha256((R/folder/f).read_bytes()).hexdigest()==sha for folder in ['input','src','artifacts'])
nb=json.loads((R/'notebooks/LR08_3.ngscript').read_text());codes=[c for c in nb['cells'] if c['cell_type']=='code']
assert all(c.get('execution_count') is not None for c in codes)
assert not any(o.get('output_type')=='error' for c in codes for o in c.get('outputs',[]))
streams=''.join(''.join(o.get('text',[])) for c in codes for o in c.get('outputs',[]) if o.get('output_type')=='stream')
assert 'COMPLETE; ARCHIVE' in streams
result=dict(result='PASS',checks=['authentic Engee CPU passport and artifact hashes','5 seeds and only d changed','test reconstruction and 200-pair interpolation PSNR','256-sample nearest PSNR and direct pixel check for seed101 subset','independent factor regression and R2','KL, standard deviations and active dimensions','means, sample s, delta, 2s and tolerances','exact comparison image from float pixels','hypothesis before training and unchanged teacher scripts','executed Engee notebook without errors'],limitation='No independent local retraining; full-series PSNR aggregated from saved per-image errors; pixel-level reconstruction and nearest-neighbor check covers first 8 seed101 samples')
(R/'reports/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
