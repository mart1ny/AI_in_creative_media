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
  configs/          параметры запуска (запрос, зерно, шаги)
  src/              скрипты генерации и проверки
  notebooks/        ноутбук для Google Colab с графическим процессором
  data/             бриф варианта и происхождение запроса
  artifacts/        PNG и manifest.json по запускам
  reports/          environment.txt, логи, отчёт
```

Кэш весов и виртуальное окружение в сдаваемый архив и git не входят.

## Как запускать в Google Colab

1. Откройте [Google Colab](https://colab.research.google.com/).
2. Среда выполнения → сменить тип → графический процессор (Tesla T4 достаточно).
3. Загрузите `notebooks/LR01_variant2_colab.ipynb` или клонируйте этот репозиторий в ячейке.
4. Выполните все ячейки. Первый запуск скачивает закреплённую ревизию SD Turbo.
5. Файл → скачать `.ipynb` — так сохраняются выводы ячеек.
6. Скачайте архив с `artifacts/` и `reports/` из последней ячейки.

Факт проверки 20.09.2026 (Colab, Tesla T4): два PNG 512×512, SHA-256 `4b14be2c…c29f02fa`, поле `"exact_sha256_match": true`. Исполненный ноутбук лежит в `notebooks/LR01_variant2_colab.ipynb`.

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

Критерий: `reports/sha256_comparison.json` содержит `"exact_sha256_match": true` **внутри той же среды**. Совпадение с чужим запуском на CPU или GPU не требуется.
