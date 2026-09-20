# ЛР №1 — Запуск открытой модели text-to-image

Дисциплина: «Искусственный интеллект в креативных технологиях».

| Поле | Значение |
| --- | --- |
| Студент | Власюк Данил Витальевич |
| Группа | Т26ИИКТ-МИК11 |
| Вариант | 2 |
| Тема | Обложка подкаста о городской среде |
| Модель | `stabilityai/sd-turbo` |
| Ревизия | `b261bac6fd2cf515557d5d0707481eafa0485ec2` |

Успех работы — не «красивая картинка», а воспроизводимый локальный запуск открытых весов: PNG 512×512, JSON-манифест, `environment.txt` и сравнение SHA-256 двух запусков в одной среде.

## Структура

```
LR1/
  configs/          параметры запуска (prompt, seed, steps)
  src/              скрипты генерации и проверки
  notebooks/        ноутбук для Google Colab (GPU)
  data/             бриф варианта и происхождение prompt
  artifacts/        PNG и manifest.json по запускам
  reports/          environment.txt, логи, отчёт
```

Кэш весов и `.venv` в сдаваемый архив и git не входят.

## Как запускать в Google Colab (GPU)

1. Откройте [Google Colab](https://colab.research.google.com/).
2. Runtime → Change runtime type → GPU (T4 достаточно).
3. Загрузите `notebooks/LR01_variant2_colab.ipynb` или клонируйте этот репозиторий в ячейке.
4. Run all. Первый запуск скачивает закреплённую ревизию SD Turbo.
5. File → Download `.ipynb` — так сохраняются выводы ячеек.
6. Скачайте zip с `artifacts/` и `reports/` из последней ячейки.

После скачивания файлы возвращаются в этот репозиторий и коммитятся. Промпт и финальная генерация выполняются отдельно, в конце работы.

## Локальный запуск (CPU допустим)

```bash
cd LR1
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
export HF_HOME="$PWD/cache/huggingface"
python src/run_reproducibility.py 2>&1 | tee reports/run_console.log
```

Критерий: `reports/sha256_comparison.json` содержит `"exact_sha256_match": true` **внутри той же среды**. Совпадение с чужим CPU/GPU запуском не требуется.
