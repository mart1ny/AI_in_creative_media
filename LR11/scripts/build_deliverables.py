# -*- coding: utf-8 -*-
from pathlib import Path
import json,html,sys,hashlib,zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nbformat as nb
from nbclient import NotebookClient
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
R=Path(__file__).resolve().parents[1];A=R/'artifacts';P=R/'reports'
recs=json.loads((A/'per_seed.json').read_text());s=json.loads((A/'summary.json').read_text());passport=json.loads((A/'passport.json').read_text())
assert len(recs)==10
for row in s['rows']:
 a=np.array([r['metrics'][row[0]] for r in recs if r['regime']=='A']);b=np.array([r['metrics'][row[0]] for r in recs if r['regime']=='B']);d=b.mean()-a.mean();sd=a.std(ddof=1)
 assert np.allclose(row[1:6],[a.mean(),sd,b.mean(),d,abs(d)/sd])
fig,axes=plt.subplots(2,2,figsize=(10,6))
for name in ['A','B']:
 h=json.loads((A/f'history_{name}_101.json').read_text())
 for ax,key in zip(axes.flat,['lg','ld','d_real','d_fake']):ax.plot(np.arange(len(h[key]))*10,h[key],label=name);ax.set_title(key);ax.set_xlabel('training step');ax.grid(alpha=.2);ax.legend()
fig.tight_layout();fig.savefig(A/'losses.png',dpi=150);plt.close(fig)
tols={'nn_psnr':.5,'coverage':.1,'diversity':.05}
table=[['Метрика','Среднее A','s_A','Среднее B','Δ','∣Δ∣/s_A','>2s_A','>допуск']]
for row in s['rows']:
 m,ma,sd,mb,d,q,flag=row;table.append([m,*[f'{v:.4f}' for v in [ma,sd,mb,d,q]],'да' if flag else 'нет',('да' if abs(d)>tols[m] else 'нет') if m in tols else 'не задан'])
