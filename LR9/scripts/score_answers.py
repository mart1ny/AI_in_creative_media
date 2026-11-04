from pathlib import Path
import json,sys,statistics,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import lab09_llm as L
out={}
for method in ['zero','few','step']:
 paths=[R/'answers'/f'ctx1_{method}_r{i}.txt' for i in range(1,4)]
 if not all(p.exists() for p in paths):continue
 scores=[L.score_file(p,1) for p in paths]
 out[method]={**{k:statistics.mean(s[k] for s in scores) for k in ['k1','k2','k3']},'k4':L.stability(paths),'per_repeat':scores,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(R/'reports/llm_scores.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
