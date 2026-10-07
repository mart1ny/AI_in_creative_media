"""Независимая проверка арифметики, Float64 массивов, серии и исходников."""
from pathlib import Path
import csv, json, math, hashlib, statistics, struct
R=Path(__file__).resolve().parents[1]
A=R/'artifacts'
rows=list(csv.DictReader((A/'per_seed.csv').open()))
summary=list(csv.DictReader((A/'summary.csv').open()))
checks={}
for factor,variant in [(2,2),(3,3)]:
 r=[x for x in rows if float(x['noise'])==.02 and int(x['factor'])==factor]
 assert [int(x['seed']) for x in r]==list(range(101,106))
 for m in ['mean','contrast','entropy']:
  b=[float(x[m+'_before']) for x in r]; a=[float(x[m+'_after']) for x in r]
  z=next(x for x in summary if int(x['variant'])==variant and x['metric']==m)
  base=statistics.mean(b); after=statistics.mean(a); s=statistics.stdev(b); d=after-base
  for k,val in [('base',base),('after',after),('s',s),('delta',d),('ratio',abs(d)/s),('relative_change',abs(d)/abs(base))]:
   assert math.isclose(float(z[k]),val,rel_tol=1e-9,abs_tol=1e-12),(k,val,z[k])
  assert (z['stat_significant']=='true')==(abs(d)>2*s)
  assert (z['practical_significant']=='true')==(abs(d)/abs(base)>.05)
 checks[f'summary_x{2 if factor==2 else 4}']=True
for name in ['before','after_x2','after_x4']:
 data=(A/(name+'_seed101.f64')).read_bytes()
 vals=struct.unpack('<16384d',data)
 assert all(0<=x<=1 for x in vals)
 checks[name+'_range_size']=True
 reference=next(x for x in rows if float(x['noise'])==.02 and int(x['factor'])==(2 if name=='after_x2' else 3) and int(x['seed'])==101)
 assert hashlib.sha256(data).hexdigest()==reference['sha_before' if name=='before' else 'sha_after']
 checks[name+'_hash']=True
before=struct.unpack('<16384d',(A/'before_seed101.f64').read_bytes())
for name,f in [('after_x2',2),('after_x4',3)]:
 a=struct.unpack('<16384d',(A/(name+'_seed101.f64')).read_bytes())
 mse=statistics.mean((x-y)**2 for x,y in zip(before,a))
 ref=next(x for x in rows if float(x['noise'])==.02 and int(x['factor'])==f and int(x['seed'])==101)
 assert math.isclose(mse,float(ref['mse']),rel_tol=1e-12)
 assert math.isclose(10*math.log10(1/mse),float(ref['psnr']),rel_tol=1e-12)
 checks[name+'_mse_psnr']=True
assert (R/'src/lab03_lib.jl').read_bytes()==(R/'input/lab03_lib.jl').read_bytes()
checks['teacher_library_unchanged']=True
pre=json.loads((R/'reports/pre_run_record.json').read_text())
assert hashlib.sha256((R/'data/hypothesis.md').read_bytes()).hexdigest()==pre['hypothesis_sha256']
assert pre['recorded_at']<'2026-10-07T20:32:24+03:00'
checks['hypothesis_unchanged_recorded_before_run']=True
nb=json.loads((R/'engee/LR03_3.ngscript').read_text())
assert not any(o.get('output_type')=='error' for c in nb['cells'] for o in c.get('outputs',[]))
stdout=''.join(''.join(o.get('text',[])) for c in nb['cells'] for o in c.get('outputs',[]) if o.get('output_type')=='stream')
assert 'ALL CHECKS PASS' in stdout and 'Julia 1.12.4' in stdout
checks['executed_notebook_no_errors']=True
(A.parent/'reports/verification.json').write_text(json.dumps({'result':'PASS','checks':checks},indent=2))
print(json.dumps(checks,indent=2)); print('RESULT: PASS')
