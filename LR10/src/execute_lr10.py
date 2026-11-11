"""Вариант 3. Восстановлено по приложению А методички ЛР10; ZIP не предоставлен."""
import os,time,gc,json,random,sys,platform,hashlib
from pathlib import Path
import importlib.metadata as md
import numpy as np
import torch
from PIL import Image
from scipy import ndimage
from diffusers import DiffusionPipeline
from transformers import CLIPModel,CLIPProcessor
R=Path(__file__).resolve().parent;O=R/'artifacts';O.mkdir(exist_ok=True)
torch.set_num_threads(min(4,torch.get_num_threads()))
PROMPT='editorial poster concept for a robotics festival, glowing mechanical arm silhouette, deep blue and amber palette, clean composition, no text, no logo, no people'
CONFIGS={'turbo':dict(repo='stabilityai/sd-turbo',revision='b261bac6fd2cf515557d5d0707481eafa0485ec2',steps=1,guidance=0.,size=512),'amused':dict(repo='amused/amused-256',revision='09b6259bf96dbe6d70a852b70812420fe02df55e',steps=12,guidance=10.,size=256)}
CLIP_ID='openai/clip-vit-large-patch14';CLIP_REV='32bd64288804d66eefd0ccbe215aa642df71cc41'
SEEDS=list(range(101,106));METRICS=['clip_brief','clip_text','edge','contrast','seconds']
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2))
def generate(pipe,c,seed):
 g=torch.Generator('cpu').manual_seed(seed);t=time.perf_counter()
 img=pipe(PROMPT,num_inference_steps=c['steps'],guidance_scale=c['guidance'],height=c['size'],width=c['size'],generator=g).images[0]
 return img,time.perf_counter()-t
@torch.no_grad()
def sims(model,proc,img):
 out=model(**proc(text=[PROMPT,'written text and letters'],images=img,return_tensors='pt',padding=True,truncation=True))
 a=out.image_embeds/out.image_embeds.norm(dim=-1,keepdim=True);b=out.text_embeds/out.text_embeds.norm(dim=-1,keepdim=True)
 return [float(v)*100 for v in (a@b.T)[0]]
def main():
 save('passport.json',dict(started=time.strftime('%Y-%m-%dT%H:%M:%S%z'),python=sys.version,platform=platform.platform(),packages={p:md.version(p) for p in ['torch','diffusers','transformers','numpy','scipy','Pillow']},configs=CONFIGS,clip=CLIP_ID,clip_revision=CLIP_REV,prompt=PROMPT,seeds=SEEDS,device='cpu',dtype='float32',threads=torch.get_num_threads(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
 clip=CLIPModel.from_pretrained(CLIP_ID,revision=CLIP_REV,use_safetensors=True).eval();proc=CLIPProcessor.from_pretrained(CLIP_ID,revision=CLIP_REV);res={}
 for key,c in CONFIGS.items():
  print('LOADING',key,flush=True)
  pipe=DiffusionPipeline.from_pretrained(c['repo'],revision=c['revision'],torch_dtype=torch.float32,safety_checker=None,requires_safety_checker=False,use_safetensors=True);pipe.set_progress_bar_config(disable=True)
  save(key+'_scheduler.json',dict(type=type(pipe.scheduler).__name__,config=dict(pipe.scheduler.config)))
  generate(pipe,c,0);res[key]=[]
  for seed in SEEDS:
   img,seconds=generate(pipe,c,seed);cs=sims(clip,proc,img)
   x=np.asarray(img.convert('RGB').resize((256,256)),dtype=np.float64)/255;y=.299*x[...,0]+.587*x[...,1]+.114*x[...,2]
   rec=dict(seed=seed,clip_brief=cs[0],clip_text=cs[1],edge=float(np.hypot(ndimage.sobel(y,axis=0),ndimage.sobel(y,axis=1)).mean()/8),contrast=float(y.std()),seconds=seconds)
   img.save(O/f'{key}_s{seed}.png');img.save(O/f'{key}_s{seed}.jpg',quality=90);res[key].append(rec);save('per_seed.json',res);print(key,rec,flush=True)
  del pipe;gc.collect()
 rows=[]
 for m in METRICS:
  a=np.array([x[m] for x in res['turbo']]);b=np.array([x[m] for x in res['amused']]);d=float(b.mean()-a.mean());s=float(a.std(ddof=1));rows.append([m,float(a.mean()),s,float(b.mean()),d,abs(d)/s,bool(abs(d)>2*s)])
 save('summary.json',dict(variant=3,pair=['turbo','amused'],rows=rows))
 rng=random.Random(3);keymap={}
 for seed in SEEDS:
  left,right=('turbo','amused') if rng.random()<.5 else ('amused','turbo');keymap[str(seed)]=left
  sheet=Image.new('RGB',(780,384),'white')
  for model,x in [(left,0),(right,396)]:sheet.paste(Image.open(O/f'{model}_s{seed}.jpg').convert('RGB').resize((384,384)),(x,0))
  sheet.save(O/f'blind_{seed}.png')
 save('blind_key.json',keymap);print('COMPLETE',json.dumps(rows),flush=True)
if __name__=='__main__':main()
