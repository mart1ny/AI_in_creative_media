"""Create a Russian PDF report using actual measurements only."""
from pathlib import Path
import json,html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,Preformatted,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1];A=R/'artifacts';O=R/'output/pdf';O.mkdir(parents=True,exist_ok=True)
def read(f):return json.loads((A/f).read_text())
p=read('passport.json');cl=read('classification.json');baseline=read('baseline.json')['psnr'];diag=read('diagnostic_summary.json');demo=read('demo_summary.json')
visual=(R/'reports/visual_review.md').read_text()
answers=(R/'reports/control_answers.md').read_text()
fontroot=Path('/System/Library/Fonts/Supplemental')
for name,file in [('Arial','Arial.ttf'),('ArialBold','Arial Bold.ttf'),('Mono','Courier New.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fontroot/file)))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold',italic='Arial',boldItalic='ArialBold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyRU',fontName='Arial',fontSize=10.5,leading=15,spaceAfter=8))
styles.add(ParagraphStyle(name='H1RU',fontName='ArialBold',fontSize=17,leading=22,spaceAfter=15,textColor=colors.HexColor('#12334f')))
styles.add(ParagraphStyle(name='H2RU',fontName='ArialBold',fontSize=12,leading=17,spaceBefore=10,spaceAfter=9,textColor=colors.HexColor('#12334f')))
styles.add(ParagraphStyle(name='SmallRU',fontName='Arial',fontSize=8.2,leading=11,spaceAfter=6))
styles.add(ParagraphStyle(name='TitleRU',fontName='ArialBold',fontSize=23,leading=30,alignment=TA_CENTER,spaceAfter=25,textColor=colors.HexColor('#12334f')))
styles.add(ParagraphStyle(name='MonoRU',fontName='Mono',fontSize=7,leading=10))
flow=[]
def P(t,style='BodyRU'):return Paragraph(html.escape(str(t)).replace('\n','<br/>'),styles[style])
def para(t,style='BodyRU'):flow.append(P(t,style))
def heading(t):para(t,'H1RU')
def table(data,widths):
 data=[[P(v,'SmallRU') for v in row] for row in data]
 tb=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#7895ab')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d5dfe6')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
 flow.append(tb);flow.append(Spacer(1,12))
def page():flow.append(PageBreak())
def fmt(x):return f'{x:.5f}'
def rowtable(rows):
 data=[['Метрика','A','s_A','B','Δ','|Δ|/s','>2s']]
 for r in rows:data.append([r['metric'],fmt(r['A']),fmt(r['s_A']),fmt(r['B']),f"{r['delta']:+.5f}",f"{r['ratio']:.2f}",'да' if r['over_2s'] else 'нет'])
 table(data,[70,65,65,65,65,50,43])
