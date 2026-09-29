#!/usr/bin/env python3
"""Create the variant 3 lab notebook without third-party dependencies."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks/LR01_variant3.ipynb"


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(keepends=True)}


cells = [
    markdown("""# Лабораторная работа 1 — вариант 3

**Студент:** Власюк Данил Витальевич  
**Группа:** Т26ИИКТ-МИК11  
**Тема:** подготовка среды и паспорт воспроизводимого AI эксперимента  
**Контекст:** облачное небо для фона афиши  
**Фактор:** шаг решётки `cell` 32 → 64 пикселя

Гипотеза и правило решения записаны заранее в `data/hypothesis.md` (24.09.2026 13:39 UTC): увеличение шага решётки снизит граничную энергию; эффект по метрике обнаружен, если `|Δ| > 2 × s_base` при пяти seed. Ниже находятся фактически выполненные ячейки, выводы и ссылки на сохранённые файлы."""),
    markdown("## 1. Среда и предварительная запись"),
    code("""from pathlib import Path
import hashlib, json, platform, statistics, subprocess, sys, zlib
from datetime import datetime, timezone

ROOT = next((p for p in (Path.cwd(), *Path.cwd().parents) if (p / 'src/lab01_experiment.py').exists()), None)
if ROOT is None:
    ROOT = Path.cwd() / 'LR1_1'
assert (ROOT / 'src/lab01_experiment.py').exists(), 'Не найдена папка LR1_1'
PYTHON = ROOT / '.venv/bin/python'
if not PYTHON.exists():
    PYTHON = Path(sys.executable)
