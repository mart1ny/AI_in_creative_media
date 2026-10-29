from pathlib import Path
import json,datetime,hashlib,uuid
R=Path(__file__).resolve().parents[1]
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()
hyp='''# Гипотеза и практические допуски до запуска

Вариант 3: бриф «афиша фестиваля робототехники», размер A=512×512, B=768×768. Только размер меняется; один шаг, guidance=0, fp16, свежий CPU-генератор для каждого вызова; seed 101–105, одна модель и GPU.

Гипотеза: увеличение стороны в 1,5 раза увеличит время более чем на 20%; рост сходства CLIP менее 1 пункта не оправдает увеличение размера. Направление изменения энергии границ и контраста заранее не считаем гарантированным. При 768 возможны дублирование частей и композиционные артефакты; их наличие проверяется глазами, не выводится из метрик.

Допуски: CLIP ±1,0 пункта; энергия границ и контраст ±10% среднего A; время ±20% среднего A. В пределах допуска — нейтрально; выше допуска для CLIP — улучшение, ниже — ухудшение. Для времени направление обратное. Для границ и контраста «улучшение/ухудшение» означает только увеличение/уменьшение данного показателя резкости/яркостного диапазона и не равно художественному качеству. Отдельно считаем |Δ|>2s_A по методичке; это эвристика разброса seed, не p-value и не формальный статистический тест.

CLIP измеряется относительно одного исходного английского брифа. Пространственные метрики также пересчитываются после приведения обоих изображений к 512×512 методом LANCZOS; это дополнительный контроль масштаба. Основная таблица остаётся результатом неизменённой функции преподавателя.

Ошибка guidance: ожидаем совпадение 0 и 1 и CFG=False; при 3 CFG=True и результат меняется. Проверяем фактически.
'''
p=R/'data/hypothesis.md'
if not p.exists():p.write_text(hyp+'\nЗаписано: '+now+'\n')
pre=R/'reports/pre_run_record.json'
if not pre.exists():pre.write_text(json.dumps(dict(recorded_at=now,hypothesis_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),ensure_ascii=False,indent=2))
cells=[]
def add(k,s):
 c=dict(cell_type=k,id=uuid.uuid4().hex[:8],metadata={},source=s.strip().splitlines(keepends=True))
 if k=='code':c.update(execution_count=None,outputs=[])
 cells.append(c)
def md(s):add('markdown',s)
def code(s):add('code',s)
md('''# Лабораторная работа №6. Исследование параметров text-to-image

Власюк Данил Витальевич, Т26ИИКТ-МИК11. **Вариант 3**: размер 512 → 768, бриф фестиваля робототехники. Цель — измерить эффект одного фактора на серии seed, отделив разброс и практическую пользу.

Выполнение по приложенной PDF-методичке: Google Colab, T4 GPU, отдельный ноутбук ЛР6. В учебной странице упомянута Engee, но исходники требуют PyTorch/CUDA и CLIP. Данные синтетические; реальные люди, бренды и закрытые материалы не используются.

Изучена [документация WorkspaceArray](https://engee.com/helpcenter/stable/ru/guide/workspacearray.html): это AbstractArray для временных рядов с ленивой загрузкой. Поля time/value дают временные метки и значения, срез остаётся ленивым; collect загружает данные. В текущем эксперименте используются тензоры PyTorch и PIL, а не WorkspaceArray.''')
md(p.read_text())
md('## 1. Среда и исходные скрипты\n\nВыбрать Runtime → Change runtime type → T4 GPU и Run all. Библиотеки и оба демо сохраняются без изменения; SHA-256 проверяется до запуска.')
code('''import sys,subprocess,json,hashlib,datetime,time,platform,pathlib,shutil
STARTED=datetime.datetime.now(datetime.timezone.utc).isoformat()
subprocess.check_call([sys.executable,'-m','pip','-q','install','diffusers==0.40.0','transformers==5.16.1','accelerate==1.15.0','safetensors==0.8.0','huggingface_hub==1.31.0','scipy','Pillow'])
import torch,numpy as np
assert torch.cuda.is_available(), 'Нужен GPU CUDA'
GPU=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv'],text=True)
print(STARTED,sys.version,torch.__version__,GPU)
OUT=pathlib.Path('/content/LR06_variant3_results');OUT.mkdir(exist_ok=True)
def write_json(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\\n')
''')
for f in ['lab05_lib.py','lab06_lib.py','lab05_demo.py','lab06_demo.py']:
 code('%%writefile '+f+'\n'+(R/'input'/f).read_text())
hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (R/'input').glob('*.py')}
code('EXPECTED='+repr(hashes)+'''\nfor name,sha in EXPECTED.items():
 assert hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()==sha,name
 print(name,sha)
 shutil.copy2(name,OUT/name)
''')
md('## 2. Полное выполнение предоставленных демо\n\nСначала запускается демо ЛР5 как дополнительная проверка базового конвейера, затем демо ЛР6 целиком, включая ошибку guidance=1. Их выводы относятся к демонстрационным условиям; индивидуальная таблица варианта 3 строится ниже.')
code('%run lab05_demo.py')
code('%run lab06_demo.py')
md('## 3. Вариант 3: один фактор, пять seed\n\nВызывается неизменённая M.variant_summary. Обёртка M.measure сохраняет каждое реально полученное изображение и метрики после измерения времени. Сам исходный файл не меняется. Стандартное отклонение — выборочное, ddof=1, по режиму A. Изменение размера меняет форму шума и композицию, поэтому PSNR между разными размерами не используется.')
code(r'''
import lab05_lib as L,lab06_lib as M
from PIL import Image
N=3;c,k=(N-1)//6,(N-1)%6
a_cfg,b_cfg=M.settings(M.FACTORS[k],c)
assert [x for x in a_cfg if a_cfg[x]!=b_cfg[x]]==['size']
print('A',a_cfg,'B',b_cfg)
records=[]
original_measure=M.measure
def recorded_measure(pipe,clip,cfg,c,seed):
    torch.cuda.synchronize()
    values,img=original_measure(pipe,clip,cfg,c,seed)
    condition='A' if cfg==a_cfg else 'B'
    folder=OUT/f'{condition}_{seed}';folder.mkdir(exist_ok=True)
    payload=L.png_bytes(img);(folder/'result.png').write_bytes(payload)
    rec=dict(condition=condition,seed=seed,settings=cfg,metrics=values,sha256=L.sha(payload),file=str(folder.relative_to(OUT)/'result.png'))
    write_json(folder/'manifest.json',rec);records.append(rec)
    return values,img
M.measure=recorded_measure
try:result=M.variant_summary(pipe,clip,N)
finally:M.measure=original_measure
assert len(records)==10
write_json(OUT/'records.json',records);write_json(OUT/'summary.json',result)
for row in result['rows']:print(row)
''')
md('## 4. Практическая классификация и контроль масштаба\n\nДопуски заданы до запуска. Критерий 2s и практический допуск считаются отдельно. Рост границ/контраста сам по себе не доказывает улучшения дизайна. Для контроля размера повторно измеряются границы и контраст при общем масштабе 512×512; CLIP в основной таблице уже включает штатное масштабирование препроцессором.')
code(r'''
from IPython.display import display,Markdown
TOLS={'clip':1.,'edge':.10,'contrast':.10,'seconds':.20}
def classify_rows(rows):
    out=[]
    for metric,a,s,b,d,ratio,sig in rows:
        tolerance=TOLS[metric] if metric=='clip' else TOLS[metric]*abs(a)
        practical=bool(abs(d)>tolerance)
        direction=-d if metric=='seconds' else d
        label='нейтрально' if not practical else 'улучшение' if direction>0 else 'ухудшение'
        out.append(dict(metric=metric,A=a,s_A=s,B=b,delta=d,ratio=ratio,over_2s=sig,tolerance=tolerance,practical=practical,label=label,criteria_disagree=bool(sig)!=practical))
    return out
classified=classify_rows(result['rows'])
write_json(OUT/'classification.json',classified)
def table(rows):
    header='| Метрика | A | s_A | B | Δ | abs(Δ)/s | >2s | Допуск | Класс |\n|---|---:|---:|---:|---:|---:|---|---:|---|\n'
    return header+'\n'.join(f"| {r['metric']} | {r['A']:.6f} | {r['s_A']:.6f} | {r['B']:.6f} | {r['delta']:+.6f} | {r['ratio']:.3f} | {r['over_2s']} | {r['tolerance']:.6f} | {r['label']} |" for r in rows)
display(Markdown(table(classified)))
print('Расхождения критериев:',[r['metric'] for r in classified if r['criteria_disagree']])
normalized=[]
for r in records:
    img=Image.open(OUT/r['file']).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
    normalized.append(dict(condition=r['condition'],seed=r['seed'],edge=M.edge_energy(img),contrast=M.contrast(img)))
rows=[]
for metric in ['edge','contrast']:
    aa=np.array([r[metric] for r in normalized if r['condition']=='A']);bb=np.array([r[metric] for r in normalized if r['condition']=='B'])
    d=float(bb.mean()-aa.mean());s=float(aa.std(ddof=1))
    rows.append((metric,float(aa.mean()),s,float(bb.mean()),d,abs(d)/s if s else float('inf'),bool(abs(d)>2*s)))
norm_class=classify_rows(rows)
write_json(OUT/'normalized_512.json',dict(records=normalized,classification=norm_class))
display(Markdown('### Общий масштаб 512×512\n'+table(norm_class)))
pair=[Image.open(OUT/f'{cond}_101/result.png').convert('RGB').resize((384,384),Image.Resampling.LANCZOS) for cond in ['A','B']]
sheet=Image.new('RGB',(768,384));sheet.paste(pair[0],(0,0));sheet.paste(pair[1],(384,0));sheet.save(OUT/'comparison.png')
print('Seed 101: A 512 слева; B 768 справа; одинаковый размер показа, оригиналы сохранены.')
display(sheet)
''')
md('## 5. Намеренная ошибка: guidance=1\n\nПроверяем на своём брифе и seed 101, сохраняем изображения. Симптом — ожидать включения CFG при 1; диагностика — SHA-256 и pipe.do_classifier_free_guidance после каждого вызова. При 3 CFG активен, но это исследование за пределами рекомендованного режима SD-Turbo.')
code(r'''
guidance=[];gimgs=[]
for value in [0.,1.,3.]:
    img=L.generate(pipe,L.BRIEFS[c],101,guidance=value)[0]
    payload=L.png_bytes(img);name=f'guidance_{int(value)}.png';(OUT/name).write_bytes(payload)
    guidance.append(dict(guidance=value,cfg_active=bool(pipe.do_classifier_free_guidance),sha256=L.sha(payload),file=name));gimgs.append(img)
error_check=dict(records=guidance,equal_0_1=guidance[0]['sha256']==guidance[1]['sha256'],psnr_0_3=L.psnr_db(gimgs[0],gimgs[2]))
assert error_check['equal_0_1'] and [r['cfg_active'] for r in guidance]==[False,False,True]
write_json(OUT/'guidance_check.json',error_check);print(json.dumps(error_check,indent=2))
''')
md('''## 6. Вывод, ограничения и контрольные вопросы

Численное заключение формируется по фактическим измерениям. Визуальное описание сравнительного листа добавляется после осмотра сохранённых изображений. Пять seed и одна модель не позволяют переносить вывод на все генераторы. Энергия границ растёт также от артефактов; контраст зависит от композиции, CLIP не измеряет эстетику. Критерий 2s методички не является формальным тестом значимости; время зависит от прогрева, GPU и фоновой нагрузки. Отдельный новый сеанс не проверяется автоматически.

1. Шаги — число итераций шумоподавления. SD-Turbo дистиллирована для 1–4 шагов; больше шагов не гарантирует лучшее качество.
2. Размер 768 вне рекомендуемых 512 меняет распределение пространственных структур; возможны повторы объектов и анатомические ошибки.
3. Seed фиксирует начальное состояние генератора, но не одинаковый результат при разных формах тензора, версиях, GPU или параметрах.
4. CLIP здесь — 100×cos(image,text), не CLIPScore и не эстетическая оценка; бриф для сравнения один английский.
5. Выборочное s оценивает разброс A между seed; |Δ|>2s — учебная эвристика эффекта относительно разброса, практический допуск — заранее выбранная полезная величина.
6. Совпадение или расхождение этих критериев указывается для каждой метрики; нельзя подгонять допуск после результата.
7. Нельзя менять prompt одновременно с размером: влияние факторов станет неразличимым.
8. Guidance 1 не включает CFG в этом конвейере; нужен scale>1. Для SD-Turbo рекомендован 0, а 3 используется только как контроль ошибки.
9. Рост границ/контраста может означать шум, пересветы или раздробленную композицию; требуется осмотр.
10. Для воспроизведения нужны модель и ревизия, GPU/драйвер, версии, dtype, seed, prompt и параметры, прогрев, методы расчёта и сохранённые артефакты.

Источники: приложенная методичка и неизменённые скрипты; [SD-Turbo, закреплённая ревизия](https://huggingface.co/stabilityai/sd-turbo/tree/b261bac6fd2cf515557d5d0707481eafa0485ec2), [лицензия](https://huggingface.co/stabilityai/sd-turbo/blob/b261bac6fd2cf515557d5d0707481eafa0485ec2/LICENSE.md); [CLIP, закреплённая ревизия](https://huggingface.co/openai/clip-vit-base-patch32/tree/3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268). Открытый доступ к весам не означает отсутствия лицензионных ограничений; запуск учебный, коммерческие права не исследуются. Индивидуальный вклад: гипотеза, допуски, сохранение серии, независимый пересчёт, контроль масштаба, анализ и отчёт.''')
code(r'''
lines=['# Численный вывод варианта 3',table(classified),'\nРасхождения 2s и допуска: '+str([r['metric'] for r in classified if r['criteria_disagree']]),'\nРост показателей границ/контраста не равен росту художественного качества.']
(OUT/'conclusion.md').write_text('\n\n'.join(lines));display(Markdown('\n\n'.join(lines)))
import importlib.metadata as metadata
packages={name:metadata.version(name) for name in ['torch','diffusers','transformers','accelerate','safetensors','huggingface_hub','numpy','scipy','Pillow']}
passport=dict(student='Власюк Данил Витальевич',group='Т26ИИКТ-МИК11',variant=N,started_utc=STARTED,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_id=L.MODEL_ID,revision=L.REVISION,clip_id=M.CLIP_ID,clip_revision=M.CLIP_REVISION,gpu=GPU,python=sys.version,platform=platform.platform(),packages=packages,seeds=list(M.SEEDS),settings_A=a_cfg,settings_B=b_cfg,generator='cpu; fresh generator each call',dtype=str(pipe.unet.dtype),tolerances=TOLS,source_sha256=EXPECTED,independent_new_session_tested=False)
write_json(OUT/'passport.json',passport)
(OUT/'environment.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
archive=shutil.make_archive('/content/LR06_variant3_results','zip',OUT)
print('COMPLETE; ARCHIVE',archive)
from google.colab import files
files.download(archive)
''')
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3'),colab=dict(name='LR06_3.ipynb'),accelerator='GPU'),cells=cells)
p=R/'notebooks/prepared';p.mkdir(exist_ok=True);(p/'LR06_3.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(cells),'cells',p)