answers='''1. D минимизирует -E log D(x) - E log(1-D(G(z))); G в ненасыщающей постановке минимизирует -E log D(G(z)). Обновления чередуются; на шаге D подделки отсоединены от графа G.
2. Когда D(G(z)) близко к нулю, исходная минимаксная log(1-D(G(z))) даёт слабый градиент по логиту. Для проверки нужен отдельный фактор потери (вариант 6); вариант 3 этого не проверяет.
3. Падение потери G означает улучшение относительно текущего D; качество и разнообразие подтверждаются образцами и отдельными метриками.
4. nn_psnr измеряет близость каждой подделки к ближайшему тестовому образцу. coverage измеряет охват тестовых сцен. Повтор одного реалистичного диска может дать высокий PSNR при низком охвате.
5. Для короткого обучения и трёх факторов 5-й сосед даёт слишком маленькие шары; 20-й делает coverage чувствительнее. Значения с разными k напрямую несопоставимы.
6. diversity<1 указывает на меньший разброс, возможное схлопывание; >1 может означать лишний шум. Ровно 1 не гарантирует реалистичности.
7. lr и beta1 зависят от данных, архитектуры и длины обучения. Предупреждение DCGAN не является универсальным законом для учебной сцены.
8. Одинаковый знак на пяти seed - направленная тенденция. Если |Δ|≤2s_A, эвристический порог не превышен; практическую пользу проверяют отдельно.
9. Снимки показывают переход от шума к структуре, временные колебания и возможное позднее схлопывание.
10. Версии библиотек, аппаратная платформа, порядок операций с плавающей точкой и параллелизм могут менять траекторию. Нужны несколько seed, паспорт и допуски вместо требования побитового совпадения.
11. Нужны пять seed для каждого режима, общие train/test, архитектура, batch, число шагов, потоки и версия кода, четыре метрики, журналы и листы образцов. Меняется только выбранный фактор.'''
(P/'control_answers.md').write_text(answers)
sections=[]
def add(title,text):sections.append((title,text))
add('Лабораторная работа №11. Базовая GAN','Власюк Данил Витальевич, Т26ИИКТ-МИК11. Вариант 3.\nСобственный эксперимент: '+passport['started']+' (UTC).')
add('Цель и гипотеза','Обучить GAN на синтетических сценах с диском и проверить влияние повышения скорости обучения обеих сетей с 0.0002 до 0.001.\n'+(R/'journal.md').read_text())
add('Данные и архитектура','4096 обучающих и 1024 тестовых сцены 32×32×3 из lab07_lib.py. Генератор: z=32, Linear до 64×4×4, ConvTranspose 64→32→16→3, BatchNorm и ReLU, выход Sigmoid. Дискриминатор: Conv 3→16→32→64, LeakyReLU(0.2), Linear до логита; без BatchNorm. Adam: beta1=0.5, beta2=0.999, batch64, 1500 пар обновлений, ненасыщающая потеря G. Между A и B меняется только lr_g и lr_d.')
add('Среда и выполнение','Фактический запуск выполнен в Engee 26.10.2-H3 на CPU. Python '+passport['python'].split()[0]+', PyTorch '+passport['torch']+', NumPy '+passport['numpy']+', потоки '+str(passport['threads'])+'.\nКоманда: python3 -u LR11/src/execute_lr11.py. Все десять обучений выполнены; метрики и история каждого запуска сохранены отдельно. Гипотеза и допуски записаны до запуска основной серии Engee; перед этим была остановленная локальная проба, исключённая из сдаваемых результатов. Опыт пробы мог повлиять на ожидания.\nВремя seed101 включает callbacks сохранения снимков; остальные времена не включают их. Поэтому seconds - эксплуатационный замер, а не чистый контролируемый тест производительности.')
add('Методика метрик','1024 подделки и 1024 тестовые сцены. nn_psnr: среднее 10log10(1/MSE) до ближайшей тестовой сцены. coverage: доля тестовых сцен, в шар радиуса до 20-го тестового соседа которых попала подделка. diversity: среднее попарное расстояние подделок / такое же тестовых сцен. s_A выборочное по пяти seed. Эвристика |Δ|>2s_A не заменяет проверку статистической значимости. Для diversity учитывается близость к 1, а не просто рост.')
add('Результаты','Собственные результаты десяти обучений приведены ниже. Порог практического изменения не означает автоматически улучшение качества.')
# dynamic conclusion
nn=s['rows'][0];cv=s['rows'][1];dv=s['rows'][2]
add('Оценка гипотезы',f'Получены Δnn_psnr={nn[4]:+.4f} дБ, Δcoverage={cv[4]:+.4f}, Δdiversity={dv[4]:+.4f}. '+('Гипотеза ухудшения PSNR не подтвердилась: B выше A.' if nn[4]>0 else 'Направление изменения PSNR согласуется с гипотезой ухудшения.')+' '+('Гипотеза снижения охвата не подтвердилась.' if cv[4]>0 else 'Охват снизился, что согласуется с гипотезой.')+f' Расстояние diversity до 1: A={abs(dv[1]-1):.4f}, B={abs(dv[3]-1):.4f}.')
ha=json.loads((A/'history_A_101.json').read_text());hb=json.loads((A/'history_B_101.json').read_text())
add('Потери и качество',f"На последних десяти зарегистрированных точках seed101 средняя потеря G: A={np.mean(ha['lg'][-10:]):.4f}, B={np.mean(hb['lg'][-10:]):.4f}; D: A={np.mean(ha['ld'][-10:]):.4f}, B={np.mean(hb['ld'][-10:]):.4f}. Сравнение относится к одному seed, а таблица - к пяти. Значения потерь описывают игру с текущим D и не являются оценкой качества изображения. Изменение PSNR необходимо рассматривать вместе с coverage, diversity и визуальными артефактами.")
add('Справочные данные преподавателя','Приложенная сводка results_30_summary.txt, вариант3: nn_psnr A20.22/B22.27, coverage A0.786/B0.980, diversity A0.917/B0.933. Это чужой прогон Engee от 20.09.2026, не результат данного запуска. Приложенный demo11_sheet.png относится к варианту1 (размерность шума), поэтому он не использован как собственный лист варианта3. Различия с новым прогоном возможны из-за PyTorch, платформы и численной траектории обучения.')
add('Визуальная оценка',(P/'visual_review.md').read_text())
add('Ограничения и вывод','Сравнены две конфигурации на одной простой сцене и пяти seed. Нельзя переносить вывод на естественные изображения или считать lr=0.001 универсально лучшей настройкой. Пиксельные метрики не оценивают семантику. Парные seed не устраняют все различия траекторий. Обучение не повторено вторым независимым полным прогоном. Для уверенной оценки времени нужно исключить callbacks и контролировать нагрузку. Цель работы выполнена: GAN обучена, динамика и разнообразие измерены, эффект lr сопоставлен с разбросом и практическими допусками. Версии среды приведены в паспорте.')
add('Паспорт и источники','Полный паспорт: artifacts/passport.json; конфигурации, SHA-256 кода и seed сохранены. Архив: ЛР11_Вариант_3_Сдача.zip. Источники: приложенная методичка ЛР11, src11.zip и lab07_lib.py из ЛР7. Синтетические сцены порождаются кодом, внешние изображения не загружались. Отдельная лицензия на присланный учебный код не приложена; отсутствие внешнего датасета само по себе не задаёт лицензию кода. Общедоступные источники из методички: Goodfellow et al. arXiv:1406.2661; Radford et al. arXiv:1511.06434; Naeem et al. arXiv:2002.09797.')
add('Ответы для защиты',answers)
# Markdown
md=[]
for title,text in sections:
 md.extend(['## '+title,text,''])
 if title=='Результаты':
  md+=['| '+' | '.join(table[0])+' |','| '+' | '.join(['---']*len(table[0]))+' |']+['| '+' | '.join(row)+' |' for row in table[1:]]
  md+=['![Потери](../artifacts/losses.png)','![A](../artifacts/A_32.png)','![B](../artifacts/B_32.png)']
