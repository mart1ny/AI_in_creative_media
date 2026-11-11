from pathlib import Path
import zipfile,json,hashlib
R=Path(__file__).resolve().parents[1]
files=[p for p in R.rglob('*') if p.is_file() and not any(x in p.parts for x in ['tmp','__pycache__']) and p.name not in ['prepare_lr10.jl','manifest.json'] and p.suffix!='.zip']
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(R/'reports/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(R/'ЛР10_Вариант_3_Сдача.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files+[R/'reports/manifest.json']:z.write(p,'LR10/'+str(p.relative_to(R)))
print('Packaged',len(files)+1,'files')
