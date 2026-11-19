from pathlib import Path
import hashlib,json,zipfile
r=Path(__file__).resolve().parents[1]
files=[p for p in r.rglob('*') if p.is_file() and not any(v in p.relative_to(r).parts for v in ['tmp','__pycache__']) and p.suffix!='.zip' and p.name not in ['manifest.json','prepare_lr11.jl']]
m={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(r/'reports/manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
with zipfile.ZipFile(r/'ЛР11_Вариант_3_Сдача.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files+[r/'reports/manifest.json']:z.write(p,'LR11/'+str(p.relative_to(r)))
print('Packed',len(files)+1,'files')
