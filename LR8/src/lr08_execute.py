"""LR8 variant 3: unchanged teacher functions, authentic Engee CPU run and audit files."""
from pathlib import Path
import sys,time,datetime,json,hashlib,platform,subprocess,shutil,traceback
import numpy as np,torch
from PIL import Image
import lab07_lib as L,lab08_lib as V
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)
class Tee:
 def __init__(self,*streams):self.streams=streams
 def write(self,text):
  for out in self.streams:out.write(text);out.flush()
 def flush(self):
  for out in self.streams:out.flush()
LOG=open(ROOT/'run.log','w',buffering=1)
sys.stdout=Tee(sys.stdout,LOG);sys.stderr=Tee(sys.stderr,LOG)
def write_json(path,x):path.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
STARTED=datetime.datetime.now(datetime.timezone.utc).isoformat()
assert V.DEVICE=='cpu','This notebook follows the Engee CPU protocol'
print('STARTED',STARTED,sys.version,torch.__version__,'CPU threads',torch.get_num_threads(),flush=True)
for f in ['lab07_lib.py','lab08_lib.py','lab08_demo.py','run_lr08.py']:
 payload=(ROOT/f).read_bytes();shutil.copy2(ROOT/f,OUT/f);print('SOURCE_SHA256',f,hashlib.sha256(payload).hexdigest(),flush=True)
