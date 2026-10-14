"""Независимая проверка сохранённых результатов Engee. Python 3.11+, stdlib."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, math, statistics, struct, tomllib

R=Path(__file__).resolve().parents[1]
A=R/'artifacts'
rows=list(csv.DictReader((A/'per_seed.csv').open()))
summary=list(csv.DictReader((A/'summary.csv').open()))
passport=tomllib.loads((A/'passport.toml').read_text())
checks={}
assert len(rows)==150 and len(summary)==90
for scene in range(1,6):
    for op in range(1,7):
        series=[r for r in rows if int(r['scene'])==scene and int(r['operation'])==op]
        assert [int(r['seed']) for r in series]==list(range(101,106))
        for metric in ['psnr','edge','contrast']:
            b=[float(r[metric+'_before']) for r in series]
            a=[float(r[metric+'_after']) for r in series]
            base,after,s=statistics.mean(b),statistics.mean(a),statistics.stdev(b)
            delta=after-base
            line=next(z for z in summary if int(z['scene'])==scene and int(z['operation'])==op and z['metric']==metric)
            expected={'base':base,'s':s,'after':after,'delta':delta,'ratio':abs(delta)/s}
            for k,v in expected.items():
                assert math.isclose(float(line[k]),v,rel_tol=1e-9,abs_tol=1e-10),(scene,op,metric,k)
            assert (line['stat_significant']=='true')==(abs(delta)>2*s)
        for r in series:
            for side in ['before','after']:
                assert math.isclose(10*math.log10(1/float(r['mse_'+side])),float(r['psnr_'+side]),abs_tol=1e-10)
        if op==6:
            assert all(0<=float(r['iou_before'])<=1 and 0<=float(r['iou_after'])<=1 for r in series)
            expected_iou=statistics.mean(float(r['iou_after']) for r in series)
            assert math.isclose(float(line['iou_after']),expected_iou,abs_tol=1e-12)
checks['all_30_variants_and_150_seed_rows']=True
checks['all_summary_arithmetic_psnr_and_iou']=True

arrays={name:struct.unpack('<16384d',(A/(name+'.f64')).read_bytes())
        for name in ['noisy_seed101','reference_clean','gauss3_seed101']}
assert all(all(0<=x<=1 for x in values) for values in arrays.values())
raw=(A/'noisy_seed101.f64').read_bytes()
assert hashlib.sha256(raw).hexdigest()==passport['scene_sha256']
ref=arrays['reference_clean']
row=next(r for r in rows if r['scene']=='1' and r['operation']=='3' and r['seed']=='101')
for side,name in [('before','noisy_seed101'),('after','gauss3_seed101')]:
    vals=arrays[name]
    mse=statistics.mean((x-y)**2 for x,y in zip(vals,ref))
    assert math.isclose(mse,float(row['mse_'+side]),rel_tol=1e-12)
    assert math.isclose(statistics.stdev(vals),float(row['contrast_'+side]),rel_tol=1e-12)
checks['float64_size_range_sha_mse_contrast']=True
for number in ['03','04']:
    data=(R/f'src/lab{number}_lib.jl').read_bytes()
    assert hashlib.sha256(data).hexdigest()==passport[f'library{number}_sha256']
assert (R/'src/lab04_lib.jl').read_bytes()==(R/'input/lab04_lib.jl').read_bytes()
checks['teacher_libraries_unchanged']=True
pre=json.loads((R/'reports/pre_run_record.json').read_text())
hyp_hash=hashlib.sha256((R/'data/hypothesis.md').read_bytes()).hexdigest()
assert hyp_hash==pre['hypothesis_sha256']==passport['hypothesis_sha256']
assert datetime.fromisoformat(pre['recorded_at']).astimezone(timezone.utc)<datetime.fromisoformat(passport['started_at']).replace(tzinfo=timezone.utc)
checks['hypothesis_and_threshold_recorded_before_run']=True
nb=json.loads((R/'notebooks/LR04_3.ngscript').read_text())
codes=[c for c in nb['cells'] if c['cell_type']=='code']
assert len(codes)==15
assert all(c.get('execution_count') is not None and c.get('outputs') for c in codes)
assert not any(o.get('output_type')=='error' for c in codes for o in c.get('outputs',[]))
streams=''.join(''.join(o.get('text',[])) for c in codes for o in c.get('outputs',[]) if o.get('output_type')=='stream')
assert 'ALL CHECKS PASS' in streams and 'MATCH_DEMO=true' in streams and 'Julia 1.12.4' in streams
assert sum('image/png' in o.get('data',{}) for c in codes for o in c.get('outputs',[]))==8
assert (A/'workspacearray_status.txt').read_text().startswith('EXECUTED')
checks['executed_notebook_all_cells_images_no_errors']=True
checks['workspacearray_example_executed']=True
result={'result':'PASS','checks':checks}
(R/'reports/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
