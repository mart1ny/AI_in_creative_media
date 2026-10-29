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
p=read('passport.json');cl=read('classification.json');diag=read('diagnostic.json');controls=read('ae_vae_controls.json');collapse=read('collapse_records.json');demo=read('demo_summary.json')
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
def P(t,style='BodyRU'):return Paragraph(html.escape(str(t).replace('–','-').replace('—','-').replace('−','-').replace('‑','-')).replace('\n','<br/>'),styles[style])
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
flow.append(Spacer(1,65));para('Лабораторная работа №8','TitleRU');para('Генерация и интерполяция\nв латентном пространстве','TitleRU');para('Вариант 3: VAE d=8 → d=2','H2RU');flow.append(Spacer(1,25))
para('Власюк Данил Витальевич\nГруппа Т26ИИКТ-МИК11\nДисциплина «Искусственный интеллект в креативных технологиях»')
para('Фактическое выполнение: 29 октября 2026 года, Engee 26.10.2-H2, Python на CPU. Дата/время Python: '+p['started_utc'])
para('Цель: обучить VAE на синтетических сценах, получить сэмплы и промежуточные изображения, оценить влияние размера латентного вектора на четыре показателя и объяснить диагностику активных осей.')
para('Основной эксперимент выполнен в Engee, как требует приложенная методичка. Подготовлен отдельный ноутбук LR08_3.ngscript; Julia вызывает Python 3.11. Установлен CPU PyTorch 2.4.1. Внешние веса, фотографии и персональные данные не используются.')
page();heading('1. Гипотеза и протокол до запуска')
para((R/'data/hypothesis.md').read_text().replace('# Гипотеза и допуски до обучения ЛР8','').strip())
para('Гипотеза и SHA-256 записаны в data/hypothesis.md и reports/pre_run_record.json до обучения. Основная таблица получена неизменённой функцией V.variant_summary(3).','SmallRU')
page();heading('2. VAE, данные и воспроизводимость')
table([['Параметр','Фактическое значение'],['Среда','Engee 26.10.2-H2; Julia 1.12.6; Python '+p['python'].splitlines()[0]],['Версии',f"PyTorch {p['torch']}; NumPy {p['numpy']}; CPU; threads={p['threads']}; CUDA={p['cuda']}"],['Набор','disc: 4096 train, 1024 test; RGB 32×32; data seed7; x/y/радиус'],['A / B',str(p['settings_A'])+'\n'+str(p['settings_B'])],['Обучение','30 эпох, 960 обновлений; Adam lr=0.002; batch128; warmup10; seed101–105'],['Оценка','200 пар (seed11), t=0.25/0.5/0.75; 256 сэмплов N(0,I); seed1000+seed обучения']],[100,423])
para('Кодировщик свёрточной сети выдаёт μ и log σ². При обучении z=μ+exp(0,5 log σ²)·ε, ε~N(0,I). Декодер восстанавливает RGB. Потери на изображение: сумма квадратов ошибок по пикселям + β·KL(q(z|x)||N(0,I)). Это сумма, а не средняя MSE по 3072 пикселям; изменение нормировки меняло бы относительный вес β.')
para('KL одной оси: −0,5·(1+log σ²−μ²−σ²). Разогрев линейно увеличивает вес KL до β за первые 10 эпох. Для оценки реконструкции используется μ, без случайного шума; при β=0 обучение также декодирует μ и соответствует обычному AE в этой библиотеке.')
para('Сначала полностью выполнен lab08_demo.py: β=1/8, диагностика AE/VAE и схлопывания без warmup. Затем выполнен вариант3; кэш повторно использует уже обученные d=8, β=1. Собственный код лишь сохраняет метрики, ошибки и латентные массивы; учебные исходники не изменены. run_lr08.py - служебный пакетный прогон всех шести вариантов, он не требуется для индивидуального варианта3.','SmallRU')
page();heading('3. Четыре метрики и практический эффект')
para('Средние и выборочный s_A (ddof=1) по seed101–105. Реконструкция - среднее PSNR по 1024 test-сценам. Интерполяция - среднее по 200 парам и трём t относительно рендера взвешенных факторов. Сэмплы - PSNR ближайшей test-сцены для 256 генераций. R² - среднее по трём факторам, линейная регрессия обучена на train, проверена на test.')
rowtable(cl)
table([['Метрика','Допуск','Класс','2s и допуск расходятся']]+[[r['metric'],fmt(r['tolerance']),r['label'],'да' if r['criteria_disagree'] else 'нет'] for r in cl],[100,110,155,158])
para('Рост PSNR сэмплов показывает близость к test-сценам, но не разнообразие. Высокий R² не доказывает независимости или интерпретируемости отдельных осей. Критерий 2s - учебная эвристика относительно разброса seed, не p-value и не формальное доказательство статистической значимости.','SmallRU')
page();heading('4. Сэмплы и интерполяция')
para('Seed101. Строки сверху вниз: 8 сэмплов A из N(0,I); 8 сэмплов B; линейный путь A; линейный путь B между test-сценами 0 и2. d различается, поэтому одинаковый seed задаёт генераторы, но не одинаковую форму начального тензора. Лист содержит t=0,1/7,…,1; метрика интерполяции измерена отдельно в t=0,25/0,5/0,75. Изображения 32×32 увеличены NEAREST.')
flow.append(Image(str(A/'comparison.png'),width=523,height=261.5));flow.append(Spacer(1,10))
para('Истинный путь: рендер взвешенных факторов x/y/радиус той же пары.','SmallRU');flow.append(Image(str(A/'interpolation_true_path.png'),width=523,height=65.375));flow.append(Spacer(1,10))
for block in visual.split('\n\n'):
 if not block.startswith('#'):para(block)