flow.append(Spacer(1,65));para('Лабораторная работа №7','TitleRU');para('Построение\nавтокодировщика','TitleRU');para('Вариант 3: свёрточная и полносвязная архитектуры','H2RU');flow.append(Spacer(1,25))
para('Власюк Данил Витальевич\nГруппа Т26ИИКТ-МИК11\nДисциплина «Искусственный интеллект в креативных технологиях»')
para('Фактическое выполнение: 29 октября 2026 года, Google Colab, '+p['gpu'].splitlines()[-1])
para('Цель: обучить автокодировщик на синтетических сценах, проверить реконструкцию на отложенных данных и измерить влияние архитектуры по пяти seed с учётом эталона, разброса и ресурсной цены.')
para('Работа выполнена по приложенным методическим указаниям ЛР7: отдельный ноутбук Colab, ускоритель T4, библиотека lab07_lib.py. В карточке задания упомянута Engee, но исходники и PDF требуют PyTorch/CUDA в Colab. Внешние данные и предобученные веса не используются.')
page();heading('1. Протокол до обучения')
para((R/'data/hypothesis.md').read_text().replace('# Гипотеза и допуски до обучения','').strip())
para('Первый запуск: '+p['started_utc']+' UTC. Дата и контрольная сумма гипотезы сохранены в reports/pre_run_record.json.','SmallRU')
page();heading('2. Данные, сети и ход работы')
table([['Параметр','Фактическое значение'],['Среда',p['gpu'].strip()+'\nPython '+p['python'].splitlines()[0]],['Версии','; '.join(f'{k}={v}' for k,v in p['packages'].items())],['Данные','disc, RGB 32×32; 4096 train и 1024 test; data seed=7; факторы: x, y, радиус'],['Обучение','seed 101–105; 20 эпох; Adam lr=0.002; batch=128; 640 обновлений; MSE; float32; чистые входы'],['A: ConvAE','3 свёртки 3→16→32→64 с шагом 2; 32→16→8→4; линейный слой 1024→8; декодер 8→1024 и ConvTranspose2d'],['B: DenseAE','Flatten 3072→256→8→256→3072; ReLU и Sigmoid'],['Параметры','A: 101 035; B: 1 580 552. Это архитектурное сравнение с разной ёмкостью.']],[105,418])
para('Данные генерируются render(): янтарный диск на фиксированном градиентном фоне, центр и радиус меняются. Кодировщик E получает RGB и выдаёт z из восьми чисел; декодер D восстанавливает RGB. Размер входа 3072 числа, отношение 3072/8=384. Sigmoid ограничивает выход в 0…1. Сжатие по числу координат не равно степени сжатия файла.','BodyRU')
para('Порядок: сохранены исходники и их SHA-256; демо выполнено целиком; посчитан эталон по train; L.variant_summary(3) выполнена на пяти seed; сохранены метрики, ошибки по изображениям, веса seed101 и сравнительный лист; проведена диагностика d и независимая проверка. Основной лист использует модели из основной серии без повторного обучения.')
para('Задание 1: изучена документация WorkspaceArray Engee. Временные ряды читаются лениво; time/value дают метки/значения, срез хранит ссылку на источник, collect материализует данные в DataFrame. В текущем коде используются тензоры PyTorch.','SmallRU')
page();heading('3. Основная серия: качество и ресурсы')
para('Средние по seed 101–105. s_A - выборочное стандартное отклонение A, ddof=1. PSNR на test: среднее 10log10(1/MSE_i) по 1024 изображениям; gap = PSNR_train − PSNR_test, для train берутся первые 1024 сцены. Параметры в тысячах, время в секундах.')
rowtable(cl)
para('Классификация по заранее заданным допускам','H2RU')
table([['Метрика','Допуск','Класс','2s и допуск расходятся']]+[[r['metric'],fmt(r['tolerance']),r['label'],'да' if r['criteria_disagree'] else 'нет'] for r in cl],[100,110,155,158])
ps=next(r for r in cl if r['metric']=='psnr')
para(f'Эталон «средняя картинка»: {baseline:.4f} дБ на test. Выигрыш A относительно эталона: {ps["A"]-baseline:.4f} дБ; B: {ps["B"]-baseline:.4f} дБ. Средняя картинка строится только по train и не зависит от конкретного входа.')
para('При s_A=0 у числа параметров отношение |Δ|/s записано как inf. Это детерминированное различие числа весов, а не значимость по случайной выборке. Практический класс для параметров означает расход ресурсов, для gap - направление разрыва, не оценку эстетики. Критерий 2s является учебной эвристикой, не p-value.','SmallRU')
page();heading('4. Сравнительный лист и наблюдения')
para('Seed обучения 101; первые восемь тестовых сцен. Строки сверху вниз: оригинал; A - ConvAE, d=8; B - DenseAE, d=8. Сцены 32×32 увеличены NEAREST. PSNR рассчитан до округления RGB в PNG.')
flow.append(Image(str(A/'comparison.png'),width=523,height=196.125));flow.append(Spacer(1,15))
for block in visual.split('\n\n'):
 if not block.startswith('#'):para(block)
para('Изображения - синтетические диски; результаты не переносятся на фотографии без проверки. По одной сравнительной строке нельзя оценивать всю вариативность обучения; численная таблица использует все пять seed.','SmallRU')
page();heading('5. Диагностика и воспроизведение демо')
para('Воспроизведена типичная ошибка интерпретации: «PSNR выше двадцати - значит узкого места достаточно». Исправление - сравнение с тривиальным эталоном и развёртка d. Демо и вариант 3 используют один набор disc, поэтому ниже приводятся фактические диагностические обучения ConvAE из полного демо (seed 101–103), не архивные числа преподавателя.')
table([['d','Средний PSNR test','s по трём seed','PSNR каждого seed']]+[[str(r['d']),f"{r['mean']:.4f}",f"{r['s']:.4f}",'; '.join(f'{v:.3f}' for v in r['values'])] for r in diag],[45,135,100,243])
para((R/'reports/diagnostic_analysis.md').read_text().replace('# Анализ диагностики','').strip())
para('Демо: собственные результаты против образца методички','H2RU')
ref={'psnr':(26.00,23.20),'gap':(.040,.101),'params':(101.0,88.7),'seconds':(2.27,2.10)}
table([['Метрика','Наше A/B, d=8/2','Образец A/B']]+[[r[0],f'{r[1]:.4f} / {r[3]:.4f}',f'{ref[r[0]][0]:.3f} / {ref[r[0]][1]:.3f}'] for r in demo['rows']],[100,223,200])
para('Образец относится к запуску преподавателя 19.09.2026; наши числа получены заново. У обучения на GPU последние цифры и время могут различаться. Образец нужен для сопоставления картины, а не как эталон побитового совпадения.','SmallRU')
page();heading('6. Вывод, причины и границы')
for block in (R/'reports/final_conclusion.md').read_text().split('\n\n'):
 if not block.startswith('#'):para(block)