print('time_utc =', datetime.now(timezone.utc).isoformat())
print('root =', ROOT)
print('notebook interpreter =', sys.executable)
print('experiment interpreter =', PYTHON)
print('python =', platform.python_version())
print('platform =', platform.platform())
print('zlib =', zlib.ZLIB_VERSION)
freeze = subprocess.run([str(PYTHON), '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
print('third-party freeze =', freeze.stdout.strip() or '(empty)')
assert not freeze.stdout.strip(), 'Среда эксперимента должна быть без сторонних пакетов'
import_check = subprocess.run([str(PYTHON), '-c', "import sys; sys.path.insert(0, 'src'); import lab01_generator; print(lab01_generator.SCRIPT_VERSION)"], cwd=ROOT, capture_output=True, text=True, check=True)
print('generator import/version =', import_check.stdout.strip())
hypothesis = (ROOT / 'data/hypothesis.md').read_text(encoding='utf-8')
assert '24.09.2026, 13:39 UTC' in hypothesis and '|Δ| > 2 × s_base' in hypothesis
print('prior hypothesis and threshold = verified in data/hypothesis.md')"""),
    markdown("## 2. Ошибка без seed и исправление"),
    code("""diagnostic_dir = ROOT / 'artifacts/notebook_seed_diagnostic'
diagnostic_dir.mkdir(parents=True, exist_ok=True)
diagnostics = []
for label, seed in [('without_seed_1', None), ('without_seed_2', None), ('seed_101_1', 101), ('seed_101_2', 101)]:
    command = [str(PYTHON), 'src/lab01_generator.py', '--out', str(diagnostic_dir / label)]
    if seed is not None:
        command += ['--seed', str(seed)]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    result = json.loads(proc.stdout)
    diagnostics.append({'label': label, 'command': command, 'seed': result['seed'], 'sha256_pixels': result['sha256_pixels'], 'sha256_png': result['sha256_png'], 'stderr': proc.stderr.strip()})
    print(f"{label}: seed={result['seed']}, pixel_sha256={result['sha256_pixels']}, warning={bool(proc.stderr.strip())}")
assert diagnostics[0]['sha256_pixels'] != diagnostics[1]['sha256_pixels']
assert diagnostics[2]['sha256_pixels'] == diagnostics[3]['sha256_pixels']
assert all('ПРЕДУПРЕЖДЕНИЕ' in r['stderr'] for r in diagnostics[:2])
diagnostic_path = ROOT / 'reports/notebook_seed_diagnostic.json'
diagnostic_path.write_text(json.dumps({'runs': diagnostics, 'unseeded_equal': False, 'seeded_equal': True}, ensure_ascii=False, indent=2), encoding='utf-8')
print('diagnostic =', diagnostic_path.relative_to(ROOT))"""),
    markdown("## 3. Основной эксперимент варианта 3"),
    code("""out_dir = ROOT / 'artifacts/notebook_variant03'
command = [str(PYTHON), 'src/lab01_experiment.py', '--variant', '3', '--out', str(out_dir)]
proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
experiment_log = ROOT / 'reports/notebook_experiment.log'
experiment_log.write_text('command: ' + ' '.join(command) + '\\nstdout:\\n' + proc.stdout + 'stderr:\\n' + proc.stderr + 'returncode: ' + str(proc.returncode) + '\\n', encoding='utf-8')
result = json.loads((out_dir / 'results.json').read_text(encoding='utf-8'))
print(proc.stdout.strip())
print('result file =', (out_dir / 'results.json').relative_to(ROOT))
print('experiment log =', experiment_log.relative_to(ROOT))
print('base parameters =', result['params_base'])
print('factor parameters =', result['params_perturbed'])
assert result['variant'] == 3 and result['n'] == 5
assert result['params_base']['cell'] == 32 and result['params_perturbed']['cell'] == 64"""),
    markdown("## 4. Воспроизводимость по полным массивам пикселей"),
    code("""expected = {'EQ_1_2': True, 'EQ_1_4': True, 'EQ_1_3': False, 'EQ_2_4': True}
assert result['eq'] == expected
for number, run in enumerate(result['runs_repro'], 1):
    print(f"run={number} seed={run['seed']} pixel_sha256={run['sha256_pixels']} png_sha256={run['sha256_png']}")
print('eq =', result['eq'])
print('png_1_2_equal =', result['eq_png']['EQ_1_2_png'])
historical = json.loads((ROOT / 'artifacts/variant03/results.json').read_text(encoding='utf-8'))
assert result['metrics_table'] == historical['metrics_table']
assert [r['sha256_pixels'] for r in result['runs_repro']] == [r['sha256_pixels'] for r in historical['runs_repro']]
print('matches 24.09.2026 results = True')"""),
    markdown("## 5. Полная серия по пяти seed и проверка метрик"),
    code("""sys.path.insert(0, str(ROOT / 'src'))
import lab01_generator as gen
per_seed = []
for seed in range(101, 106):
    a = gen.run_once(result['params_base'], seed)
    b = gen.run_once(result['params_perturbed'], seed)
    per_seed.append({'seed': seed, 'base': a, 'factor': b})
    print(f"seed={seed} base={a['sha256_pixels'][:16]} factor={b['sha256_pixels'][:16]} edge_base={a['edge']:.6f} edge_factor={b['edge']:.6f}")
for metric in ('mean', 'contrast', 'edge', 'entropy'):
    base_values = [row['base'][metric] for row in per_seed]
    factor_values = [row['factor'][metric] for row in per_seed]
    row = result['metrics_table'][metric]
    assert statistics.fmean(base_values) == row['mean_base']
    assert statistics.stdev(base_values) == row['s_base']
    assert statistics.fmean(factor_values) == row['mean_pert']
    assert statistics.stdev(factor_values) == row['s_pert']
per_seed_path = ROOT / 'reports/notebook_per_seed.json'
per_seed_path.write_text(json.dumps(per_seed, ensure_ascii=False, indent=2), encoding='utf-8')
print('all four aggregate metrics independently verified = True')
print('per-seed data =', per_seed_path.relative_to(ROOT))"""),
    markdown("## 6. Таблица результатов и вывод"),
    code("""names = {'mean': 'Средняя яркость', 'contrast': 'Контраст', 'edge': 'Граничная энергия', 'entropy': 'Энтропия'}
print(f"{'Метрика':22} {'База':>8} {'s_база':>8} {'Фактор':>8} {'s_фактор':>9} {'Δ':>8} {'|Δ|/s':>8} {'Вывод':>12}")
for key, name in names.items():
    row = result['metrics_table'][key]
    outcome = 'существенно' if row['significant'] else 'не обнаружено'
    print(f"{name:22} {row['mean_base']:8.4f} {row['s_base']:8.4f} {row['mean_pert']:8.4f} {row['s_pert']:9.4f} {row['delta']:+8.4f} {row['delta_over_s']:8.2f} {outcome:>12}")
assert result['metrics_table']['edge']['delta'] < 0
assert result['metrics_table']['edge']['significant']
print('Гипотеза о снижении граничной энергии подтверждена по учебному критерию при n=5.')
print('Контраст и энтропия также уменьшились; изменение средней яркости не обнаружено при n=5.')
print('Читаемость заголовка этими четырьмя метриками не измерялась.')"""),
    markdown("""### Пара изображений для seed 101

Оба изображения 96 × 96 пикселей и показаны в одном масштабе.

| База `cell=32` | Фактор `cell=64` |
| :---: | :---: |
| ![Базовая текстура](../artifacts/notebook_variant03/artifacts/base_seed101.png) | ![Текстура после удвоения шага решётки](../artifacts/notebook_variant03/artifacts/perturbed_seed101.png) |

Ограничения: `n=5` даёт грубую оценку разброса; правило `2s_base` учебное и не является статистическим тестом. При `cell=64` в изображении 96 × 96 мало независимых узлов. Для оценки читаемости нужен отдельный макет с заголовком."""),
]

notebook = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}},
    "nbformat": 4,
    "nbformat_minor": 5,
}
OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(OUT)
