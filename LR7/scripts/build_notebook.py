from pathlib import Path
import json,hashlib,uuid,datetime
R=Path(__file__).resolve().parents[1];cells=[]
def add(k,s):
 c=dict(cell_type=k,id=uuid.uuid4().hex[:8],metadata={},source=s.strip().splitlines(keepends=True))
 if k=='code':c.update(execution_count=None,outputs=[])
 cells.append(c)
def md(s):add('markdown',s)
def code(s):add('code',s)
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()
hyp='''# Гипотеза и допуски до обучения

Вариант 3, набор disc: один янтарный диск на градиентном фоне, факторы x, y, радиус. A=ConvAE(d=8), B=DenseAE(d=8). Меняется только семейство архитектуры, а число параметров является его следствием: это не сравнение моделей одинаковой ёмкости.

Гипотеза: полносвязная сеть с 256 скрытыми нейронами будет иметь существенно больше параметров. Свёрточная структура полезна для пространственных закономерностей, но преимущество по PSNR при данном объёме данных не гарантируется. Проверим направленное ожидание: выигрыш B относительно A не превысит 1 дБ и не оправдает увеличение ёмкости. Время может отличаться из-за разных операций; заранее не задаём его направление.

Общие условия: данные seed 7, 4096 обучающих и 1024 тестовых сцены, 32×32 RGB; обучение seed 101–105; Adam, lr=0.002, batch=128, 20 эпох (640 обновлений), MSE, чистые входы, dtype=float32, одна T4.

Допуски: тестовый PSNR ±1 дБ; разрыв train−test ±0.1 дБ; время ±20% среднего A; для числа параметров дополнительный ресурсный допуск ±20% A. Для PSNR рост выше допуска — улучшение. Для времени и числа параметров снижение выше допуска — экономия (улучшение); для разрыва рост — ухудшение обобщения, а снижение — улучшение лишь в смысле этого показателя, не доказательство качества. В пределах допуска — нейтрально.

Отдельно рассчитываем |Δ|>2s_A по методичке: учебная эвристика, не p-value. При s=0 и ненулевом Δ отношение бесконечно; у числа параметров это детерминированное различие, а не статистическое доказательство. Эталон — среднее только по train, оценённое на test. PSNR усредняется по изображениям, а не вычисляется из общего среднего MSE.

Ошибка интерпретации: нельзя объявлять PSNR «хорошим» без эталона или малое d достаточным без диагностики. Проверим ConvAE d=1,2,3,4,8 на seed 101–103. Непрерывных факторов три, но пиксельный рендер дискретен; из одного числа факторов нельзя выводить строгое универсальное минимальное d. Нужны измерения, архитектура и оговорки.
'''
p=R/'data/hypothesis.md'
if not p.exists():p.write_text(hyp+'\nЗаписано: '+now+'\n')
pre=R/'reports/pre_run_record.json'
if not pre.exists():pre.write_text(json.dumps(dict(recorded_at=now,hypothesis_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
md('''# Лабораторная работа №7. Построение автокодировщика

Власюк Данил Витальевич, Т26ИИКТ-МИК11. Вариант 3: набор «диск», архитектура conv → dense, d=8.

Цель: собрать и обучить автокодировщики, оценить реконструкцию на отложенной выборке, сравнить с тривиальным эталоном и отделить эффект архитектуры от разброса seed и ресурсной цены. Выполнение в отдельном ноутбуке Colab/T4 по приложенным PDF и Python-скриптам. Упоминание Engee в карточке задания расходится с требованиями приложений.

Задание 1: изучена [документация WorkspaceArray Engee](https://engee.com/helpcenter/stable/ru/guide/workspacearray.html). Этот AbstractArray представляет временные ряды с ленивой загрузкой. Поля time/value дают времена и значения, срез не копирует данные, collect загружает их в DataFrame. Для обучения ниже используются тензоры PyTorch.

Сцены синтетические, генерируются приложенным кодом; внешних фотографий и предобученных весов нет. Исходники преподавателя сохранены без изменения. Архивные результаты преподавателя не выдаются за свои.''')
md(p.read_text())
md('## 1. Среда и исходники\n\nВыбрать T4 GPU и Run all. Обучение на CPU намеренно не запускается. SHA-256 обеих библиотек из архива совпадают; используется lab07_lib.py. Версии и настройки фиксируются фактически.')
code(r'''
import sys,subprocess,datetime,time,pathlib,json,hashlib,shutil,platform
import numpy as np,torch
from PIL import Image
from IPython.display import display,Markdown
STARTED=datetime.datetime.now(datetime.timezone.utc).isoformat()
assert torch.cuda.is_available(),'Выберите GPU T4'
GPU=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv'],text=True)
print(STARTED,sys.version,torch.__version__,GPU)
OUT=pathlib.Path('/content/LR07_variant3_results');OUT.mkdir(exist_ok=True)
def write_json(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
''')
for f in ['lab07_lib.py','lab07_demo.py']:code('%%writefile '+f+'\n'+(R/'input'/f).read_text())
expected={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'input').glob('*.py')}
code('EXPECTED='+repr(expected)+r'''
for name,sha in EXPECTED.items():
 assert hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()==sha,name
 shutil.copy2(name,OUT/name);print(name,sha)
import lab07_lib as L
assert L.DEVICE=='cuda'
''')
md('## 2. Предоставленное демо целиком\n\nlab07_demo.py выполняется без изменения. Обёртка L.run фиксирует возвращённые метрики после каждого обучения; код обучения и измерения времени не меняется. Демо использует тот же набор disc, поэтому его диагностика d=1,2,3,4,8 на seed 101–103 применима к нашему набору без повторного обучения. Диагностика относится к ConvAE; переносить её автоматически на DenseAE нельзя.')
code(r'''
original_run=L.run;demo_records=[]
def demo_recorded_run(kind,cfg,seed):
    metrics,model=original_run(kind,cfg,seed)
    demo_records.append(dict(kind=kind,settings=dict(cfg),seed=seed,metrics=metrics))
    return metrics,model
L.run=demo_recorded_run
try:
    exec(compile(pathlib.Path('lab07_demo.py').read_text(),'lab07_demo.py','exec'),globals())
finally:L.run=original_run
assert len(demo_records)==28
write_json(OUT/'demo_records.json',demo_records)
write_json(OUT/'demo_summary.json',result)
shutil.copy2('comparison.png',OUT/'comparison_demo_variant01.png')
display(sheet)
diagnostic=demo_records[11:26]
assert [r['settings']['d'] for r in diagnostic]==[d for d in [1,2,3,4,8] for _ in range(3)]
write_json(OUT/'diagnostic.json',diagnostic)
''')
md('## 3. Данные, архитектуры и эталон\n\nConvAE: три свёртки с шагом 2 (32→16→8→4), линейное сжатие в 8 чисел; декодер выполняет обратное развёртывание и ConvTranspose2d, Sigmoid ограничивает RGB в 0…1. DenseAE: Flatten 3072→256→8→256→3072, ReLU и Sigmoid. Пространственные связи у DenseAE не встроены, количество весов меняется вместе с архитектурой. Обе модели обучаются MSE и оцениваются средним PSNR по 1024 test-сценам. Эталон вычисляется только из train.')
code(r'''
N=3;c,k=(N-1)//6,(N-1)%6
kind=L.KINDS[c];a_cfg,b_cfg=L.settings(L.FACTORS[k])
assert [key for key in a_cfg if a_cfg[key]!=b_cfg[key]]==['arch']
Xtr,Xte,Ftr,Fte=L.dataset(kind)
assert Xtr.shape==(4096,3,32,32) and Xte.shape==(1024,3,32,32)
np.savez_compressed(OUT/'dataset.npz',train=Xtr.cpu().numpy(),test=Xte.cpu().numpy(),factors_train=Ftr.cpu().numpy(),factors_test=Fte.cpu().numpy())
mean_train=Xtr.mean(0,keepdim=True)
baseline=L.psnr_images(mean_train.expand_as(Xte),Xte)
np.save(OUT/'mean_train.npy',mean_train.cpu().numpy())
write_json(OUT/'baseline.json',dict(psnr=baseline,method='mean over training images only, average per-image test PSNR',train=4096,test=1024,data_seed=7,scene_factors=3))
print('A',a_cfg,'B',b_cfg,'baseline',baseline)
''')
md('## 4. Основная серия варианта 3\n\nВызывается неизменённая L.variant_summary(3), включая прогрев. Обёртка сохраняет метрики и поизображенные MSE train/test для всех пяти seed; для seed 101 дополнительно сохраняются веса обеих моделей и первые восемь реконструкций float32. Это позволяет проверить таблицу и сравнительный лист. Модели на листе взяты из основной серии, не из нового обучения.')
code(r'''
records=[];models_101={}
def recorded_run(kind,cfg,seed):
    metrics,model=original_run(kind,cfg,seed)
    if seed in range(101,106):
        condition='A' if cfg==a_cfg else 'B'
        with torch.no_grad():
            pte=L.reconstruct(model,Xte,cfg['eval_noise']);ptr=L.reconstruct(model,Xtr[:1024],cfg['eval_noise'])
            mse_test=((pte-Xte)**2).flatten(1).mean(1).cpu().numpy()
            mse_train=((ptr-Xtr[:1024])**2).flatten(1).mean(1).cpu().numpy()
        name=f'{condition}_{seed}_errors.npz'
        np.savez_compressed(OUT/name,mse_test=mse_test,mse_train=mse_train)
        rec=dict(condition=condition,kind=kind,settings=dict(cfg),seed=seed,metrics=metrics,errors=name)
        records.append(rec)
        if seed==101:
            torch.save(model.state_dict(),OUT/f'{condition}_101_weights.pt')
            np.save(OUT/f'{condition}_101_predictions.npy',pte[:8].cpu().numpy())
            models_101[condition]=model
        print('DONE',condition,seed,metrics)
    return metrics,model
L.run=recorded_run
try:result=L.variant_summary(N)
finally:L.run=original_run
assert len(records)==10
write_json(OUT/'records.json',records);write_json(OUT/'summary.json',result)
for row in result['rows']:print(row)
''')
md('## 5. Таблица, допуски, эталон и диагностика\n\nPSNR выше — точнее, время и число параметров ниже — экономнее; малый gap означает меньший разрыв, но не сам по себе хорошую реконструкцию. Число параметров детерминировано, при s=0 статистический смысл 2s отсутствует. В базовой библиотеке отношение записывается Infinity. Практическую ресурсную классификацию параметров приводим отдельно от качества.')
code(r'''
TOLS={'psnr':1.,'gap':.1,'params':.2,'seconds':.2}
classified=[]
for metric,a,s,b,d,ratio,sig in result['rows']:
    tolerance=TOLS[metric] if metric in ['psnr','gap'] else TOLS[metric]*abs(a)
    practical=bool(abs(d)>tolerance)
    direction=d if metric=='psnr' else -d
    label='нейтрально' if not practical else 'улучшение' if direction>0 else 'ухудшение'
    classified.append(dict(metric=metric,A=a,s_A=s,B=b,delta=d,ratio=ratio,over_2s=sig,tolerance=tolerance,practical=practical,label=label,criteria_disagree=bool(sig)!=practical,deterministic=metric=='params'))
write_json(OUT/'classification.json',classified)
def table(rows):
    header='| Метрика | A | s_A | B | Δ | abs(Δ)/s | >2s | Допуск | Класс |\n|---|---:|---:|---:|---:|---:|---|---:|---|\n'
    return header+'\n'.join(f"| {r['metric']} | {r['A']:.6f} | {r['s_A']:.6f} | {r['B']:.6f} | {r['delta']:+.6f} | {r['ratio']:.3f} | {r['over_2s']} | {r['tolerance']:.6f} | {r['label']} |" for r in rows)
display(Markdown(table(classified)))
print('Baseline',baseline)
for r in classified:
    if r['metric']=='psnr':print('Gain above baseline: A',r['A']-baseline,'B',r['B']-baseline)
print('Disagreement',[r['metric'] for r in classified if r['criteria_disagree']])
diag_summary=[]
for d in [1,2,3,4,8]:
    values=[r['metrics']['psnr'] for r in diagnostic if r['settings']['d']==d]
    diag_summary.append(dict(d=d,mean=float(np.mean(values)),s=float(np.std(values,ddof=1)),values=values))
write_json(OUT/'diagnostic_summary.json',diag_summary)
print('Diagnostic',json.dumps(diag_summary,indent=2))
''')
md('## 6. Сравнительный лист\n\nПервые восемь test-сцен, seed обучения 101. Строки сверху вниз: оригиналы; ConvAE d=8; DenseAE d=8. Пиксели увеличены методом NEAREST без сглаживания, исходный размер 32×32. Численная оценка PSNR выполнена по float32 до округления в PNG.')
code(r'''
rows=[Xte[:8].cpu().numpy(),np.load(OUT/'A_101_predictions.npy'),np.load(OUT/'B_101_predictions.npy')]
grid=np.concatenate([np.concatenate(list(r.transpose(0,2,3,1)),axis=1) for r in rows],axis=0)
sheet=Image.fromarray((grid*255).round().astype('uint8')).resize((1024,384),Image.Resampling.NEAREST)
sheet.save(OUT/'comparison.png');display(sheet)
''')
md('''## 7. Анализ и ограничения

Визуальный анализ и заключение по фактическим результатам добавляются после выполнения и осмотра. Высокое абсолютное PSNR не объявляется достаточным: его сопоставляем с эталоном. Диагностика d относится к трём факторам синтетической сцены и конечной выборке; это эмпирическая проверка, а не доказательство строгой минимальной размерности для всех изображений.

Сравнение архитектур не выравнивает число параметров. Причина разницы может включать пространственную структуру, ёмкость и особенности оптимизации. Пять seed и один набор не позволяют обобщать на фотографии. Обучение на GPU не обещает побитовую повторяемость; новый сеанс отдельно не проверялся. Критерий 2s — эвристика, не p-value. Время зависит от GPU и прогрева. Исходники преподавателя сохранены, собственные результаты и их анализ получены отдельно.''')
md('## 8. Паспорт и архив\n\nДанные и модели созданы в этой работе с нуля. Внешние веса не используются. Источник алгоритма и синтетических сцен — предоставленные lab07_lib.py и lab07_demo.py; лицензионный файл к ним не приложен, свободное коммерческое использование не утверждается. [Документация PyTorch](https://docs.pytorch.org/docs/stable/nn.html), приложенная PDF-методичка. Все значения ниже фактические.')
code(r'''
import importlib.metadata as metadata
passport=dict(student='Власюк Данил Витальевич',group='Т26ИИКТ-МИК11',variant=N,started_utc=STARTED,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpu=GPU,python=sys.version,platform=platform.platform(),packages={name:metadata.version(name) for name in ['torch','numpy','Pillow']},kind=kind,data_seed=7,seeds=list(L.SEEDS),settings_A=a_cfg,settings_B=b_cfg,optimizer='Adam',lr=.002,batch=128,training_updates=640,dtype='float32',tolerances=TOLS,source_sha256=EXPECTED,cudnn_benchmark=torch.backends.cudnn.benchmark,cudnn_deterministic=torch.backends.cudnn.deterministic,deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),independent_new_session_tested=False)
write_json(OUT/'passport.json',passport)
(OUT/'environment.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
manifest={str(p.relative_to(OUT)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in OUT.rglob('*') if p.is_file()}
write_json(OUT/'run_manifest.json',manifest)
archive=shutil.make_archive('/content/LR07_variant3_results','zip',OUT)
print('COMPLETE; ARCHIVE',archive)
from google.colab import files
files.download(archive)
''')
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3'),colab=dict(name='LR07_3.ipynb'),accelerator='GPU'),cells=cells)
p=R/'notebooks/prepared';p.mkdir(exist_ok=True);(p/'LR07_3.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(cells),'cells')
