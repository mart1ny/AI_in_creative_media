# Паспорт среды Engee — лабораторная работа 1, часть Б

**Исполнитель:** Власюк Данил Витальевич, группа Т26ИИКТ-МИК11.  
**Вариант:** 3.  
**Дата и время проверки:** 29.09.2026, 22:47–22:58 MSK (UTC+3).  
**Среда:** Engee в личном кабинете ДГТУ Ростов-на-Дону, кампус лицензия.

| Поле | Фактическое значение |
| --- | --- |
| Версия личного кабинета | `26.9.1.1` — нижний левый угол бокового меню кабинета. |
| Версия рабочей среды Engee | `26.9.2-H1` — заголовок вкладки рабочей среды. |
| Язык и версия ядра | Julia `1.12.4`, подтверждены `VERSION` и `versioninfo()`. |
| Рабочий каталог | `/user` по команде `pwd()`. |
| Папка курса | `/user/AI_in_creative_media`. |
| Папка лабораторной | `/user/AI_in_creative_media/LR01`. |
| Сценарий | `LR01_environment.ngscript`; одна кодовая ячейка с `println("VERSION = ", VERSION)` и `versioninfo()` выполнена и сохранена вместе с выводом. |
| Необработанный вывод | `versioninfo.txt` в папке LR01; идентичная копия находится в этом репозитории. |
| Исходный `seed` | `seed = 101`; в таблице «Переменные» виден `seed`, значение `101`, класс `Int64`. |
| После очистки | Команда интерфейса «Очистить все переменные» → подтверждение «Да»: `seed` исчез, служебный `ans = 101` остался в таблице. |
| После перезапуска | Команда «Перезапуск ядра» → подтверждение «Перезапустить»: `seed` отсутствует. Дополнительная команда `(isdefined(Main, :seed), isdefined(Main, :ans))` вернула `(false, true)`; в таблице виден `ans` с этим кортежем. |
| Ошибки выполнения | Ошибок при выполнении ячейки и сохранении сценария нет. |

## Необработанный вывод кодовой ячейки

```text
VERSION = 1.12.4
Julia Version 1.12.4
Commit 01a2eadb047 (2026-01-06 16:56 UTC)
Build Info:
  Official https://julialang.org release
Platform Info:
  OS: Linux (x86_64-linux-gnu)
  CPU: 112 × Intel(R) Xeon(R) Platinum 8180 CPU @ 2.50GHz
  WORD_SIZE: 64
  LLVM: libLLVM-18.1.7 (ORCJIT, skylake-avx512)
  GC: Built with stock GC
Threads: 5 default, 3 interactive, 5 GC (on 112 virtual cores)
Environment:
  JULIA_LSP_STORE_PATH = /user/lsp_store
  JULIA_CPU_TARGET = generic;sandybridge,-xsaveopt,clone_all;haswell,-rdrnd,base(1)
  JULIA_LSP_PORT = 3751
  JULIA_NUM_PRECOMPILE_TASKS = 8
  JULIA_PKG_PRECOMPILE_AUTO = 0
  JULIA_DEPOT_PATH = /user/.packages:/opt/depot/core:/opt/depot/mtl:/opt/depot/demos:/opt/depot/stdlib
  JULIA_PATH = /usr/local/julia
  LD_LIBRARY_PATH = /usr/local/nvidia/lib:/usr/local/nvidia/lib64
  JULIA_PROJECT = /user/.project/
  JULIA_DA_STORE_PATH = /user/da_store
  JULIA_PKG_SERVER = http://pkgserver.pkgserver.svc.cluster.local
  JULIA_NUM_THREADS = 7,1
  JULIA_DA_PORT = 3752
  JULIA_DEBUG = BackendLib,AbstractAPI
```

## Ход работы и наблюдения интерфейса

1. В панели «Файлы» выбран каталог `/user`. Меню по правому щелчку показывает «Создать» → «Папку» и «Скрипт» → `.ngscript`, `.ipynb`, `.jl`. Подменю в текущем интерфейсе не сработало при выборе мышью, поэтому папки созданы в «Командной строке» командой `mkpath("AI_in_creative_media/LR01")`. Наличие обеих папок подтверждено деревом файлов.
2. В «Командной строке» исполнены `VERSION`, `versioninfo()` и `pwd()`. Вывод `versioninfo()` дополнительно записан без правок в `versioninfo.txt`.
3. Файл `LR01_environment.ngscript` создан на основе формата стартового скрипта Engee, загружен через кнопку загрузки панели «Файлы» в LR01, открыт в «Редакторе скриптов», ячейка исполнена кнопкой «Выполнить», статус показал «Выполнено». Скрипт сохранён кнопкой «Сохранить», статус показал «Сохранено»; затем скачана копия с сохранённым выводом.
4. В панели «Переменные» объявлен `seed = 101`, после чего проверены «Очистить все переменные» и «Перезапуск ядра». В текущей версии `ans` отображается после обоих действий; наличие `seed` после перезапуска проверено отдельно через `isdefined`.
5. Версия личного кабинета считана из бокового меню, версия Engee — из заголовка вкладки. Учётные данные и полный адрес рабочего пространства в паспорт не вносились.
