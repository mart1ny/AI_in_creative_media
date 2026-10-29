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
p=read('passport.json');cl=read('classification.json');normal=read('normalized_512.json')['classification'];g=read('guidance_check.json')
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
flow.append(Spacer(1,65));para('Лабораторная работа №6','TitleRU');para('Исследование параметров\ntext-to-image генерации','TitleRU');para('Вариант 3: размер 512×512 → 768×768','H2RU');flow.append(Spacer(1,25))
para('Власюк Данил Витальевич\nГруппа Т26ИИКТ-МИК11\nДисциплина «Искусственный интеллект в креативных технологиях»')
para('Фактическое выполнение: 28 октября 2026 года, Google Colab, '+p['gpu'].splitlines()[-1])
para('Цель: оценить влияние одного параметра на сходство с брифом, пространственные характеристики и время генерации на серии из пяти seed.')
para('Работа выполнена по приложенным методическим указаниям ЛР6, которые требуют Colab с T4. Упоминание Engee в тексте учебной страницы не соответствует программной среде приложенных Python-скриптов. Ноутбук ЛР6 хранится отдельно от ЛР5.')
page();heading('1. Протокол и гипотеза до запуска')
para((R/'data/hypothesis.md').read_text().replace('# Гипотеза и практические допуски до запуска','').strip())
para('Запуск: '+p['started_utc']+' UTC. Контрольная сумма гипотезы сохранена в reports/pre_run_record.json и проверена независимо.','SmallRU')
page();heading('2. Среда, данные и ход работы')
table([['Параметр','Фактическое значение'],['Модель',p['model_id']+'\n'+p['revision']],['Метрика CLIP',p['clip_id']+'\n'+p['clip_revision']],['Python',p['python'].splitlines()[0]],['GPU',p['gpu'].strip()],['Пакеты','; '.join(f'{k}={v}' for k,v in p['packages'].items())],['Параметры','fp16; steps=1; guidance=0; CPU generator; seed 101–105; A=512; B=768']],[105,418])
para('Текст запроса (одинаков для A, B и оценки CLIP):','H2RU');para(p['settings_A']['prompt'])
para('Последовательность: сохранены исходные файлы и SHA-256; полностью выполнены lab05_demo.py и lab06_demo.py; M.variant_summary(pipe, clip, 3) выполнена с сохранением всех десяти изображений; сформирован comparison.png для seed 101; рассчитаны допуски и контроль масштаба; отдельно проверены guidance 0, 1 и 3. Время модели исключает загрузку весов и CLIP-оценку, включает фактический вызов генерации; перед серией выполнен прогрев A и B.')
para('Задание 1: изучена документация WorkspaceArray Engee. Этот AbstractArray представляет временные ряды с ленивой загрузкой. Поля time и value предоставляют временные метки и значения; collect материализует данные. Для SD-Turbo здесь используются тензоры PyTorch и PIL.','SmallRU')
page();heading('3. Результаты пяти seed')
para('Основная таблица получена штатной функцией преподавателя. s_A - выборочное стандартное отклонение A (ddof=1). Δ = mean(B) - mean(A). CLIP = 100×cos(image,text), не CLIPScore. Время приведено в секундах.')
rowtable(cl)
para('Практическая классификация','H2RU')
table([['Метрика','Допуск','Отклик','2s и допуск расходятся']]+[[r['metric'],fmt(r['tolerance']),r['label'],'да' if r['criteria_disagree'] else 'нет'] for r in cl],[105,110,150,158])
for r in cl:
 rel=100*r['delta']/r['A']
 para(f"{r['metric']}: изменение {r['delta']:+.6f} ({rel:+.1f}% относительно A); {r['label']}. Эффект {'выходит' if r['over_2s'] else 'не выходит'} за 2s_A.")
para('Классы границ и контраста обозначают направление показателя, а не доказанное улучшение дизайна. Критерий 2s не имеет здесь интерпретации p-value. Разброс времени характеризует этот запуск.','SmallRU')
page();heading('4. Сравнительный лист и осмотр')
para('Seed 101. A (512×512) слева; B (768×768) справа. Для листа обе картинки приведены к 384×384; исходные PNG сохранены в полном размере.')
flow.append(Image(str(A/'comparison.png'),width=523,height=261.5));flow.append(Spacer(1,12))
for block in visual.split('\n\n'):
 if block.startswith('#'):continue
 para(block)