page();heading('5. Активные оси и факторы сцены')
table([['Режим','seed','d','Активные оси','std μ по осям']]+[[r['condition'],str(r['seed']),str(r['d']),str(r['active']),'; '.join(f'{v:.3f}' for v in r['mu_std'])] for r in diag],[45,45,35,95,303])
para('Активная ось: средний KL по test >0,05 нат; это заданная операционная диагностика. Полные KL по осям сохранены в diagnostic.json. Разброс μ - отдельная характеристика и не заменяет KL.')
per=read('r2_per_factor.json');table_data=[['Режим','Средний R²_x','Средний R²_y','Средний R²_radius']]
for cond in ['A','B']:
 rr=[x for x in per if x['condition']==cond]
 table_data.append([cond]+[f"{sum(x[key] for x in rr)/len(rr):.5f}" for key in ['r2_x','r2_y','r2_radius']])
table(table_data,[75,140,140,168])
para((R/'reports/diagnostic_analysis.md').read_text().replace('# Анализ диагностики','').strip())
page();heading('6. Демо: AE, VAE и схлопывание')
para('Все значения ниже получены своим полным запуском lab08_demo.py в Engee, не взяты из архивных таблиц преподавателя. Диагностика на том же наборе disc, seed101.')
table([['β','Активные оси','Recon','Interp','Samples','R²']]+[[str(r['beta']),str(r['active']) if r['active'] is not None else 'не применяется',fmt(r['metrics']['recon']),fmt(r['metrics']['interp']),fmt(r['metrics']['sample']),fmt(r['metrics']['r2'])] for r in controls],[35,100,97,97,97,97])
para('AE без KL не обучает согласование агрегированного латентного распределения с N(0,I); брать из него сэмплы по этому prior без проверки необоснованно. β>0 не гарантирует улучшения всех метрик - регуляризация имеет цену.')
para('Без разогрева и с warmup10: реконструкция по пяти seed','H2RU')
data=[['Режим','101','102','103','104','105']]
for name,rr in [('без warmup',collapse[:5]),('warmup10',collapse[5:])]:data.append([name]+[f"{x['metrics']['recon']:.3f}" for x in rr])
table(data,[123,80,80,80,80,80])
para((R/'reports/collapse_analysis.md').read_text().replace('# Анализ схлопывания','').strip())
para('Демо β=1 →8: собственная сводка','H2RU');rowtable([dict(metric=r[0],A=r[1],s_A=r[2],B=r[3],delta=r[4],ratio=r[5],over_2s=r[6]) for r in demo['rows']])
page();heading('7. Вывод и ограничения')
for block in (R/'reports/final_conclusion.md').read_text().split('\n\n'):
 if not block.startswith('#'):para(block)
