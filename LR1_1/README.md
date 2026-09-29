# ЛР 1_1 — Подготовка среды и паспорт эксперимента

**Студент:** Власюк Данил Витальевич, Т26ИИКТ-МИК11. **Вариант:** 3.

Эксперимент выполнен на учебном генераторе текстур из методического архива. Для фона афиши «облачное небо» проверено влияние удвоения шага решётки `cell` с 32 до 64 пикселей при неизменных остальных параметрах. Предварительная гипотеза записана в [`data/hypothesis.md`](data/hypothesis.md), полный отчёт — в [`reports/LR01_1_report.md`](reports/LR01_1_report.md).

## Состав

- `src/` — исходные скрипты преподавателя, скопированные из предоставленного архива без изменений;
- `requirements.txt` — пустой файл: в изолированной среде сторонние пакеты не установлены;
- `data/hypothesis.md` — гипотеза и порог, записанные до первого запуска эксперимента;
- `artifacts/variant03/` — исходные `results.json`, `passport.json`, `passport.md` и PNG;
- `artifacts/seed_diagnostic/` — изображения для проверки ошибки без `seed`;
- `notebooks/LR01_variant3.ipynb` — исполненный ноутбук с сохранёнными выводами шести кодовых ячеек;
- `notebooks/run_notebook.py` — повторный запуск ноутбука без сторонних пакетов;
- `artifacts/notebook_variant03/` и `artifacts/notebook_seed_diagnostic/` — результаты повторного запуска через ноутбук;
- `reports/` — единый отчёт по частям А и Б в `.md` и `.docx`, паспорт, сведения о среде, данные по каждому `seed` и журналы запуска;
- `engee/` — выполненный облачный сценарий `.ngscript` с сохранённым выводом, паспорт части Б, исходный `versioninfo()` и журнал действий.

## Повтор запуска

Нужен Python 3.10 или новее. В macOS/Linux из папки `LR1_1`:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip freeze > requirements.txt
.venv/bin/python src/lab01_experiment.py --variant 3 --out artifacts/variant03
.venv/bin/python notebooks/run_notebook.py
```

Проверка: в `results.json` поля `eq` должны содержать `true, true, false, true` в порядке `EQ_1_2`, `EQ_1_4`, `EQ_1_3`, `EQ_2_4`. При другой версии Python или `zlib` различия сначала сопоставляют с паспортом среды.

Выполненный ноутбук сравнивает новый результат с сохранённым запуском 24.09.2026. Полный журнал находится в `reports/notebook_run.log`, а сводный отчёт — в [`reports/LR01_1_report.md`](reports/LR01_1_report.md) и [`reports/ЛР01_Вариант_3_Отчёт.docx`](reports/ЛР01_Вариант_3_Отчёт.docx).

## Часть Б в Engee

29.09.2026 проверены кабинет `26.9.1.1`, среда `26.9.2-H1` и ядро Julia `1.12.4`. В Engee создана папка `/user/AI_in_creative_media/LR01`, запущен и сохранён [`engee/LR01_environment.ngscript`](engee/LR01_environment.ngscript), загружен [`engee/passport.md`](engee/passport.md). Полный вывод `versioninfo()` — в [`engee/versioninfo.txt`](engee/versioninfo.txt), наблюдения по `seed`, очистке и перезапуску — в паспорте и [`engee/session.log`](engee/session.log).
