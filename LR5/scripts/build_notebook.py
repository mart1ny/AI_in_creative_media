from pathlib import Path
import json,uuid,hashlib
R=Path(__file__).resolve().parents[1]
cells=[]
def add(kind,text):
 c={'cell_type':kind,'id':uuid.uuid4().hex[:8],'metadata':{},'source':text.strip().splitlines(keepends=True)}
 if kind=='code':c.update(execution_count=None,outputs=[])
 cells.append(c)
def md(t):add('markdown',t)
def code(t):add('code',t)
md('''# Лабораторная работа 5 Запуск открытой модели text-to-image

**Вариант 3 — бриф «афиша фестиваля робототехники», генератор CPU и CUDA при seed 1003.**

Власюк Данил Витальевич, группа Т26ИИКТ-МИК11.

Работа выполняется по приложенной методичке ЛР5 в Google Colab с NVIDIA GPU. Сначала выбрать Runtime → Change runtime type → T4 GPU, затем Run all. Сравнивается устройство **генератора начального шума**; вычисления модели в обоих условиях остаются на одном GPU. Выполняются оба предоставленных скрипта, индивидуальный вариант, повтор со свежим генератором, намеренная ошибка с общим генератором и контроль причины различий. Все численные результаты появляются только после выполнения.

Индивидуальный вклад: постановка гипотезы, протокол A/B, сохранение манифестов и начального шума, проверка повторяемости, независимый контроль, анализ и визуальная оценка. Исходная библиотека преподавателя сохранена без изменения.''')
md('''## 1 Документация и выбор среды

Изучена [документация WorkspaceArray](https://engee.com/helpcenter/stable/ru/guide/workspacearray.html). Этот тип предназначен для временных рядов и ленивого чтения; `wa[i]` получает запись, срез задаёт подмножество, `collect` загружает данные. Для генерации SD-Turbo используются тензоры PyTorch и изображения PIL.

В тексте учебной страницы упомянута Engee, но приложенные PDF и Python-скрипты ЛР5 требуют Colab с CUDA. В Engee проверено отсутствие `nvidia-smi` и `/dev/nvidia0`. По уточнению пользователя работа выполняется по приложениям. Контроль CUDA ниже не позволяет выдать CPU-only запуск за выполнение варианта 3.''')
md((R/'data/hypothesis.md').read_text())
md('''## 2 Среда и зависимости

Проверяем фактический GPU. Версии служебных библиотек закреплены; штатный CUDA PyTorch Colab не переустанавливается. GPU должен быть доступен до загрузки модели. Фиксируем UTC и московское время, Python, PyTorch, драйвер и GPU.''')
code(r'''
import os,sys,subprocess,time,json,hashlib,platform,pathlib,datetime
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
os.environ['HF_HUB_DISABLE_XET']='1'
import torch
STARTED_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()
print('START UTC',STARTED_UTC)
print('Python',sys.version,'torch',torch.__version__,'CUDA',torch.cuda.is_available())
assert torch.cuda.is_available(), 'Для варианта 3 выберите T4 GPU в Runtime → Change runtime type'
GPU_INFO=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv'],text=True)
print(GPU_INFO)
subprocess.run([sys.executable,'-m','pip','install','-q','diffusers==0.40.0','transformers==5.16.1','accelerate==1.15.0','safetensors==0.8.0','huggingface-hub==1.31.0'],check=True)
''')
md('''## 3 Предоставленные скрипты

Следующие две ячейки записывают исходные файлы из архива. Проверка SHA-256 подтверждает, что библиотека и демонстрационный скрипт не изменены. Демонстрационный скрипт затем выполняется целиком; основной эксперимент использует те же функции.''')
code('%%writefile lab05_lib.py\n'+(R/'src/lab05_lib.py').read_text())
code('%%writefile lab05_demo.py\n'+(R/'src/lab05_demo.py').read_text())
code(r'''
import numpy as np, PIL, diffusers, transformers, accelerate, safetensors, huggingface_hub
from PIL import Image
from IPython.display import display,Markdown
import lab05_lib as L
from diffusers.utils.torch_utils import randn_tensor
assert hashlib.sha256(pathlib.Path('lab05_lib.py').read_bytes()).hexdigest()=='4eb176506585ffcda1702605a767309fb451808229c3622f80ce882b7fa2ce1a'
assert hashlib.sha256(pathlib.Path('lab05_demo.py').read_bytes()).hexdigest()=='53b3b13f19e6754bda1cde58ef09f1e45b1595d1c4dab2a9b02bd4d99d731ce4'
OUT=pathlib.Path('artifacts');OUT.mkdir(exist_ok=True)
PACKAGES={n:__import__(n).__version__ for n in ['torch','diffusers','transformers','accelerate','safetensors','huggingface_hub','PIL','numpy']}
print(json.dumps(PACKAGES,indent=2))
torch.backends.cuda.matmul.allow_tf32=False
torch.backends.cudnn.allow_tf32=False
torch.backends.cudnn.benchmark=False
torch.backends.cudnn.deterministic=True
torch.use_deterministic_algorithms(True)
def write_json(path,value):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str),encoding='utf8')
def compare_images(a,b):
    aa,bb=np.asarray(a.convert('RGB'),dtype=np.float64),np.asarray(b.convert('RGB'),dtype=np.float64)
    mse=float(np.mean((aa-bb)**2));p=float('inf') if mse==0 else float(10*np.log10(255**2/mse))
    return dict(sha_a=L.sha(L.png_bytes(a)),sha_b=L.sha(L.png_bytes(b)),pixel_equal=bool(np.array_equal(aa,bb)),max_diff=int(np.max(np.abs(aa-bb))),mse=mse,psnr=p,verdict=L.classify(p))
def save_run(label,img,gen_device,seed=1003,extra=None):
    folder=OUT/label;folder.mkdir(exist_ok=True)
    data=L.png_bytes(img);(folder/'result.png').write_bytes(data)
    m=dict(model_id=L.MODEL_ID,revision=L.REVISION,prompt=L.BRIEFS[0],seed=seed,steps=1,guidance_scale=0.0,size=512,generator_device=gen_device,dtype=str(pipe.unet.dtype),device=torch.cuda.get_device_name(0),platform=platform.platform(),python=sys.version.split()[0],packages=PACKAGES,image_size=list(img.size),image_mode=img.mode,sha256=L.sha(data),timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scheduler=type(pipe.scheduler).__name__,label=label)
    if extra:m.update(extra)
    write_json(folder/'manifest.json',m);return m
def montage(a,b):
    canvas=Image.new('RGB',(1024,512));canvas.paste(a,(0,0));canvas.paste(b,(512,0));return canvas
print('SOURCE HASHES PASS')
''')
md('''## 4 Демонстрационный скрипт целиком

Скрипт загружает закреплённую ревизию SD-Turbo, выполняет прогрев, сохраняет изображение и манифест демо, проверяет повтор и намеренную ошибку. Его конвейер повторно используется дальше, чтобы условия A и B были получены в одной сессии. Совпадение с SHA-256 преподавателя между разными средами не предполагается.''')
code(r'''
import runpy
_demo=runpy.run_path('lab05_demo.py')
pipe=_demo['pipe']
print('DEMO EXECUTED; GPU',torch.cuda.get_device_name(0))
display(_demo['img'])
''')
md('''## 5 Индивидуальный вариант 3

A — свежий CPU-генератор; B — свежий CUDA-генератор. Seed одинаковый, 1003. Prompt, модель, ревизия, GPU вычислений, fp16, один шаг и guidance=0 совпадают. Сохраняем отдельные PNG и полные манифесты. Затем выполняем штатную `variant_summary(pipe,3)` и сопоставляем её результаты с нашей парой.''')
code(r'''
PROMPT=L.BRIEFS[0];SEED=1003
print('PROMPT',PROMPT)
a,b=L.make_pair(pipe,PROMPT,SEED,'generator_device')
manifest_a=save_run('A_cpu',a,'cpu');manifest_b=save_run('B_cuda',b,'cuda')
main_comparison=compare_images(a,b)
write_json(OUT/'comparison_main.json',main_comparison)
print(json.dumps(main_comparison,ensure_ascii=False,indent=2))
standard_summary=L.variant_summary(pipe,3)
assert standard_summary['sha_a']==main_comparison['sha_a']
assert standard_summary['sha_b']==main_comparison['sha_b']
write_json(OUT/'variant_summary.json',standard_summary)
print('STANDARD SUMMARY MATCHES SAVED A/B')
display(Markdown('**Слева A: генератор CPU. Справа B: генератор CUDA.**'))
comparison_montage=montage(a,b);comparison_montage.save(OUT/'comparison_cpu_cuda.png');display(comparison_montage)
''')
md('''## 6 Повтор и ошибка общего генератора

При корректном повторе каждый вызов получает новый генератор с тем же seed. Для воспроизведения ошибки создаём один CPU-генератор и передаём его дважды: после первого вызова его состояние уже изменилось. Проверяем это на своём брифе и seed, а не только в демо.''')
code(r'''
repeat=L.generate(pipe,PROMPT,SEED,gen_device='cpu')[0]
save_run('repeat_fresh_cpu',repeat,'cpu')
repeat_comparison=compare_images(a,repeat)
g=torch.Generator(device='cpu').manual_seed(SEED)
first=pipe(prompt=PROMPT,num_inference_steps=1,guidance_scale=0.0,height=512,width=512,generator=g).images[0]
second=pipe(prompt=PROMPT,num_inference_steps=1,guidance_scale=0.0,height=512,width=512,generator=g).images[0]
save_run('shared_generator_first',first,'cpu',extra={'generator_use':1})
save_run('shared_generator_second',second,'cpu',extra={'generator_use':2})
shared_comparison=compare_images(first,second)
assert np.array_equal(np.asarray(a),np.asarray(first))
assert repeat_comparison['pixel_equal']
write_json(OUT/'comparison_repeat.json',repeat_comparison)
write_json(OUT/'comparison_shared_generator.json',shared_comparison)
print('FRESH GENERATOR',json.dumps(repeat_comparison,indent=2))
print('SHARED GENERATOR',json.dumps(shared_comparison,indent=2))
display(Markdown('**Общий генератор: первый и второй вызовы.**'))
montage(first,second).save(OUT/'shared_generator_comparison.png');display(montage(first,second))
''')
md('''## 7 Где возникает различие

Проверяем начальные латентные тензоры тем же механизмом `randn_tensor`, который используется конвейером. CPU и CUDA при одном seed сравниваются до сети. Затем дважды передаём один и тот же готовый шум на GPU через `latents`: это контроль, отделяющий генератор от вычислений модели.''')
code(r'''
shape=(1,pipe.unet.config.in_channels,512//pipe.vae_scale_factor,512//pipe.vae_scale_factor)
cpu_lat=randn_tensor(shape,generator=torch.Generator(device='cpu').manual_seed(SEED),device=torch.device('cuda'),dtype=pipe.unet.dtype)
cuda_lat=randn_tensor(shape,generator=torch.Generator(device='cuda').manual_seed(SEED),device=torch.device('cuda'),dtype=pipe.unet.dtype)
np.save(OUT/'initial_noise_cpu.npy',cpu_lat.float().cpu().numpy())
np.save(OUT/'initial_noise_cuda.npy',cuda_lat.float().cpu().numpy())
noise_comparison=dict(shape=list(shape),dtype=str(pipe.unet.dtype),equal=bool(torch.equal(cpu_lat,cuda_lat)),max_diff=float(torch.max(torch.abs(cpu_lat.float()-cuda_lat.float())).item()),mse=float(torch.mean((cpu_lat.float()-cuda_lat.float())**2).item()))
print('INITIAL NOISE',noise_comparison)
def from_latents(lat):
    return pipe(prompt=PROMPT,num_inference_steps=1,guidance_scale=0.0,height=512,width=512,latents=lat.clone()).images[0]
fixed1=from_latents(cpu_lat);fixed2=from_latents(cpu_lat)
fixed_comparison=compare_images(fixed1,fixed2)
reconstructed=compare_images(a,fixed1)
save_run('fixed_noise_first',fixed1,'explicit_cpu_latents')
save_run('fixed_noise_second',fixed2,'explicit_cpu_latents')
write_json(OUT/'comparison_initial_noise.json',noise_comparison)
write_json(OUT/'comparison_fixed_noise.json',fixed_comparison)
write_json(OUT/'comparison_A_vs_explicit_noise.json',reconstructed)
print('SAME LATENTS REPEAT',json.dumps(fixed_comparison,indent=2))
print('A VS EXPLICIT NOISE',json.dumps(reconstructed,indent=2))
assert not noise_comparison['equal']
assert fixed_comparison['pixel_equal']
assert reconstructed['pixel_equal']
''')
md('''## 8 Вывод по фактическим данным

Критерий 40 дБ записан до запуска. Он условен: PSNR измеряет численное отличие, а не красоту или точность следования брифу. Побитовое совпадение PNG сильнее, чем практическое совпадение по допуску. Область вывода ограничена конкретной моделью, ревизией, GPU и версиями. Новый независимый сеанс здесь не проверяется и не объявляется воспроизведённым.''')
code(r'''
checks=dict(fresh_generator_repeat=repeat_comparison['pixel_equal'],initial_noise_differs=not noise_comparison['equal'],fixed_noise_repeat=fixed_comparison['pixel_equal'],explicit_noise_reproduces_A=reconstructed['pixel_equal'],standard_summary_matches=True)
verdict_ru={'identical':'идентичны','close':'практически совпадают','different':'различаются'}
conclusion=f"""# Вывод ЛР5 вариант 3

При одном seed 1003 изображения с генераторами CPU и CUDA {verdict_ru[main_comparison['verdict']]}. PSNR={main_comparison['psnr']:.4f} дБ, максимальная разница={main_comparison['max_diff']}, MSE={main_comparison['mse']:.6f}; пиксели совпадают: {main_comparison['pixel_equal']}.

Начальные тензоры CPU/CUDA совпадают: {noise_comparison['equal']}. Два вызова сети с одним явным тензором совпадают: {fixed_comparison['pixel_equal']}. Контроль воспроизводит A: {reconstructed['pixel_equal']}. Это согласуется с возникновением различий на этапе генерации шума при неизменных вычислениях модели.

Свежий CPU-генератор воспроизводит A: {repeat_comparison['pixel_equal']}. Два вызова с общим генератором совпадают: {shared_comparison['pixel_equal']}, PSNR={shared_comparison['psnr']:.4f} дБ. Исправление — новый генератор с тем же seed на каждый независимый запуск.

Гипотеза о PSNR ниже 40 дБ: {main_comparison['psnr']<40}. Визуальная оценка соответствия брифу выполняется отдельно после осмотра пары A/B. Воспроизводимость между другими видеокартами и версиями не доказана.
"""
(OUT/'conclusion.md').write_text(conclusion,encoding='utf8');display(Markdown(conclusion))
write_json(OUT/'checks.json',checks)
print('ALL NUMERICAL CHECKS PASS',all(checks.values()))
assert all(checks.values())
''')
md('''## 9 Контрольные вопросы

1. Модель — веса и архитектура; конвейер объединяет кодировщик текста, сеть шумоподавления, декодер и планировщик; приложение предоставляет интерфейс.
2. Имя без ревизии может указывать на изменившиеся файлы. Полный commit фиксирует снимок.
3. Seed задаёт начальное состояние конкретного генератора, но не фиксирует его алгоритм на другом устройстве, версии и все недетерминированные операции.
4. CPU-генератор облегчает воспроизводимость начального шума при разных устройствах вычислений; полной межплатформенной гарантии это не даёт.
5. Генератор хранит состояние и потребляет последовательность случайных чисел. Второй вызов продолжает последовательность. Фактическая проверка приведена выше.
6. Равный SHA-256 подтверждает равенство байтов с практически пренебрежимой вероятностью коллизии. Он не доказывает качество изображения или повторяемость в другой среде. Разные файлы могут содержать одинаковые пиксели.
7. PSNR=10log10(65025/65.025)=30 дБ.
8. Может измениться как точность вычислений, так и шум, генерируемый непосредственно в float16/float32. Контроль — сформировать один шум в float32 и приводить его к нужному dtype.
9. Используются открыто доступные веса, но условия лицензии не равны отсутствию ограничений. Учебный некоммерческий запуск документирован; ссылки на карточку и LICENSE закреплены ниже. Перед иным использованием нужны применимые условия.
10. Обновить GPU, драйвер, CUDA, PyTorch и зависимости, параметры детерминизма, время и манифесты; сравнение повторить и не переносить прежний вердикт автоматически.
''')
md('''## 10 Паспорт и комплект

Модель: [SD-Turbo](https://huggingface.co/stabilityai/sd-turbo/tree/b261bac6fd2cf515557d5d0707481eafa0485ec2). [Лицензия закреплённой ревизии](https://huggingface.co/stabilityai/sd-turbo/blob/b261bac6fd2cf515557d5d0707481eafa0485ec2/LICENSE.md). Веса предоставлены Stability AI; исходники преподавателя и собственный эксперимент разделены. Запрос синтетический, без реальных людей и логотипов.

Архив содержит PNG и manifest.json для всех условий, начальные тензоры, таблицы сравнения, паспорт и версии. Скачанный ноутбук дополнительно сохраняет код, пояснения и выводы. Файлы преподавательского демо из исходного ZIP не выдаются за наш эксперимент.''')
code(r'''
passport=dict(student='Власюк Данил Витальевич',group='Т26ИИКТ-МИК11',variant=3,started_utc=STARTED_UTC,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_id=L.MODEL_ID,revision=L.REVISION,prompt=PROMPT,seed=SEED,steps=1,guidance_scale=0.0,size=[512,512],dtype=str(pipe.unet.dtype),generator_devices=['cpu','cuda'],model_device=torch.cuda.get_device_name(0),gpu_info=GPU_INFO,platform=platform.platform(),python=sys.version,packages=PACKAGES,tolerance_db=40,deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),library_sha256=hashlib.sha256(pathlib.Path('lab05_lib.py').read_bytes()).hexdigest(),demo_sha256=hashlib.sha256(pathlib.Path('lab05_demo.py').read_bytes()).hexdigest(),main_result=main_comparison,checks=checks,independent_new_session_tested=False)
write_json(OUT/'passport.json',passport)
(OUT/'environment.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf8')
import shutil
shutil.copy2('lab05_lib.py',OUT/'lab05_lib.py');shutil.copy2('lab05_demo.py',OUT/'lab05_demo.py')
archive=shutil.make_archive('LR05_variant3_results','zip',OUT)
print('COMPLETE; ARCHIVE',archive)
from google.colab import files
files.download(archive)
''')
nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','name':'python3','language':'python'},'colab':{'name':'LR05_3.ipynb'},'accelerator':'GPU'},'cells':cells}
(R/'notebooks/prepared').mkdir(exist_ok=True)
(R/'notebooks/prepared/LR05_3.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(cells),'cells; no fabricated execution outputs')