training_events=[];old_train=V.train_vae;old_get=V.get_model;old_run=V.run
# Observe training without modifying the supplied source or its optimization.
def observed_train(model,Xtr,beta,epochs=30,lr=2e-3,seed=0,batch=128,warmup=10):
 event=dict(index=len(training_events)+1,d=model.fc_mu.out_features,beta=beta,epochs=epochs,seed=seed,warmup=warmup,started=datetime.datetime.now(datetime.timezone.utc).isoformat())
 training_events.append(event);print('TRAIN_START',event,flush=True);write_json(OUT/'training_progress.json',training_events)
 t=time.perf_counter();answer=old_train(model,Xtr,beta,epochs,lr,seed,batch,warmup)
 event['seconds']=time.perf_counter()-t;event['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat();print('TRAIN_DONE',event,flush=True);write_json(OUT/'training_progress.json',training_events)
 return answer
V.train_vae=observed_train
demo_records=[]
def demo_run(kind,cfg,seed):
 answer=old_run(kind,cfg,seed);demo_records.append(dict(kind=kind,settings=dict(cfg),seed=seed,metrics=answer));write_json(OUT/'demo_records.json',demo_records);print('DEMO_METRICS',seed,cfg,answer,flush=True);return answer
demo_metric_calls=[];old_metrics=V.metrics
def demo_metrics(model,kind,interp='lin',temp=1.0,seed=0):
 answer=old_metrics(model,kind,interp,temp,seed)
 demo_metric_calls.append(dict(seed=seed,d=model.fc_mu.out_features,latest_training=dict(training_events[-1]),metrics=answer))
 write_json(OUT/'demo_metric_calls.json',demo_metric_calls)
 return answer
V.metrics=demo_metrics
V.run=demo_run
print('DEMO_BEGIN',flush=True)
try:exec(compile((ROOT/'lab08_demo.py').read_text(),'lab08_demo.py','exec'),globals())
finally:
 V.run=old_run;V.metrics=old_metrics
assert len(demo_metric_calls)==23
write_json(OUT/'collapse_records.json',demo_metric_calls[13:23])
write_json(OUT/'demo_summary.json',result)
shutil.copy2(ROOT/'comparison.png',OUT/'comparison_demo_variant01.png')
print('DEMO_COMPLETE',flush=True)
N=3;c,k=(N-1)//6,(N-1)%6;kind=L.KINDS[c];a_cfg,b_cfg=V.settings(V.FACTORS[k])
assert [key for key in a_cfg if a_cfg[key]!=b_cfg[key]]==['d']
print('INDIVIDUAL_A',a_cfg,'B',b_cfg,flush=True)
Xtr,Xte,Ftr,Fte=L.dataset(kind)
np.savez_compressed(OUT/'dataset.npz',train=Xtr.numpy(),test=Xte.numpy(),factors_train=Ftr.numpy(),factors_test=Fte.numpy())
ia,ib,targets=V.interp_targets(kind)
np.savez_compressed(OUT/'interpolation_pairs.npz',ia=ia.numpy(),ib=ib.numpy())
records=[];audit=[]
@torch.no_grad()
def audit_metrics(model,cfg,seed,condition):
 mu_tr=model.encode(Xtr);mu_te,lv_te=model.encode_dist(Xte)
 reconstructed=model.decode(mu_te)
 recon_mse=((reconstructed-Xte)**2).flatten(1).mean(1)
 imse=[]
 for t,target in targets.items():
  za,zb=mu_te[ia],mu_te[ib]
  z=V.slerp(za,zb,t) if cfg['interp']=='slerp' else (1-t)*za+t*zb
  imse.append(((model.decode(z)-target)**2).flatten(1).mean(1).numpy())
 g=torch.Generator(device='cpu').manual_seed(1000+seed)
 zs=cfg['temp']*torch.randn((V.N_SAMPLES,cfg['d']),generator=g)
 samples=model.decode(zs)
 mse=torch.cdist(samples.flatten(1),Xte.flatten(1)).pow(2)/3072
 nearest,nn_indices=mse.min(1)
 A=torch.cat([mu_tr,torch.ones(mu_tr.shape[0],1)],1).double()
 W=torch.linalg.solve(A.T@A+1e-6*torch.eye(A.shape[1],dtype=A.dtype),A.T@Ftr.double()).float()
 predictions=torch.cat([mu_te,torch.ones(mu_te.shape[0],1)],1)@W
 kl_axis=(-.5*(1+lv_te-mu_te**2-lv_te.exp())).mean(0)
 diagnostic=dict(condition=condition,seed=seed,d=cfg['d'],beta=cfg['beta'],mu_std=mu_te.std(0).numpy().tolist(),kl_axis=kl_axis.numpy().tolist(),active=int((kl_axis>.05).sum()))
 path=f'{condition}_{seed}_audit.npz'
 np.savez_compressed(OUT/path,recon_mse=recon_mse.numpy(),interp_mse=np.stack(imse),sample_min_mse=nearest.numpy(),sample_nn_indices=nn_indices.numpy(),mu_train=mu_tr.numpy(),mu_test=mu_te.numpy(),lv_test=lv_te.numpy(),regression_W=W.numpy(),factor_predictions=predictions.numpy())
 if seed==101:
  torch.save(model.state_dict(),OUT/f'{condition}_101_weights.pt')
  np.savez_compressed(OUT/f'{condition}_101_pixels.npz',reconstruction=reconstructed[:8].numpy(),samples=samples[:8].numpy(),sample_nn=Xte[nn_indices[:8]].numpy())
 return path,diagnostic

def recorded_run(kind,cfg,seed):
 answer=old_run(kind,cfg,seed)
 condition='A' if cfg==a_cfg else 'B'
 name,diagnostic=audit_metrics(V.get_model(kind,cfg,seed),cfg,seed,condition)
 rec=dict(condition=condition,kind=kind,settings=dict(cfg),seed=seed,metrics=answer,audit=name)
 records.append(rec);audit.append(diagnostic)
 write_json(OUT/'records.json',records);write_json(OUT/'diagnostic.json',audit)
 print('INDIVIDUAL_METRICS',rec,flush=True)
 return answer
V.run=recorded_run
try:result=V.variant_summary(N)
finally:V.run=old_run
write_json(OUT/'summary.json',result)
TOLS={'recon':1.,'interp':1.,'sample':1.,'r2':.05};classified=[]
for metric,a,s,b,d,ratio,sig in result['rows']:
 tol=TOLS[metric];label='нейтрально' if abs(d)<=tol else 'улучшение' if d>0 else 'ухудшение'
 classified.append(dict(metric=metric,A=a,s_A=s,B=b,delta=d,ratio=ratio,over_2s=sig,tolerance=tol,label=label,criteria_disagree=bool(sig)!=(abs(d)>tol)))
write_json(OUT/'classification.json',classified)
print('MAIN_SUMMARY',json.dumps(result),flush=True);print('CLASSIFICATION',json.dumps(classified,ensure_ascii=False),flush=True)
# Mandatory AE baseline and active-axis diagnostics, seed101; reuse demo cached models.
diag_controls=[]
for beta in [0.,1.,8.]:
 cfg=dict(V.BASE,beta=beta);model=V.get_model(kind,cfg,101)
 with torch.no_grad():
  mu,lv=model.encode_dist(Xte);kl=(-.5*(1+lv-mu**2-lv.exp())).mean(0)
 values=V.metrics(model,kind,'lin',1.,101)
 diag_controls.append(dict(beta=beta,mu_std=mu.std(0).numpy().tolist(),kl_axis=kl.numpy().tolist(),active=int((kl>.05).sum()) if beta>0 else None,metrics=values))
write_json(OUT/'ae_vae_controls.json',diag_controls)
# Four rows: A/B prior samples; A/B paths between test scenes 0 and2.
rows=[];paths={};t=torch.linspace(0,1,8).unsqueeze(1)
with torch.no_grad():
 for condition,cfg in [('A',a_cfg),('B',b_cfg)]:
  model=V.get_model(kind,cfg,101);g=torch.Generator(device='cpu').manual_seed(5);z=torch.randn((8,cfg['d']),generator=g)
  rows.append(model.decode(z).numpy())
 for condition,cfg in [('A',a_cfg),('B',b_cfg)]:
  model=V.get_model(kind,cfg,101);za,zb=model.encode(Xte[0:1]),model.encode(Xte[2:3])
  imgs=model.decode((1-t)*za+t*zb).numpy();rows.append(imgs);paths[condition]=imgs
true_path=np.stack([L.render(kind,(1-float(tt))*Fte[0].numpy()+float(tt)*Fte[2].numpy()) for tt in t])
np.savez_compressed(OUT/'comparison_pixels.npz',rows=np.stack(rows),true_path=true_path,t=t.numpy())
def strip(x):return np.concatenate(list(x.transpose(0,2,3,1)),axis=1)
img=Image.fromarray((np.concatenate([strip(x) for x in rows],axis=0)*255).round().astype('uint8')).resize((1024,512),Image.Resampling.NEAREST);img.save(OUT/'comparison.png')
ref=Image.fromarray((strip(true_path)*255).round().astype('uint8')).resize((1024,128),Image.Resampling.NEAREST);ref.save(OUT/'interpolation_true_path.png')
# Additional per-factor R2 reveals which factors are lost; no claim of disentangled axes.
per_factor=[]
for rec in records:
 data=np.load(OUT/rec['audit']);pred=data['factor_predictions'];f=Fte.numpy()
 r2=1-((pred-f)**2).sum(0)/((f-f.mean(0))**2).sum(0)
 per_factor.append(dict(condition=rec['condition'],seed=rec['seed'],r2_x=float(r2[0]),r2_y=float(r2[1]),r2_radius=float(r2[2])))
write_json(OUT/'r2_per_factor.json',per_factor)
passport=dict(student='Власюк Данил Витальевич',group='Т26ИИКТ-МИК11',variant=N,started_utc=STARTED,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment='Engee CPU',python=sys.version,platform=platform.platform(),torch=torch.__version__,numpy=np.__version__,threads=torch.get_num_threads(),cuda=torch.cuda.is_available(),kind=kind,data_seed=7,seeds=list(L.SEEDS),settings_A=a_cfg,settings_B=b_cfg,optimizer='Adam',lr=.002,batch=128,warmup=10,training_updates=960,n_pairs=V.N_PAIRS,n_samples=V.N_SAMPLES,pair_seed=11,sample_seed='1000+training_seed',tolerances=TOLS,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['lab07_lib.py','lab08_lib.py','lab08_demo.py','run_lr08.py']},independent_new_session_tested=False)
write_json(OUT/'passport.json',passport)
(OUT/'environment.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
manifest={str(p.relative_to(OUT)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in OUT.rglob('*') if p.is_file()}
write_json(OUT/'run_manifest.json',manifest)
archive=shutil.make_archive(str(ROOT/'LR08_variant3_results'),'zip',OUT)
print('COMPLETE; ARCHIVE',archive,flush=True)
write_json(ROOT/'status.json',dict(status='complete',archive=archive,finished=passport['finished_utc']))