para('Чувствительность к удвоению допуска','H2RU')
for r in cl:
 tol=2*r['tolerance'];label='нейтрально' if abs(r['delta'])<=tol else 'улучшение' if r['delta']>0 else 'ухудшение'
 para(f"{r['metric']}: при допуске {tol:.3f} класс «{label}». Критерий 2s не изменяется.")
para('Допуски основного вывода остаются исходными; удвоение - только анализ чувствительности, не подгонка результата.','SmallRU')
page();heading('8. Код и контрольные вопросы')
para('Ключевой код Python. Полные исходники приложены, а фактическое выполнение и вывод сохранены в ноутбуке Engee.')
flow.append(Preformatted('N = 3\na_cfg, b_cfg = V.settings(V.FACTORS[(N-1) % 6])\nresult = V.variant_summary(N)\n# Training: SSE over pixels + beta * KL\nz = mu + torch.exp(0.5 * logvar) * epsilon\n# Evaluation: deterministic reconstruction from mu\nreconstruction = model.decode(model.encode(Xte))',styles['MonoRU']));flow.append(Spacer(1,12))
for block in answers.split('\n\n'):
 if not block.startswith('#'):para(block)
page();heading('9. Паспорт, комплект и источники')
para('Комплект: выполненный LR08_3.ngscript и копия Jupyter; этот PDF; основной, истинный и демонстрационный листы; журнал и снимок вывода Engee; исходные библиотеки; метрики, ошибки, латентные векторы, KL и регрессионные массивы; синтетические данные и факторы; веса seed101; паспорт и SHA-256; независимый проверяющий скрипт.')
para('Независимая проверка пересчитывает четыре метрики, регрессию факторов, KL и активность, средние, s и допуски. Пиксельные ошибки и ближайшие соседи отдельно проверяются для первых восьми примеров seed101; вся серия проверяется по сохранённым ошибкам. Локальное повторное обучение и новый Engee-сеанс отдельно не выполнялись.')
para('Индивидуальный вклад: гипотеза и допуски, подготовка среды Engee CPU, сохранение всех seed и диагностики, проверка R² по каждому фактору, независимый пересчёт, визуальный анализ и отчёт. Учебные исходники сохранены без изменения. Их лицензионный файл не приложен; неограниченное коммерческое использование не утверждается.')
para('Источники','H2RU')
for source in ['Приложенные методические указания ЛР8, 29 страниц; lab08_lib.py, lab08_demo.py, run_lr08.py; lab07_lib.py из ЛР7. Две копии lab08_lib в ZIP побитово одинаковы.','Kingma, Welling. Auto-Encoding Variational Bayes: https://arxiv.org/abs/1312.6114','Burgess et al. Understanding disentangling in beta-VAE: https://arxiv.org/abs/1804.03599','Документация PyTorch: https://docs.pytorch.org/docs/stable/nn.html']:
 para(source,'SmallRU')
para('Синтетические сцены и веса получены с нуля в этой работе. Персональные данные, фотографии и внешние предобученные модели не использованы.','SmallRU')
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#d5dfe6'));c.line(36,35,559,35);c.setFont('Arial',8);c.setFillColor(colors.HexColor('#567080'));c.drawString(36,23,'ЛР8 · Вариант 3 · Власюк Д. В.');c.drawRightString(559,23,str(doc.page))
path=O/'ЛР08_Вариант_3_Отчёт.pdf'
SimpleDocTemplate(str(path),pagesize=(595.28,841.89),leftMargin=36,rightMargin=36,topMargin=40,bottomMargin=50,title='ЛР8. Вариант 3',author=p['student']).build(flow,onFirstPage=footer,onLaterPages=footer)
print(path)
