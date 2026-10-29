"""Export the executed Colab notebook, keeping actual code, output and figures."""
from pathlib import Path
import base64,json
R=Path(__file__).resolve().parents[1]
nb=json.loads((R/'notebooks/LR06_3.ipynb').read_text())
def txt(v):return ''.join(v) if isinstance(v,list) else v
figdir=R/'artifacts/notebook_figures';figdir.mkdir(exist_ok=True)
parts=['[Выполненный ноутбук Colab](https://colab.research.google.com/drive/1KBal7Z1NTIviMGRXmHuv-UI54IHZB-jy). [Локальная копия с выводами](../notebooks/LR06_3.ipynb).\n\nНиже — экспорт фактически выполненного ноутбука. Служебный HTML загрузки архива опущен.']
image_index=0
for c in nb['cells']:
    source=txt(c['source'])
    if c['cell_type']=='markdown':parts.append(source)
    else:
        parts.append('```python\n'+source.rstrip()+'\n```')
        for o in c.get('outputs',[]):
            data=o.get('data',{})
            if o.get('output_type')=='stream':parts.append('```text\n'+txt(o.get('text','')).rstrip()+'\n```')
            elif 'text/markdown' in data:parts.append(txt(data['text/markdown']))
            elif 'image/png' in data:
                image_index+=1;name=f'figure_{image_index:02d}.png'
                (figdir/name).write_bytes(base64.b64decode(txt(data['image/png'])))
                parts.append(f'![Результат выполнения {image_index}](../artifacts/notebook_figures/{name})')
            elif 'text/html' not in data and 'text/plain' in data:parts.append('```text\n'+txt(data['text/plain']).rstrip()+'\n```')
(R/'reports/ЛР06_Вариант_3_Отчёт.md').write_text('\n\n'.join(parts)+'\n')
print('Exported actual outputs, figures:',image_index)
