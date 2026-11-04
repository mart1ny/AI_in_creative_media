"""Собственный запуск только варианта 3; учебная библиотека не изменяется."""
import json,sys,time,platform,hashlib
from pathlib import Path
import importlib.metadata as md
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)
def save(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2))
import lab09_lib as L
save('environment.json',dict(started=time.strftime('%Y-%m-%dT%H:%M:%S%z'),python=sys.version,platform=platform.platform(),packages={p:md.version(p) for p in ['torch','diffusers','transformers','numpy','scipy','Pillow']},model=L.MODEL_ID,revision=L.REVISION,clip=L.CLIP_ID,clip_revision=L.CLIP_REVISION,seeds=list(L.SEEDS),steps=L.STEPS,guidance=L.GUIDANCE,size=L.SIZE,device='cpu',source_sha256=hashlib.sha256((ROOT/'lab09_lib.py').read_bytes()).hexdigest()))
print('Loading SD-Turbo and CLIP',flush=True)
pipe=L.load_pipe();clip=L.load_clip()
L.generate(pipe,L.prompt_a(0),0)
a=[];b=[]
for mode,prompt,records in [('A',L.prompt_a(0),a),('B',L.prompt_b(0,2),b)]:
 for seed in L.SEEDS:
  r,img=L.measure(pipe,clip,0,prompt,seed);r['seed']=seed;records.append(r)
  img.save(OUT/f'{mode}_{seed}.png')
  save(f'{mode}_per_seed.json',records)
  print(mode,seed,r,flush=True)
rows=L.compare(a,b,2)
save('comparison.json',dict(variant=3,prompt_a=L.prompt_a(0),prompt_b=L.prompt_b(0,2),target=L.ELEMENTS[0][2][1],rows=rows))
print('COMPLETE',json.dumps(rows),flush=True)