page();heading('5. Масштаб, ошибка и границы вывода')
para('Контроль при одинаковом масштабе 512×512 (LANCZOS)','H2RU');rowtable(normal)
para('Контроль отделяет часть влияния масштаба при измерении градиента. Он не превращает две разные композиции в один и тот же объект и не доказывает причину всех отличий. Размер меняет также форму начального шума при одном seed.')
para('Намеренная ошибка: guidance=1 включает CFG','H2RU')
para('Фактически SHA-256 для guidance 0 и 1 '+('совпали' if g['equal_0_1'] else 'различны')+'. CFG после 0/1/3: '+str([r['cfg_active'] for r in g['records']])+f". PSNR 0 против 3: {g['psnr_0_3']:.5f} дБ.")
para('Исправление объяснения: в данном конвейере CFG активируется при guidance>1. SD-Turbo рекомендована с guidance=0. Значение 3 применено как проверка вне рекомендованного режима, а не как универсальное улучшение.')
para('Вывод и ограничения','H2RU');para((R/'reports/final_conclusion.md').read_text().replace('# Итоговый вывод','').strip())
page();heading('6. Код и контрольные вопросы')
para('Ключевой фрагмент эксперимента. Полный код и фактические выводы - в LR06_3.ipynb; исходные библиотеки сохранены без изменений.')
flow.append(Preformatted('N = 3\nc, k = (N - 1) // 6, (N - 1) % 6\na_cfg, b_cfg = M.settings(M.FACTORS[k], c)\nresult = M.variant_summary(pipe, clip, N)\n# seeds = 101..105; ddof=1 for s_A\ndelta = mean_B - mean_A\nvisible_effect = abs(delta) > 2 * s_A\npractical = abs(delta) > tolerance',styles['MonoRU']));flow.append(Spacer(1,15))
for block in answers.split('\n\n'):
 if not block.startswith('#'):para(block)
page();heading('7. Комплект, вклад и источники')
para('Комплект для сдачи: выполненный ноутбук с выводами; этот отчёт; comparison.png; оригиналы A/B для пяти seed, их манифесты и SHA-256; таблицы метрик и классификации; контроль масштаба; изображения и проверка guidance; паспорт среды; независимый локальный проверяющий скрипт. Архив не содержит весов моделей. Полные версии зависимостей находятся в artifacts/environment.txt.')
para('Индивидуальный вклад: сформулирована гипотеза и допуски, организовано сохранение серии, выполнен контроль масштаба, пересчитаны пространственные метрики и сводная статистика, проверена ошибка CFG, проведён осмотр и оформлены ноутбук и отчёт. Демонстрационные числа из методички не выдаются за свои результаты.')
para('Источники','H2RU')
sources=[('Методические указания ЛР6','Приложенный PDF «ЛР06_Исследование_параметров_text_to_image», 20 страниц; lab05_lib.py, lab05_demo.py, lab06_lib.py, lab06_demo.py.'),('Документация Engee','https://engee.com/helpcenter/stable/ru/guide/workspacearray.html'),('SD-Turbo: карточка и файлы','https://huggingface.co/stabilityai/sd-turbo/tree/'+p['revision']),('SD-Turbo: лицензия','https://huggingface.co/stabilityai/sd-turbo/blob/'+p['revision']+'/LICENSE.md'),('CLIP: модель и ревизия','https://huggingface.co/openai/clip-vit-base-patch32/tree/'+p['clip_revision']),('Radford et al., CLIP','https://arxiv.org/abs/2103.00020'),('Sauer et al., ADD','https://arxiv.org/abs/2311.17042')]
for name,url in sources:para(name+'\n'+url,'SmallRU')
para('Весам и исходникам применимы их собственные лицензии. Использование здесь учебное; открытый доступ не равен неограниченным правам. Коммерческие условия и права на дальнейшее использование требуют отдельной проверки.','SmallRU')
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#d5dfe6'));c.line(36,35,559,35);c.setFont('Arial',8);c.setFillColor(colors.HexColor('#567080'));c.drawString(36,23,'ЛР6 · Вариант 3 · Власюк Д. В.');c.drawRightString(559,23,str(doc.page))
path=O/'ЛР06_Вариант_3_Отчёт.pdf'
SimpleDocTemplate(str(path),pagesize=(595.28,841.89),leftMargin=36,rightMargin=36,topMargin=40,bottomMargin=50,title='ЛР6. Вариант 3',author=p['student']).build(flow,onFirstPage=footer,onLaterPages=footer)
print(path)
