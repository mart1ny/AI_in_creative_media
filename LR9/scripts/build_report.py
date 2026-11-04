from pathlib import Path
import json,html,statistics
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1];O=R/'output/pdf';O.mkdir(parents=True,exist_ok=True)
for n,f in [('Arial','Arial.ttf'),('Bold','Arial Bold.ttf')]:pdfmetrics.registerFont(TTFont(n,'/System/Library/Fonts/Supplemental/'+f))
body=ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14,spaceAfter=8)
head=ParagraphStyle('head',parent=body,fontName='Bold',fontSize=16,leading=21,spaceBefore=12,spaceAfter=12)
small=ParagraphStyle('small',parent=body,fontSize=8,leading=11)
flow=[];md=[]
def p(s,h=False):
 flow.append(Paragraph(html.escape(s).replace('\n','<br/>'),head if h else body));md.append(('## ' if h else '')+s+'\n')
def table(rows):
 t=Table([[Paragraph(html.escape(str(c)),small) for c in row] for row in rows],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef5')),('GRID',(0,0),(-1,-1),.4,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));flow.extend([t,Spacer(1,12)]);md.extend(['| '+' | '.join(map(str,x))+' |' for x in rows])
p('Лабораторная работа №9\nПромпт-инжиниринг',True);p('Вариант 3. Власюк Данил Витальевич\nГруппа Т26ИИКТ-МИК11\n4 ноября 2026 года')
p('Цель и постановка',True);p('Проверить влияние одного элемента запроса на SD-Turbo и сравнить три приёма обращения к языковой модели. Контекст: афиша фестиваля робототехники. Сравниваются только исходный предмет и добавление цветовой палитры.')
p('Гипотеза до запуска',True);p((R/'journal.md').read_text())
p('Методика',True);p('A: robotic arm poster. B: robotic arm poster, deep blue and amber colors. Текст-цель: deep blue and amber colors. Общие seed 101-105, размер 512×512, один шаг, guidance_scale=0, CPU float32. Учебные функции генерации и метрик сохранены без изменения. Критерий |Δ|>2s_A является эвристикой разброса, а не p-value. CLIP измеряет соответствие тексту, а не качество изображения.')
A=R/'artifacts';cmp=json.loads((A/'comparison.json').read_text());env=json.loads((A/'environment.json').read_text())
p('Результаты генерации',True);table([['Метрика','A','s_A','B','Δ','|Δ|/s','>2s']]+[[r[0]]+[f'{v:.4f}' for v in r[1:6]]+['да' if r[6] else 'нет'] for r in cmp['rows']])
for r in cmp['rows']:
 tol=1 if r[0].startswith('clip') else .1*abs(r[1]);p(f'{r[0]}: допуск {tol:.4f}, Δ={r[4]:+.4f}; превышение допуска: {abs(r[4])>tol}.')
if (A/'comparison.png').exists():flow.append(Image(str(A/'comparison.png'),width=480,height=240));md.append('![Сравнение A/B](../artifacts/comparison.png)')
p((R/'reports/visual_review.md').read_text())
p('Эксперимент с языковой моделью',True);p('Dia, стандартный чат без выбора модели, 04.11.2026. Точная базовая модель интерфейсом не сообщена. Девять новых чатов, без истории предыдущих повторов; поиск запрещён текстом учебного запроса. Использованы исходные build_prompt(zero/few/step,1). Пять описаний заказчика в каждом повторе. Полные тексты запросов приложены в prompts/, ответы в answers/. JSON zero/few скопирован кнопкой Copy code (без внешнего Markdown-ограждения), пошаговые ответы целиком кнопкой Copy as text; содержимое не исправлялось.')
scores=json.loads((R/'reports/llm_scores.json').read_text());table([['Приём','Повторов','K1','K2','K3','K4']]+[[m,3]+[f'{scores[m][k]:.3f}' for k in ['k1','k2','k3','k4']] for m in ['zero','few','step']])
p('Анализ и ограничения',True);p('K1 проверяет схему, K2 - подстрочное покрытие элементов, K3 - точное совпадение запретов; K4 оценивает согласованность style/composition между повторами. Потолок K1-K3 не означает эквивалентность методов на любых задачах. Различие K4 при трёх повторах и пяти описаниях предварительно; 30 сравнений на приём не независимы. Более сложный запрос сам по себе не гарантирует большей стабильности. Проверка подстрок допускает ложные совпадения и не заменяет смысловую оценку. Неизвестная базовая модель Dia ограничивает воспроизводимость.')
p('Паспорт среды',True);p(json.dumps(env,ensure_ascii=False,indent=2));p('Исходные скрипты и синтетические описания: приложенный src.zip. Ревизии SD-Turbo и CLIP закреплены учебной библиотекой и приведены выше. Веса не включаются в архив сдачи; сохраняются результаты и исходники. Запуск run_lr09.py всех 30 вариантов не требуется для индивидуального варианта: собственный сценарий выполняет те же функции для варианта 3.')
p('Ответы на контрольные вопросы',True);p((R/'reports/control_answers.md').read_text())
p('Вывод',True);p('Выполнено сравнение запросов на пяти общих seed и трёх приёмов языковой модели по трём независимым чатам. Решение о влиянии палитры следует из таблицы и визуальной оценки, а практический эффект отделён от разброса seed. По языковой части вывод ограничен контекстом робототехники и режимом Dia на дату запуска.')
p('Комплект и источники',True);p('Архив ЛР09_Вариант_3_Сдача.zip: ноутбук, исходники, изображения, метрики, девять ответов, запросы, журнал, PDF и Markdown-отчёт. Источники: приложенные методические указания ЛР09; lab09_lib.py и lab09_llm.py из src.zip. Чужие демонстрационные числа не используются как собственные результаты.')
def footer(c,d):c.setFont('Arial',8);c.drawString(42,25,'ЛР9 · Вариант 3 · Власюк Д. В.');c.drawRightString(550,25,str(d.page))
SimpleDocTemplate(str(O/'ЛР09_Вариант_3_Отчёт.pdf'),rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=42).build(flow,onFirstPage=footer,onLaterPages=footer)
(R/'reports/ЛР09_Вариант_3_Отчёт.md').write_text('\n'.join(md))
