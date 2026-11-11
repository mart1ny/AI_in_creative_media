from pathlib import Path
import json,uuid
R=Path(__file__).resolve().parents[1];cells=[]
def add(k,s):
 c=dict(cell_type=k,id=uuid.uuid4().hex[:8],metadata={'engee':{'isDisplay':True,'isParagraph':k=='markdown'}},source=s)
 if k=='code':c.update(execution_count=None,outputs=[])
 cells.append(c)
add('markdown','# ЛР10. Сравнение text-to-image\nВласюк Данил Витальевич, Т26ИИКТ-МИК11. Вариант3.\n'+(R/'journal.md').read_text())
add('code','cd("/user/AI_in_creative_media/LR10")\nprintln(read("artifacts/passport.json",String))')
add('markdown','## Выполнение\nСценарий execute_lr10.py выполнен отдельным процессом Engee. Следующая ячейка показывает его фактический журнал; это не повторная генерация. Для нового расчёта: run(`/user/.user_venvs/py3.11/bin/python3 -u execute_lr10.py`). Модели загружаются последовательно, время измеряется после прогрева и до CLIP.')
add('code','println(read("run.log",String))\nprintln(read("artifacts/summary.json",String))')
for f in ['sources.md','blind_result.md','visual_review.md','conclusion.md','control_answers.md']:
 if (R/'reports'/f).exists():add('markdown',(R/'reports'/f).read_text())
add('markdown','## Исходный сценарий\n```python\n'+(R/'src/execute_lr10.py').read_text()+'\n```')
(R/'notebooks/LR10_3.ngscript').write_text(json.dumps(dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'display_name':'Julia','language':'julia','name':'julia'}},cells=cells),ensure_ascii=False,indent=2))
