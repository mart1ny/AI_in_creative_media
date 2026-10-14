"""Упаковка полного комплекта ЛР4 с проверкой SHA-256 и ZIP CRC."""
from pathlib import Path
import hashlib, json, zipfile
R=Path(__file__).resolve().parents[1]
files=[R/'README.md',R/'.gitignore']
for folder in ['src','data','artifacts','scripts','reports']:
    files.extend(p for p in (R/folder).rglob('*') if p.is_file()
                 and '__pycache__' not in p.parts and p.name!='artifact_manifest.json')
files.extend([R/'notebooks/LR04_3.ngscript',R/'notebooks/LR04_3.ipynb'])
files.extend(p for p in (R/'input').iterdir()
             if p.is_file() and p.suffix in {'.jl','.json','.md'})
files=sorted(set(files))
manifest={str(p.relative_to(R)):{'bytes':p.stat().st_size,
          'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
mp=R/'reports/artifact_manifest.json'
mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=R/'ЛР04_Вариант_3_Сдача.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,strict_timestamps=False) as z:
    for p in files+[mp]:z.write(p,'LR4/'+str(p.relative_to(R)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,expected in manifest.items():
        data=z.read('LR4/'+name)
        assert len(data)==expected['bytes']
        assert hashlib.sha256(data).hexdigest()==expected['sha256']
print(f'PASS: {len(files)+1} files; {archive.stat().st_size} bytes; {archive}')