(R/'reports/ЛР11_Вариант_3_Отчёт.md').write_text('\n\n'.join(md))
# PDF
for name,file in [('Arial','Arial.ttf'),('Bold','Arial Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,'/System/Library/Fonts/Supplemental/'+file))
body=ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14,spaceAfter=8);head=ParagraphStyle('head',parent=body,fontName='Bold',fontSize=15,leading=19,spaceBefore=12,keepWithNext=True)
small=ParagraphStyle('sm',parent=body,fontSize=7,leading=10)
flow=[]
for title,text in sections:
 flow.append(Paragraph(html.escape(title),head))
 for para in text.split('\n'):flow.append(Paragraph(html.escape(para),body))
 if title=='Результаты':
  t=Table([[Paragraph(html.escape(v),small) for v in row] for row in table],colWidths=[71,60,52,60,52,55,47,58],repeatRows=1);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef5')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));flow.extend([t,Spacer(1,12),Image(str(A/'losses.png'),width=490,height=294)])
  for name in ['A','B']:
   flow.append(KeepTogether([Paragraph('32 образца, seed101, режим '+name,body),Image(str(A/f'{name}_32.png'),width=420,height=210)]))

  flow.append(Paragraph('Динамика seed101: шаги 100, 300, 700, 1500',head))
  for name in ['A','B']:
   for step in [100,300,700,1500]:
    flow.append(KeepTogether([Paragraph(f'{name}, шаг {step}',small),Image(str(A/f'{name}_s101_step{step}.png'),width=300,height=150)]))
 def footer(c,d):c.setFont('Arial',8);c.drawString(42,25,'ЛР11 · Вариант 3 · Власюк Д. В.');c.drawRightString(552,25,str(d.page))
SimpleDocTemplate(str(R/'output/pdf/ЛР11_Вариант_3_Отчёт.pdf'),leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=42).build(flow,onFirstPage=footer,onLaterPages=footer)
# executed notebook: analysis cells read original execution data; training source provided separately
cells=[nb.v4.new_markdown_cell('# ЛР11. Базовая GAN\nВариант3. Власюк Данил Витальевич.\nОбучение выполнено отдельным Python-процессом внутри Engee. Ячейки ниже анализируют сохранённые результаты, не повторяют обучение.\n'+(R/'journal.md').read_text()),nb.v4.new_code_cell("from pathlib import Path\nimport json\nR=Path.cwd().parent\nA=R/'artifacts'\nprint((A/'passport.json').read_text())"),nb.v4.new_code_cell("print((R/'run.log').read_text())\nprint((A/'summary.json').read_text())"),nb.v4.new_code_cell("from IPython.display import display,Image\nfor f in ['losses.png','A_32.png','B_32.png']:\n    display(Image(filename=str(A/f)))")]
for title,text in sections[1:]:cells.append(nb.v4.new_markdown_cell('## '+title+'\n'+text))
cells.append(nb.v4.new_markdown_cell('## Исходный код полного прогона\nДля нового обучения: `python3 src/execute_lr11.py` из каталога LR11. Команда перезаписывает результаты, используйте копию папки.\n```python\n'+(R/'src/execute_lr11.py').read_text()+'\n```'))
n=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}})
nb.write(n,R/'notebooks/LR11_analysis_template.ipynb')
(P/'verification.txt').write_text('PASS: 10 runs, summary recomputed from per-seed records; training performed in Engee external Python process.\n')
print('Deliverables built')
