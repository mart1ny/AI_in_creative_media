"""Сборка комплекта ЛР03 и проверка его целостности (stdlib Python)."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
files = [root / 'README.md', root / '.gitignore']
for folder in ['src', 'data', 'engee', 'artifacts', 'scripts']:
    files.extend(p for p in (root / folder).rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts)
files.extend(p for p in (root / 'reports').iterdir()
             if p.is_file() and p.name != 'artifact_manifest.json')
files.extend(root / 'input' / name for name in
             ['method.md', 'variants_lr03.json', 'engee_run_log.md', 'lab03_lib.jl'])
files = sorted(set(files))
manifest = {str(p.relative_to(root)): {
    'bytes': p.stat().st_size,
    'sha256': hashlib.sha256(p.read_bytes()).hexdigest()
} for p in files}
manifest_path = root / 'reports/artifact_manifest.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
archive = root / 'ЛР03_Вариант_3_Сдача.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED,
                     strict_timestamps=False) as z:
    for p in files + [manifest_path]:
        z.write(p, 'LR3/' + str(p.relative_to(root)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name, expected in manifest.items():
        data = z.read('LR3/' + name)
        assert len(data) == expected['bytes']
        assert hashlib.sha256(data).hexdigest() == expected['sha256']
print(f'PASS: {len(files) + 1} files, {archive.stat().st_size} bytes; {archive}')
