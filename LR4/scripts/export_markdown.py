"""Экспорт фактически исполненного ноутбука с пояснениями и результатами."""
from pathlib import Path
import base64, json
R=Path(__file__).resolve().parents[1]
nb=json.loads((R/'notebooks/LR04_3.ngscript').read_text())
def txt(v):return ''.join(v) if isinstance(v,list) else v
names=['scene_noisy_reference','box5_comparison','gauss1_comparison','gauss3_comparison',
       'unsharp_comparison','sobel_comparison','otsu_open_comparison','disc_edge_detail']
figdir=R/'artifacts/notebook_figures'
figdir.mkdir(exist_ok=True)
parts=[]
image_index=0
for c in nb['cells']:
    source=txt(c['source'])
    if c['cell_type']=='markdown':parts.append(source)
    else:
        parts.append('```julia\n'+source.rstrip()+'\n```')
        for o in c.get('outputs',[]):
            data=o.get('data',{})
            if o.get('output_type')=='stream':
                parts.append('```text\n'+txt(o.get('text','')).rstrip()+'\n```')
            elif 'text/markdown' in data:parts.append(txt(data['text/markdown']))
            elif 'image/png' in data:
                name=names[image_index]+'.png'
                (figdir/name).write_bytes(base64.b64decode(txt(data['image/png'])))
                parts.append(f'![Результат выполнения {image_index+1}](../artifacts/notebook_figures/{name})')
                image_index+=1
            elif o.get('output_type')=='display_data' and 'text/plain' in data:
                parts.append('```text\n'+txt(data['text/plain']).rstrip()+'\n```')
assert image_index==8
(R/'reports/ЛР04_Вариант_3_Отчёт.md').write_text('\n\n'.join(parts)+'\n')
print('Exported executed notebook to Markdown with 8 figures')
