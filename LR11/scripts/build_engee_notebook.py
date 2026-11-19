# -*- coding: utf-8 -*-
from pathlib import Path
import json,uuid
R=Path(__file__).resolve().parents[1]
cells=[]
def add(kind,source):
 c=dict(cell_type=kind,id=uuid.uuid4().hex[:8],metadata={'engee':{'isDisplay':True,'isParagraph':kind=='markdown'}},source=source)
 if kind=='code':c.update(execution_count=None,outputs=[])
 cells.append(c)
add('markdown','# ЛР11. Базовая GAN\nВласюк Данил Витальевич, Т26ИИКТ-МИК11. Вариант3.\nОбучение выполнено отдельным Python-процессом внутри Engee. Ячейки ниже читают фактические результаты этого процесса и показывают образцы.\n'+(R/'journal.md').read_text())
add('code','cd("/user/AI_in_creative_media/LR11")\nprintln(read("artifacts/passport.json",String))')
add('markdown','## Полный повторный запуск\nЭтот блок отключён, чтобы открытие ноутбука не перезаписало готовые результаты. Для нового эксперимента скопируйте директорию и включите блок. Основной прогон выполнен до запуска ячеек анализа.')
add('code','if false\n    run(`/user/.user_venvs/py3.11/bin/python3 -u src/execute_lr11.py`)\nend')
add('code','println(read("run.log",String))\nprintln(read("artifacts/summary.json",String))')
add('code','for name in ("A_32.png", "B_32.png")\n    println(name)\n    display(MIME("image/png"), read(joinpath("artifacts",name)))\nend')
add('markdown',(R/'reports/ЛР11_Вариант_3_Отчёт.md').read_text())
for f in ['execute_lr11.py','lab11_lib.py']:
 add('markdown','## Код '+f+'\n```python\n'+(R/'src'/f).read_text()+'\n```')
n=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'display_name':'Julia','language':'julia','name':'julia'}},cells=cells)
(R/'notebooks/LR11_3.ngscript').write_text(json.dumps(n,ensure_ascii=False,indent=2))