para('Чувствительность к удвоению допуска','H2RU')
for r in cl:
 tol=2*r['tolerance'];direction=r['delta'] if r['metric']=='psnr' else -r['delta']
 label='нейтрально' if abs(r['delta'])<=tol else 'улучшение' if direction>0 else 'ухудшение'
 para(f"{r['metric']}: при допуске {tol:.5f} класс «{label}». Критерий 2s от практического допуска не зависит.")
para('Допуски не меняются после результата; удвоение показано только как анализ чувствительности. В полном комплекте сохраняются исходные измерения и исходные пороги.','SmallRU')
page();heading('7. Код и контрольные вопросы')
para('Полный исполняемый код и фактический вывод содержатся в LR07_3.ipynb. Ключевая схема сравнения:')
flow.append(Preformatted('N = 3\nc, k = (N - 1) // 6, (N - 1) % 6\na_cfg, b_cfg = L.settings(L.FACTORS[k])\nresult = L.variant_summary(N)\n# Both modes: d=8, Adam, 20 epochs, same seeds\n# Evaluate held-out data; mean PSNR over images\nbaseline = L.psnr_images(Xtr.mean(0, keepdim=True)\n                        .expand_as(Xte), Xte)',styles['MonoRU']));flow.append(Spacer(1,12))
for block in answers.split('\n\n'):
 if not block.startswith('#'):para(block)
page();heading('8. Паспорт, комплект и источники')
para('Комплект: выполненный ноутбук; этот PDF; основной и демонстрационный сравнительные листы; фактическая серия пяти seed, ошибки по изображениям и сводные таблицы; синтетические train/test-данные и факторы; средняя картинка; веса A/B для seed101; диагностика d; паспорт и версии; независимый проверяющий скрипт; манифесты SHA-256.')
para('Независимая локальная проверка пересчитывает эталон, средние, s, разности, допуски и PSNR из поизображенных ошибок. Первые восемь реконструкций seed101 проверяются по float32-пикселям; лист сравнения восстанавливается точно. Обучение на локальном GPU не повторяется; новый Colab-сеанс отдельно не проверен.')
para('Индивидуальный вклад: гипотеза и допуски до запуска; сохранение результатов основной серии, весов и ошибок; сравнение с эталоном, анализ диагностики и чувствительности; визуальная оценка, независимый пересчёт, оформление ноутбука и отчёта. Предоставленный исходный код остаётся без изменений.')
para('Источники и права','H2RU')
for t in ['Приложенные методические указания «ЛР07_Построение_автокодировщика», 22 страницы, и скрипты lab07_lib.py / lab07_demo.py. Копии lab07_lib.py и lab07_lib(1).py в исходном ZIP побитово совпадают.', 'Документация Engee: https://engee.com/helpcenter/stable/ru/guide/workspacearray.html','PyTorch, модули нейросетей: https://docs.pytorch.org/docs/stable/nn.html','Сцены и веса в этой работе созданы с нуля. Фотографии, персональные данные и предобученные веса не применяются. Лицензионный файл к учебным исходникам не приложен; неограниченное коммерческое использование не утверждается.']:
 para(t,'SmallRU')
if (R/'reports/colab_url.txt').exists():para('Выполненный ноутбук: '+(R/'reports/colab_url.txt').read_text().strip(),'SmallRU')
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#d5dfe6'));c.line(36,35,559,35);c.setFont('Arial',8);c.setFillColor(colors.HexColor('#567080'));c.drawString(36,23,'ЛР7 · Вариант 3 · Власюк Д. В.');c.drawRightString(559,23,str(doc.page))
path=O/'ЛР07_Вариант_3_Отчёт.pdf'
SimpleDocTemplate(str(path),pagesize=(595.28,841.89),leftMargin=36,rightMargin=36,topMargin=40,bottomMargin=50,title='ЛР7. Вариант 3',author=p['student']).build(flow,onFirstPage=footer,onLaterPages=footer)
print(path)
