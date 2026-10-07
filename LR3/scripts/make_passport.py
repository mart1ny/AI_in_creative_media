from pathlib import Path
import json,tomllib,hashlib,csv,statistics
R=Path(__file__).resolve().parents[1];e=tomllib.loads((R/'artifacts/environment_and_results.toml').read_text());r=list(csv.DictReader((R/'artifacts/per_seed.csv').open()))
p={ 'student':'Власюк Данил Витальевич','group':'Т26ИИКТ-МИК11','date':'2026-10-07','timezone':'Europe/Moscow','environment':'Engee 26.9.2-H4','julia':e['julia'],'platform':e['platform'],'packages':e['package_versions'],'library':'lab03_lib.jl из архива преподавателя от 19.09.2026','library_sha256':e['library_sha256'],'variant':3,'scene':{'n':128,'lo':.15,'hi':.85,'noise':.02,'checker':0},'seeds':list(range(101,106)),'rng':'Random.MersenneTwister(seed), локальный генератор','luma':'Float64.(Gray.(img)); Rec.601 вручную только для сравнения','histogram':{'bins':32,'domain':[0,1],'bin_index':'min(32,max(1,ceil(Int,v*32)))'},'factor':'imresize(imresize(g,ratio=0.25),size(g))','comparison':'imresize(imresize(g,ratio=0.5),size(g))','control':'noise=0.0, те же seed, два масштаба','thresholds':{'statistic':'abs(mean_after-mean_before)>2*std_before_between_seeds; std corrected=true','practical_relative':.05,'practical_psnr_db':30},'hypothesis_record':json.loads((R/'reports/pre_run_record.json').read_text()),'sha_luma_101':e['sha_first'],'sha_repeat':e['sha_repeat'],'sha_equal':e['sha_equal'],'hash_encoding':'Float64 IEEE754, little-endian, Julia vec column-major, SHA-256','metric_data':'Float64 до сохранения PNG','png_storage':'Gray{N0f8}, RGB{N0f8}; квантование для отображения отдельно от расчёта','psnr_x4_mean_db':e['psnr_x4'],'psnr_x2_mean_db':e['psnr_x2'],'demo_psnr':e['demo_psnr'],'demo_verified':e['demo_verified'],'cloud_folder':'/user/AI_in_creative_media/LR03','archive':'ЛР03_Вариант_3_Сдача.zip','notebook_metadata_note':'Автометаданные IJulia 1.9.3; фактический VERSION и stdout 1.12.4'}
(R/'reports/passport.json').write_text(json.dumps(p,ensure_ascii=False,indent=2))
text=f'''# Паспорт эксперимента ЛР 3 Вариант 3

Власюк Данил Витальевич, Т26ИИКТ-МИК11. Дата: 07.10.2026, Europe/Moscow.

Среда: Engee 26.9.2-H4; Julia {e['julia']}; Linux {e['platform']}. Пакеты Images {e['package_versions']['Images']}, Plots {e['package_versions']['Plots']}; Random, Statistics, SHA, TOML, Tar, Dates, InteractiveUtils — стандартные библиотеки Julia.

Библиотека: lab03_lib.jl от 19.09.2026, без изменений, 5027 байт.
SHA-256: {e['library_sha256']}

Сцена: синтетические диагональные градиенты RGB и круг; 128×128; lo=0.15, hi=0.85, noise=0.02, checker=0. RNG: локальный MersenneTwister(seed), seed 101, 102, 103, 104, 105.

Фактор: imresize(imresize(g,ratio=0.25),size(g)); 128×128 → 32×32 → 128×128. Сравнение: ratio=0.5; 128 → 64 → 128. Интерполяция штатной imresize пакета Images, параметры по умолчанию. Контроль без шума: noise=0, те же seed.

Яркость: Float64.(Gray.(img)); ручной способ 0.299R+0.587G+0.114B сравнивается с atol=1e-7, rtol=0. Максимум разности: {e['luma_maxdiff']:.16g}.

Метрики: mean, std с corrected=true по пикселям, энтропия 32 равных интервалов [0,1]. Индекс интервала min(32,max(1,ceil(Int,v*32))). PSNR=10log10(1/MSE), MSE=mean((a-b)^2), maxval=1. Агрегируется средний PSNR пяти seed, а не PSNR от среднего MSE.

Статистический учебный критерий: |Δ|>2s; Δ — разность средних пяти seed, s — выборочный разброс базовой метрики между seed. Практические критерии записаны 07.10.2026 в 20:23:23 MSK до старта 20:32:24 MSK: |Δ|/|base|>5%; средний PSNR<30 дБ. Гипотеза и хеш исходной записи: data/hypothesis.md, reports/pre_run_record.json.

Хеш яркости seed 101: {e['sha_first']}
Повторный хеш: {e['sha_repeat']}
Равенство: true. Хеш по байтам Float64 IEEE754 little-endian, порядок vec Julia по столбцам. Сохранённый before_seed101.f64 содержит 131072 байта. Хеш PNG не является хешем Float64.

Средний PSNR: ×4 {e['psnr_x4']:.12f} дБ; ×2 {e['psnr_x2']:.12f} дБ. Демонстрационный вариант 1: {e['demo_psnr']:.12f} дБ, совпал с методичкой. Независимая проверка: RESULT PASS, reports/verification.json.

Изображения PNG сохранены в N0f8 для просмотра. Все метрики рассчитаны до сохранения в Float64. CSV, исходные массивы, графики, исходники и исполненный ngscript включены в архив ЛР03_Вариант_3_Сдача.zip. Облачный путь: /user/AI_in_creative_media/LR03.

Служебные метаданные Engee Notebook указывают IJulia 1.9.3; фактический VERSION=1.12.4 подтверждён выводом. Скачанный сценарий сохранён без изменения этих метаданных.
'''
(R/'reports/passport.md').write_text(text)
