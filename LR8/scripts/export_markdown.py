"""Export actual Engee notebook code and outputs to Markdown; no invented outputs."""
from pathlib import Path
import base64,json
R=Path(__file__).resolve().parents[1]
nb=json.loads((R/'notebooks/LR08_3.ngscript').read_text())
def txt(v):return ''.join(v) if isinstance(v,list) else v
figdir=R/'artifacts/notebook_figures';figdir.mkdir(exist_ok=True)
parts=['[Выполненный ноутбук Engee](../notebooks/LR08_3.ngscript). [Копия Jupyter](../notebooks/LR08_3.ipynb).\n\nЭкспорт фактически исполненного в Engee ноутбука; вывод Python получен вызовом из Julia.']
index=0
for c in nb['cells']:
 source=txt(c['source'])
 if c['cell_type']=='markdown':parts.append(source)
 else:
  parts.append('```julia\n'+source.rstrip()+'\n```')
  for o in c.get('outputs',[]):
   data=o.get('data',{})
   if o.get('output_type')=='stream':parts.append('```text\n'+txt(o.get('text','')).rstrip()+'\n```')
   elif 'text/markdown' in data:parts.append(txt(data['text/markdown']))
   elif 'image/png' in data:
    index+=1;name=f'figure_{index:02d}.png';(figdir/name).write_bytes(base64.b64decode(txt(data['image/png'])));parts.append(f'![Фактический вывод {index}](../artifacts/notebook_figures/{name})')
   elif 'text/plain' in data and 'text/html' not in data:parts.append('```text\n'+txt(data['text/plain']).rstrip()+'\n```')
(R/'reports/ЛР08_Вариант_3_Отчёт.md').write_text('\n\n'.join(parts)+'\n')
print('Exported actual Engee outputs; figures',index)
