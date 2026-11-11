from pathlib import Path
import json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1];A=R/'artifacts';out=R/'output/pdf';out.mkdir(parents=True,exist_ok=True)
for n,f in [('Arial','Arial.ttf'),('Bold','Arial Bold.ttf')]:pdfmetrics.registerFont(TTFont(n,'/System/Library/Fonts/Supplemental/'+f))
st=ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14,spaceAfter=8);h=ParagraphStyle('head',parent=st,fontName='Bold',fontSize=16,leading=20,spaceBefore=12,spaceAfter=10);sm=ParagraphStyle('small',parent=st,fontSize=8,leading=11)
flow=[];md=[]
def p(s,head=False):flow.append(Paragraph(html.escape(s).replace('\n','<br/>'),h if head else st));md.append(('## ' if head else '')+s+'\n')
def table(data):
 t=Table([[Paragraph(html.escape(str(v)),sm) for v in row] for row in data],repeatRows=1);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));flow.extend([t,Spacer(1,12)]);md.append('| '+' | '.join(str(v).replace('|','∣') for v in data[0])+' |');md.append('| '+' | '.join(['---']*len(data[0]))+' |');md.extend('| '+' | '.join(str(v).replace('|','∣') for v in row)+' |' for row in data[1:])
p('Лабораторная работа №10\nСравнительное исследование моделей text-to-image',True);p('Вариант 3. Власюк Данил Витальевич\nГруппа Т26ИИКТ-МИК11\n11 ноября 2026 года')
p('Цель и постановка',True);p('Сравнить конфигурации SD-Turbo и aMUSEd-256 на одном брифе, отделить разброс seed от практического эффекта и сопоставить численные показатели со слепым визуальным выбором. Сравниваются конфигурации целиком: причинный эффект архитектуры отдельно не определяется.')
p('Гипотеза и допуски до запуска',True);p((R/'journal.md').read_text())
passport=json.loads((A/'passport.json').read_text());s=json.loads((A/'summary.json').read_text());rows=s['rows']
p('Данные и методика',True);p(passport['prompt']);p('Обе конфигурации выполнены последовательно в одном сеансе Engee на CPU float32, 4 потока. Общие seed101-105. Загрузка и прогрев seed0 исключены из seconds. CLIP ViT-L/14 оценивает собственное разрешение изображений; edge/contrast рассчитаны после resize256. Результаты метрик сохранены до сжатия JPG; для проверки приложены PNG без потерь. Для слепых листов использованы JPG quality90, размер384 и зазор12, как в приложении методички.')
p('Численные результаты',True);table([['Метрика','A','s_A','B','Δ','|Δ|/s','>2s']]+[[r[0]]+[f'{x:.4f}' for x in r[1:6]]+['да' if r[6] else 'нет'] for r in rows])
for r in rows:
 tol=1 if r[0].startswith('clip') else abs(r[1])*.1
 practical=(max(r[1],r[3])/min(r[1],r[3])>=1.5) if r[0]=='seconds' else abs(r[4])>tol
 p(f'{r[0]}: критерий2s={r[6]}, практический допуск превышен={practical}. '+('Допуск времени: отношение1,5.' if r[0]=='seconds' else f'Абсолютный допуск={tol:.5f}.'))
t=next(r for r in rows if r[0]=='seconds');p(f'Среднее время B/A={t[3]/t[1]:.3f}. Время относится только к этим последовательным вызовам на CPU Engee; фоновая нагрузка и порядок запуска могут влиять. CLIP не измеряет эстетику, OCR и техническую правильность.')
p('Слепое сравнение',True);blind=json.loads((R/'reports/blind_evaluation.json').read_text());table([['Seed','Выбор','Обоснование']]+[[x['seed'],x['choice'],x['reason']] for x in blind['choices']]);p((R/'reports/blind_result.md').read_text());p('Оценку выполнил ИИ-ассистент по поручению студента. Это не независимое исследование с людьми; изображения разных разрешений и стиль могут частично раскрывать семейство модели. Ключ прочитан после сохранения выбора; даты и SHA-256 зафиксированы.')
p('Визуальное сопоставление seed101',True);flow.append(Image(str(A/'comparison.png'),width=480,height=240));md.append('![Сравнение](../artifacts/comparison.png)');p((R/'reports/visual_review.md').read_text())
p('Вывод и ограничения',True);p((R/'reports/conclusion.md').read_text());p('Один бриф, пять seed, две конфигурации, один сеанс CPU. Эвристика2s не является формальным тестом значимости. Равные номера seed не дают одинаковых внутренних случайных величин разным семействам. aMUSEd использует маскированные токены; число шагов не эквивалентно диффузионному. Размер кадра - часть конфигурации, а resize не устраняет все различия. CLIP может усекать длинный запрос; отрицания понимает слабо.')
p('Паспорт',True);p('Начало: '+passport['started']+'; Python '+passport['python']+'; '+passport['platform']);p('Пакеты: '+json.dumps(passport['packages'],ensure_ascii=False));p('CPU float32, потоки='+str(passport['threads'])+'; seed='+str(passport['seeds']));p('Конфигурации и ревизии: '+json.dumps(passport['configs'],ensure_ascii=False));p('CLIP '+passport['clip']+', ревизия '+passport['clip_revision']);p('SHA-256 сценария: '+passport['source_sha256']);p('Engee 26.10.2-H3. Конфигурации планировщиков сохранены отдельно в turbo_scheduler.json и amused_scheduler.json. Время загрузки не включалось в метрику seconds; повторный независимый полный прогон не выполнялся.')
p('Происхождение и лицензии',True);p((R/'reports/sources.md').read_text())
p('Контрольные вопросы',True);p((R/'reports/control_answers.md').read_text())
p('Комплект для сдачи',True);p('ЛР10_Вариант_3_Сдача.zip: сценарий, выполненный ноутбук, отчёты PDF/Markdown, паспорт, per-seed данные, PNG/JPG, пять слепых листов и ключ, зафиксированный выбор, журналы и проверка. Веса моделей не включены. Загрузка на do.skif не выполнялась.')
def footer(c,d):c.setFont('Arial',8);c.drawString(42,25,'ЛР10 · Вариант 3 · Власюк Д. В.');c.drawRightString(550,25,str(d.page))
SimpleDocTemplate(str(out/'ЛР10_Вариант_3_Отчёт.pdf'),leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=42).build(flow,onFirstPage=footer,onLaterPages=footer)
(R/'reports/ЛР10_Вариант_3_Отчёт.md').write_text('\n'.join(md))
