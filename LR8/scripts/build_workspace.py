from pathlib import Path
import json,base64,hashlib,uuid,datetime
R=Path(__file__).resolve().parents[1]
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()
hyp='''# Гипотеза и допуски до обучения ЛР8

Вариант 3, набор disc: янтарный диск на градиентном фоне, факторы x, y и радиус. A: VAE d=8; B: VAE d=2. Единственный изменяемый параметр - размер латентного вектора. beta=1, warmup=10 эпох, всего 30 эпох, Adam lr=0.002, batch=128, float32, линейная интерполяция, tau=1. Данные: 4096 train и 1024 test, data seed7. Seed обучения101–105. Вычисления на CPU в Engee, 4 потока (не более доступных), как в библиотеке.

Гипотеза: слишком узкое представление d=2 ухудшит реконструкцию более чем на 1 дБ и среднее линейное R2 факторов более чем на 0.05. Ожидаем, что информация о радиусе теряется сильнее, чем положение; это проверяется отдельно по R2_x, R2_y, R2_radius, а не только счётом факторов. Направление изменения интерполяции и близости сэмплов заранее не гарантируется. Меньшее d не обязательно ухудшает все метрики.

Допуски до запуска: реконструкция, интерполяция, сэмплы ±1.0 дБ; R2 ±0.05. Рост выше допуска - улучшение данного показателя, падение - ухудшение, внутри - нейтрально. |Δ|>2s_A считается отдельно как эвристика разброса seed, не p-value. Для варианта3 все четыре метрики могут меняться; неизменяемой контрольной метрики нет.

200 пар с seed11, t=0.25/0.5/0.75; истинный эталон - рендер взвешенных факторов. 256 сэмплов из N(0,I), seed1000+seed обучения; метрика сэмплов не оценивает разнообразие. Для диагностики активна ось с mean KL>0.05 нат. Сравним также AE beta=0 с VAE beta=1/8 и проверку схлопывания без warmup из полного демо. Три непрерывных фактора - ориентир; для конечного дискретного рендера универсальная теорема о минимальном d не утверждается.
'''
p=R/'data/hypothesis.md'
if not p.exists():p.write_text(hyp+'\nЗаписано: '+now+'\n')
pre=R/'reports/pre_run_record.json'
if not pre.exists():pre.write_text(json.dumps(dict(recorded_at=now,hypothesis_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
driver=R/'src/lr08_execute.py';s=driver.read_text()
if 'class Tee:' not in s:
 s=s.replace("ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)","""ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)
class Tee:
 def __init__(self,*streams):self.streams=streams
 def write(self,text):
  for out in self.streams:out.write(text);out.flush()
 def flush(self):
  for out in self.streams:out.flush()
LOG=open(ROOT/'run.log','w',buffering=1)
sys.stdout=Tee(sys.stdout,LOG);sys.stderr=Tee(sys.stderr,LOG)""")
 driver.write_text(s)
cells=[]
def add(k,s,name):
 meta=dict(name=name,engee=dict(isDisplay=True,isParagraph=k=='markdown',isClosedParagraph=False,amountHideCellsInside=0,codeOutputView='col',codeOutputHidden=False))
 c=dict(cell_type=k,id=uuid.uuid4().hex[:8],metadata=meta,source=s.strip().splitlines(keepends=True))
 if k=='code':c.update(execution_count=None,outputs=[])
 else:c['attachments']={}
 cells.append(c)
def md(s,n):add('markdown',s,n)
def code(s,n):add('code',s,n)
md('''# Лабораторная работа №8. Генерация и интерполяция в латентном пространстве

Власюк Данил Витальевич, Т26ИИКТ-МИК11. Вариант 3: VAE d=8 → d=2 на наборе «диск».

Цель: сравнить реконструкцию, интерполяцию, близость сэмплов и линейную связь латентного представления с факторами сцены. Работа выполняется в Engee на CPU по приложенной методичке. Скрипты lab07_lib.py, lab08_lib.py и lab08_demo.py сохранены без изменения. run_lr08.py - служебная проверка всех шести вариантов набора, в индивидуальном задании вместо неё вызывается V.variant_summary(3).

Данные синтетические, внешние веса и фотографии не используются. Подготовленная папка /user/AI_in_creative_media/LR08 содержит исходники, собственный исполняемый сценарий lr08_execute.py и гипотезу. Сначала выполните подготовку, затем полный эксперимент. Длительная ячейка обучает все модели и пишет живой журнал run.log. По окончании следующие ячейки покажут таблицы и изображения. Другие лабораторные не изменяются.''','Тема и порядок')
md(p.read_text(),'Гипотеза до запуска')
code('''using SHA, Dates, Images, FileIO
ROOT8="/user/AI_in_creative_media/LR08"
PY8="/user/.user_venvs/py3.11/bin/python3"
cd(ROOT8)
println("ENGEE LR08; Julia=",VERSION,"; started=",now())
run(`$PY8 -c "import sys,torch,numpy,PIL;print(sys.version,torch.__version__,torch.cuda.is_available(),numpy.__version__,PIL.__version__)"`)
for f in ["lab07_lib.py","lab08_lib.py","lab08_demo.py"]
 println(f," ",filesize(f)," SHA256=",bytes2hex(sha256(read(f))))
end
println(read("hypothesis.md",String))''','Среда и SHA256')
md('''## Выполнение демо и варианта 3

Собственный сценарий импортирует неизменённые учебные библиотеки, выполняет lab08_demo.py целиком и затем V.variant_summary(3). Модели d=8, beta=1 уже обучены в демо и повторно используются библиотечным кэшем; для d=2 обучаются новые модели. Все пять seed участвуют в обеих сериях. Дополнительный код сохраняет метрики, ошибки по изображениям, латентные векторы, KL по осям, веса seed101 и листы сравнения. Код обучения и метрик преподавателя не меняется.

Полные тексты алгоритмов доступны в приложенных .py. Вывод следующей ячейки - фактическое выполнение Python в Engee, а не импортированные числа преподавателя. Метрики и архив формируются только после завершения.''','Методика')
code('''println("LR08: Python CPU execution started ",now())
run(`$PY8 -u lr08_execute.py`)
println("LR08: Python execution finished ",now())''','Полный эксперимент Python')
code('''for f in ["summary.json","classification.json","diagnostic.json","ae_vae_controls.json","r2_per_factor.json","passport.json"]
 println("=== ",f," ===")
 println(read(joinpath(ROOT8,"artifacts",f),String))
end
println("ARCHIVE: ",joinpath(ROOT8,"LR08_variant3_results.zip"))''','Результаты и паспорт')
md('''## Листы сравнения

Основной лист: строки 1/2 - 8 сэмплов N(0,I) для A/B; строки 3/4 - линейный путь A/B между test-сценами 0 и2 (seed101). Дополнительно показан истинный путь по факторам, затем полный демонстрационный лист. Измерения выполняются до округления float32 в PNG. Близость к ближайшему test-изображению не доказывает разнообразия.''','Чтение изображений')
code('''display(load(joinpath(ROOT8,"artifacts","comparison.png")))
display(load(joinpath(ROOT8,"artifacts","interpolation_true_path.png")))
display(load(joinpath(ROOT8,"artifacts","comparison_demo_variant01.png")))''','Основной и демонстрационный листы')
md('''## Вывод по фактическим данным

Заключение, визуальная оценка и ответы на вопросы добавляются после осмотра собственных результатов. До выполнения нельзя объявлять гипотезу подтверждённой. Ограничения: один синтетический набор, пять seed, одна архитектура; ближайший сосед не оценивает разнообразие, линейное R2 не доказывает распутанности осей, CPU-обучение не обещает побитового совпадения. Источники - приложенная методичка и скрипты, документация PyTorch. Лицензионный файл учебных скриптов не приложен; неограниченное коммерческое использование не утверждается.''','Анализ после запуска')
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(display_name='IJulia 1.12.6',language='julia',name='ijulia-1.12'),language_info=dict(file_extension='.jl',name='julia',version='1.12.6'),engee={}),cells=cells)
prepared=R/'notebooks/prepared';prepared.mkdir(exist_ok=True);(prepared/'LR08_3.ngscript').write_text(json.dumps(nb,ensure_ascii=False,indent=2)+'\n')
payload={f.name:base64.b64encode(f.read_bytes()).decode() for f in (R/'src').glob('*.py')}
payload['hypothesis.md']=base64.b64encode(p.read_bytes()).decode();payload['LR08_3.ngscript']=base64.b64encode((prepared/'LR08_3.ngscript').read_bytes()).decode()
bootstrap='''from pathlib import Path
import base64,json
ROOT=Path('/user/AI_in_creative_media/LR08');ROOT.mkdir(parents=True,exist_ok=True)
FILES='''+repr(payload)+'''
for name,encoded in FILES.items():
 p=ROOT/name;b=base64.b64decode(encoded)
 if p.exists():
  if name.endswith('.ngscript'):continue
  if p.read_bytes()!=b:raise RuntimeError('Existing file differs: '+str(p))
 else:p.write_bytes(b)
print('LR08_WORKSPACE_READY',ROOT)
'''
u=R/'upload';u.mkdir(exist_ok=True);(u/'lr08_bootstrap.py').write_text(bootstrap)
print('Prepared notebook',len(cells),'cells; bootstrap',len(bootstrap),'bytes')
