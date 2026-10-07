#!/usr/bin/env python3
"""Независимые проверки сдачи; стандартная библиотека Python 3.10+."""
import csv,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import lab02_audit as A
import lab02_common as C
V=ROOT/'artifacts/v03'
checks={}
def check(name,condition):
    checks[name]=bool(condition)
    if not condition:raise AssertionError(name)
rows=list(csv.DictReader((V/'manifest.csv').open(encoding='utf-8',newline='')))
selected=list(csv.DictReader((V/'manifest_selected.csv').open(encoding='utf-8',newline='')))
policy=json.loads((V/'policy.json').read_text())
findings=A.audit(rows,policy)
decisions=json.loads((V/'audit_decisions.json').read_text())
check('исходный аудит 3 ошибки и 1 предупреждение',sum(f['severity']=='error' for f in findings)==3 and len(findings)==4)
check('решение и обоснование для каждой находки',{(f['rule'],f['item']) for f in findings}=={(f['rule'],f['item']) for f in decisions} and all(f['decision'].strip() and f['justification'].strip() for f in decisions))
check('выборка 8 без находок',len(selected)==8 and not A.audit(selected,policy))
check('политика варианта сохранена',policy=={'scenario':C.SCENARIOS['poster'][0],**C.SCENARIOS['poster'][1]})
with tempfile.TemporaryDirectory() as tmp:
    cmd=[sys.executable,str(ROOT/'src/lab02_make_variant.py'),'--variant','3','--out',tmp]
    r=subprocess.run(cmd,capture_output=True,text=True,check=True)
    for n in ['manifest.csv','policy.json','variant.json']:
        check('повторное создание '+n,(Path(tmp)/n).read_bytes()==(V/n).read_bytes())
risks=list(csv.DictReader((V/'risk_register.csv').open(encoding='utf-8',newline='')))
cats={r['category'] for r in risks}
check('семь рисков семь категорий',len(risks)==7 and len(cats)==7)
check('обязательные категории варианта',{'Intellectual Property','Information Integrity'}<=cats)
check('уникальные идентификаторы рисков',len({r['risk_id'] for r in risks})==len(risks))
for name,count in [('data_card.md',7),('model_card.md',9)]:
    text=(V/name).read_text()
    blocks=text.split('\n## ')[1:]
    check(name+' заполнены разделы',len(blocks)==count and all(len(b.split('\n',1)[1].strip())>50 for b in blocks))
r=subprocess.run([sys.executable,str(ROOT/'src/lab02_risks.py'),'--csv',str(V/'risk_register.csv')],capture_output=True,text=True)
check('штатная проверка PASS',r.returncode==0 and 'RESULT: PASS' in r.stdout)
for name,expected in json.loads((ROOT/'reports/source_sha256.json').read_text()).items():
    check('SHA256 '+name,hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected)
p=json.loads((ROOT/'inputs/lr01_variant03_passport.json').read_text())
check('версия исходного генератора ЛР1',hashlib.sha256((ROOT/'inputs/lr01_src/lab01_generator.py').read_bytes()).hexdigest()=='8f07d340a5a765a8e44f1fec407489cf00114ba54216aa7539c4e7116680e152')
check('метрики карточки из паспорта ЛР1',all(f"{m['mean_base']:.4f}".replace('.',',') in (V/'model_card.md').read_text() and f"{m['mean_pert']:.4f}".replace('.',',') in (V/'model_card.md').read_text() for m in p['результаты']['метрики'].values()))
(ROOT/'reports/verification.json').write_text(json.dumps({'result':'PASS','checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print('RESULT: PASS — '+str(len(checks))+' проверок; исходный аудит 3/1; выборка 8/0/0; риски 7/7.')
