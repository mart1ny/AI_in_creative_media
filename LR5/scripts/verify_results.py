"""Independent checks of downloaded Colab results; Python, NumPy and Pillow."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'artifacts'
def read(name):return json.loads((A/name).read_text())
def array(folder):return np.asarray(Image.open(A/folder/'result.png').convert('RGB'),dtype=np.float64)
def compare(x,y):
    mse=float(np.mean((x-y)**2));psnr=math.inf if mse==0 else 10*math.log10(255**2/mse)
    return dict(mse=mse,psnr=psnr,max_diff=int(np.max(np.abs(x-y))),pixel_equal=bool(np.array_equal(x,y)),verdict='identical' if mse==0 else 'close' if psnr>=40 else 'different')
checks={}
for folder in ['A_cpu','B_cuda','repeat_fresh_cpu','shared_generator_first','shared_generator_second','fixed_noise_first','fixed_noise_second']:
    manifest=read(folder+'/manifest.json');p=A/folder/'result.png'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['sha256'],folder
    with Image.open(p) as img:assert img.size==(512,512) and img.mode=='RGB'
    assert manifest['model_id']=='stabilityai/sd-turbo'
    assert manifest['revision']=='b261bac6fd2cf515557d5d0707481eafa0485ec2'
    assert manifest['seed']==1003 and manifest['steps']==1 and manifest['guidance_scale']==0
checks['images_manifests_and_sha']=True
for a,b,file in [('A_cpu','B_cuda','comparison_main.json'),('A_cpu','repeat_fresh_cpu','comparison_repeat.json'),('shared_generator_first','shared_generator_second','comparison_shared_generator.json'),('fixed_noise_first','fixed_noise_second','comparison_fixed_noise.json'),('A_cpu','fixed_noise_first','comparison_A_vs_explicit_noise.json')]:
    expected=read(file);actual=compare(array(a),array(b))
    for key in ['mse','psnr']:
        assert math.isclose(actual[key],expected[key],rel_tol=1e-10,abs_tol=1e-10),(file,key)
    for key in ['max_diff','pixel_equal','verdict']:assert actual[key]==expected[key],(file,key)
checks['pixel_mse_psnr_and_classification']=True
main=read('comparison_main.json');standard=read('variant_summary.json')
assert main['sha_a']==standard['sha_a'] and main['sha_b']==standard['sha_b']
assert read('comparison_repeat.json')['pixel_equal']
assert read('comparison_fixed_noise.json')['pixel_equal']
assert read('comparison_A_vs_explicit_noise.json')['pixel_equal']
assert not read('comparison_shared_generator.json')['pixel_equal']
checks['repeat_error_and_controlled_comparison']=True
nc=np.load(A/'initial_noise_cpu.npy');ng=np.load(A/'initial_noise_cuda.npy');reported=read('comparison_initial_noise.json')
assert nc.shape==ng.shape==tuple(reported['shape'])
assert not np.array_equal(nc,ng)
assert math.isclose(float(np.max(np.abs(nc-ng))),reported['max_diff'],rel_tol=1e-6)
assert math.isclose(float(np.mean((nc.astype(float)-ng.astype(float))**2)),reported['mse'],rel_tol=1e-6)
checks['initial_noise_differs_before_model']=True
passport=read('passport.json')
pre=json.loads((R/'reports/pre_run_record.json').read_text())
assert hashlib.sha256((R/'data/hypothesis.md').read_bytes()).hexdigest()==pre['hypothesis_sha256']
assert datetime.fromisoformat(pre['recorded_at']).astimezone(timezone.utc)<datetime.fromisoformat(passport['started_utc'])
assert (R/'src/lab05_lib.py').read_bytes()==(A/'lab05_lib.py').read_bytes()==(R/'input/lab05_lib.py').read_bytes()
assert (R/'src/lab05_demo.py').read_bytes()==(A/'lab05_demo.py').read_bytes()==(R/'input/lab05_demo.py').read_bytes()
checks['hypothesis_before_run_and_teacher_sources_unchanged']=True
nb=json.loads((R/'notebooks/LR05_3.ipynb').read_text());codes=[c for c in nb['cells'] if c['cell_type']=='code']
assert all(c.get('execution_count') is not None for c in codes)
assert not any(o.get('output_type')=='error' for c in codes for o in c.get('outputs',[]))
streams=''.join(''.join(o.get('text',[])) for c in codes for o in c.get('outputs',[]) if o.get('output_type')=='stream')
assert 'ALL NUMERICAL CHECKS PASS True' in streams and 'COMPLETE; ARCHIVE' in streams
checks['executed_notebook_without_errors']=True
result={'result':'PASS','checks':checks}
(R/'reports/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
