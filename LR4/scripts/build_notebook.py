"""Создать исходный ноутбук Engee без вымышленных результатов выполнения."""
from pathlib import Path
import json,uuid
R=Path(__file__).resolve().parents[1]
cells=[]
def cell(kind,text,name):
    c={'cell_type':kind,'id':uuid.uuid4().hex[:8],'metadata':{'name':name,'engee':{'isDisplay':True,'isParagraph':kind=='markdown','isClosedParagraph':False,'amountHideCellsInside':0,'codeOutputView':'col','codeOutputHidden':False}},'source':text.strip().splitlines(keepends=True)}
    if kind=='code':c.update(execution_count=None,outputs=[])
    else:c['attachments']={}
    cells.append(c)
def md(t,n):cell('markdown',t,n)
def code(t,n):cell('code',t,n)
md('''# Лабораторная работа 4 Исследование операций обработки изображений в Engee

**Вариант 3 — фильтр Гаусса σ=3, сцена со слабым шумом.**

Власюк Данил Витальевич, группа Т26ИИКТ-МИК11. 14 октября 2026 года.

Цель — сравнить сглаживание, повышение резкости, выделение границ, бинаризацию и морфологию относительно известного эталона. Основное исследование — вариант 3; дополнительно выполняются все шесть операций, демо, соседняя сцена и обзор 30 сочетаний. Синтетические данные: круг на градиенте, 128×128, пять seed 101–105. Обучение нейросети не требуется.

**Порядок выполнения:** поместить этот файл, `lab03_lib.jl`, `lab04_lib.jl` и `hypothesis.md` в отдельную папку `LR04` в Engee, затем выполнить все ячейки сверху вниз. Исходный ноутбук содержит код и пояснения; численные результаты и изображения формируются при фактическом запуске.''','Тема и порядок')
md('''## 1 Изучение документации WorkspaceArray

Изучена [документация Engee](https://engee.com/helpcenter/stable/ru/guide/workspacearray.html), дата обращения 14.10.2026.

`WorkspaceArray` нужен для временных рядов и ленивого доступа к данным моделирования. Он поддерживает индексацию и срезы; `collect` загружает выбранные данные. Изображения этой работы представлены обычными матрицами Julia `Matrix{Float64}`: моделирование временного сигнала и `WorkspaceArray` для их обработки не требуются.

Практический пример по документации: создаём CSV с `time,value`, открываем его как `WorkspaceArray`, получаем запись и срез. Пример изолирован в функции, поэтому недоступность этого API в вычислительной сессии не прервёт обработку изображений и будет явно отражена в выводе.''','Документация')
md((R/'data/hypothesis.md').read_text(),'Гипотеза до запуска')
code(r'''
using Images, Random, Statistics, SHA, Dates, TOML, Tar, InteractiveUtils, Printf
LR04_ROOT = isfile("lab04_lib.jl") ? pwd() : "/user/AI_in_creative_media/LR04"
cd(LR04_ROOT)
include("lab04_lib.jl")
LR04_OUT = joinpath(LR04_ROOT,"artifacts")
mkpath(LR04_OUT)
LR04_STARTED = string(now())
println("START ",LR04_STARTED,"; Julia ",VERSION,"; directory ",pwd())
versioninfo()
@assert size(make_gray4(101)) == (128,128)
@assert bytes2hex(sha256(read("lab04_lib.jl"))) == "094cecea2f55a0f53a652149a1a4025e98d87b3994b376be7028c4920cb0f8c2"
println("LIBRARIES LOADED; Images ",pkgversion(Images))
''','Подготовка среды')
code(r'''
function workspacearray_demo4()
    csvpath=joinpath(LR04_OUT,"workspacearray_example.csv")
    write(csvpath,"time,value\n0.1,1\n0.2,2\n0.3,3\n0.4,4\n0.5,5\n")
    if !isdefined(Main,:WorkspaceArray)
        msg="WorkspaceArray не экспортирован в Main этой сессии. Документация изучена; для изображений используются Matrix{Float64}."
        println(msg);write(joinpath(LR04_OUT,"workspacearray_status.txt"),msg)
        return nothing
    end
    try
        wa=getfield(Main,:WorkspaceArray)("lr04_demo",csvpath)
        first_record=wa[1]
        sliced=collect(wa[1:2:end])
        println("Первая запись: ",first_record,"\nКаждая вторая запись:");display(sliced)
        write(joinpath(LR04_OUT,"workspacearray_status.txt"),"EXECUTED\n"*sprint(show,sliced))
        return wa
    catch err
        msg="Пример WorkspaceArray: "*sprint(showerror,err)
        println(msg);write(joinpath(LR04_OUT,"workspacearray_status.txt"),msg)
        return nothing
    end
end
lr04_wa=workspacearray_demo4()
''','Пример WorkspaceArray')
md('''## 2 Вспомогательные функции и схема измерений

PSNR вычисляется **относительно эталона своей операции**. Для фильтров эталон — чистая сцена; для Собеля — нормированная карта её границ; для масок — истинный диск. Энергия границ — средний модуль градиента Собеля, контраст — выборочное стандартное отклонение пикселей. Разброс `s` в сводке — другая величина: стандартное отклонение базовой метрики между seed. PNG нужны для просмотра, измерения выполняются до квантования на Float64.''','Методика')
code(r'''
SEEDS4=101:105
OPNAMES4=["Усреднение 5×5","Гаусс σ=1","Гаусс σ=3","Нерезкая маска","Собель после Гаусса","Оцу и открытие"]
class4(d,t=1.0)=d>=t ? "полезна" : d<=-t ? "вредна" : "нейтральна"
function csv4(name,headers,rows)
    open(joinpath(LR04_OUT,name),"w") do io
        println(io,join(headers,","))
        for row in rows;println(io,join(row,","));end
    end
end
function mdtable4(headers,rows)
    esc(x)=replace(string(x),"|"=>"\\|")
    "| "*join(esc.(headers)," | ")*" |\n| "*join(fill("---",length(headers))," | ")*" |\n"*
    join(["| "*join(esc.(collect(r))," | ")*" |" for r in rows],"\n")
end
function showmd4(t)
    display(MIME"text/markdown"(),t)
end
function saveimage4(name,a)
    @assert size(a)==(128,128) && all(isfinite,a) && all(v->0<=v<=1,a)
    save(joinpath(LR04_OUT,name*".png"),Gray{N0f8}.(a))
end
function savedata4(name,a)
    open(joinpath(LR04_OUT,name*".f64"),"w") do io;write(io,vec(Float64.(a)));end
end
function summarytable4(z)
    headers=["Метрика","База","s","После","Δ","Модуль Δ / s",">2s"]
    rows=[(string(m),@sprintf("%.8f",b),@sprintf("%.8f",s),@sprintf("%.8f",a),@sprintf("%+.8f",d),@sprintf("%.3f",r),sig ? "Да" : "Нет") for (m,b,s,a,d,r,sig) in z.rows]
    mdtable4(headers,rows)
end
function perseed4(c,k)
    refclean=clean4(c)
    [(seed=s,scene=c,operation=k,
      psnr_before=psnr_db(b,ref),psnr_after=psnr_db(a,ref),
      mse_before=mse(b,ref),mse_after=mse(a,ref),
      edge_before=edge_energy(b),edge_after=edge_energy(a),
      contrast_before=std(b),contrast_after=std(a),
      iou_before=k==6 ? iou(Bool.(b),Bool.(ref)) : NaN,
      iou_after=k==6 ? iou(Bool.(a),Bool.(ref)) : NaN)
     for s in SEEDS4 for (a,b,ref) in (pair4(make_gray4(s;scene4(c)...),refclean,k),)]
end
println("Схема измерений и экспорта готова")
''','Измерение и экспорт')
md('''## 3 Воспроизведение демонстрационного варианта

Демо из методички — усредняющий фильтр 5×5 на сцене со слабым шумом. Сопоставляем все три метрики с опубликованным журналом преподавателя. Результаты ниже получаются при запуске, а не копируются в ячейку вывода.''','Демонстрация')
code(r'''
demo4=variant_summary4(1)
expected4=[(33.982103137714965,0.07450305641014086,29.19575338868147,-4.786349749033494),
(0.01692548814288977,0.00012750148456890567,0.008424262473284544,-0.008501225669605225),
(0.20774642267754806,0.00017156629178605263,0.20065402164009138,-0.007092401037456675)]
DEMO_MATCH4=all(isapprox(demo4.rows[i][j+1],expected4[i][j];atol=1e-10,rtol=0) for i in 1:3,j in 1:4)
println("MATCH_DEMO=",DEMO_MATCH4)
@assert DEMO_MATCH4
showmd4(summarytable4(demo4))
''','Проверка демо')
md('''## 4 Исходная сцена и оценка шума

Для основного варианта фон изменяется от 0.10 до 0.40, диск имеет яркость 0.75, шум σₙ=0.02. Эталон получаем той же функцией при нулевом шуме. Сравниваем измеренный PSNR с оценкой `−20log10(σₙ)`. Повторяем построение с тем же seed и сверяем SHA-256 массива, а не файла PNG.''','Исходные данные')
code(r'''
x4=make_gray4(101;scene4(1)...)
clean_scene4=clean4(1)
@assert x4==make_gray4(101;scene4(1)...)
@assert gauss4(x4,3)≈imfilter(x4,Kernel.gaussian(3),"replicate")
SHA_SCENE4=bytes2hex(sha256(reinterpret(UInt8,vec(x4))))
noise_rows4=[(r.seed,r.psnr_before,-20log10(scene4(1).noise),r.psnr_before+20log10(scene4(1).noise)) for r in perseed4(1,3)]
showmd4(mdtable4(["Seed","Измеренный PSNR дБ","Теория дБ","Разница дБ"],noise_rows4))
println("size=",size(x4),"; type=",eltype(x4),"; min/max=",extrema(x4),"; bytes=",sizeof(x4),"; SHA256=",SHA_SCENE4)
saveimage4("noisy_seed101",x4);saveimage4("reference_clean",clean_scene4)
savedata4("noisy_seed101",x4);savedata4("reference_clean",clean_scene4)
showmd4("Слева — зашумлённая сцена; справа — чистый эталон.")
display(Gray{N0f8}.(repeat(hcat(x4,clean_scene4),inner=(2,2))))
''','Сцена и шум')
md('''## 5 Все шесть операций

Каждая операция запускается на одной и той же сцене, seed 101; затем её метрики усредняются по пяти seed. Параметры определены исходной библиотекой преподавателя. Изображения показывают **базу, результат и эталон** слева направо. Для Собеля база — границы без сглаживания; для морфологии база — маска Оцу без открытия.''','Все операции')
for k in range(1,7):
    descriptions={1:'Среднее по окну 5×5 подавляет шум и размывает резкие переходы.',2:'Гаусс σ=1 использует больший вес близких пикселей и даёт мягкое сглаживание.',3:'Основной вариант. Гаусс σ=3 сильнее подавляет шум, но сильнее размывает границу диска.',4:'Нерезкая маска x+(x−G₁*x) усиливает высокие частоты, в том числе шум; значения ограничиваются [0,1].',5:'Сначала Гаусс σ=1, затем Собель. Все карты делятся на один максимум градиента чистой сцены, затем ограничиваются [0,1].',6:'Автоматический порог Оцу даёт маску; эрозия и следующая за ней дилатация удаляют мелкие включения. Эталон — истинный круг, дополнительно измеряем IoU.'}
    md(f'### Операция {k}\n\n{descriptions[k]}',f'Пояснение операции {k}')
    code(f'''a4_{k},b4_{k},ref4_{k}=pair4(x4,clean_scene4,{k})
z4_{k}=variant_summary4({k})
showmd4("**"*OPNAMES4[{k}]*"**\\n\\n"*summarytable4(z4_{k}))
println("ΔPSNR=",z4_{k}.rows[1][5]," дБ; операция ",class4(z4_{k}.rows[1][5]))
saveimage4("op{k}_result_seed101",a4_{k})
saveimage4("op{k}_base_seed101",b4_{k})
saveimage4("op{k}_reference",ref4_{k})
display(Gray{{N0f8}}.(repeat(hcat(b4_{k},a4_{k},ref4_{k}),inner=(2,2))))
''' + ('println("Средний IoU после открытия=",z4_6.iou)\n' if k==6 else ''),f'Выполнение операции {k}')
md('''## 6 Основной вариант 3 и соседняя сцена

Сохраняем результаты отдельно для каждого seed. Сравниваем Гаусс σ=1 и σ=3 на слабом шуме и σ=3 на соседней сцене с шумом 0.05. Дополнительная сцена меняет уровень шума при той же структуре; она показывает границы переноса вывода, но не представляет выборку реальных фотографий.''','Серия варианта 3')
code(r'''
selected4=[variant_summary4(n) for n in (2,3,9)]
rows_selected4=[(z.variant,scene4(z.ctx).noise,z.fac==2 ? 1 : 3,z.rows[1][2],z.rows[1][4],z.rows[1][5],class4(z.rows[1][5])) for z in selected4]
showmd4(mdtable4(["Вариант","Шум","σ фильтра","PSNR до","PSNR после","Δ дБ","Класс"],rows_selected4))
main_series4=perseed4(1,3)
showmd4(mdtable4(["Seed","PSNR до","PSNR после","MSE до","MSE после"],[(r.seed,r.psnr_before,r.psnr_after,r.mse_before,r.mse_after) for r in main_series4]))
savedata4("gauss3_seed101",a4_3)
showmd4("Крупный фрагмент границы диска: база, Гаусс σ=3, чистый эталон.")
display(Gray{N0f8}.(repeat(hcat(x4[25:55,45:80],a4_3[25:55,45:80],clean_scene4[25:55,45:80]),inner=(5,5))))
neighbor4=make_gray4(101;scene4(2)...)
saveimage4("neighbor_noisy_seed101",neighbor4)
saveimage4("neighbor_gauss3_seed101",gauss4(neighbor4,3))
''','Сравнение параметров и шума')
md('''## 7 Обзор сочетаний и сохранение таблиц

Для полноты выполняем `variant_summary4` для всех 30 сочетаний. Это описательный обзор; основной вывод и гипотеза относятся к варианту 3. Сохраняем метрики каждого seed и сводки, чтобы проверка не зависела от округлений в ноутбуке. `NaN` в IoU для операций 1–5 означает «не применимо».''','Обзор и CSV')
code(r'''
all_summary4=[variant_summary4(n) for n in 1:30]
all_perseed4=[r for c in 1:5 for k in 1:6 for r in perseed4(c,k)]
headers4=collect(keys(first(all_perseed4)))
csv4("per_seed.csv",headers4,[Tuple(r) for r in all_perseed4])
summary_rows4=[(z.variant,z.ctx,z.fac,row...,z.iou) for z in all_summary4 for row in z.rows]
csv4("summary.csv",["variant","scene","operation","metric","base","s","after","delta","ratio","stat_significant","iou_after"],summary_rows4)
showmd4(mdtable4(["Вариант","Операция","PSNR до","PSNR после","Δ дБ","Класс"],[(z.variant,OPNAMES4[z.fac],@sprintf("%.3f",z.rows[1][2]),@sprintf("%.3f",z.rows[1][4]),@sprintf("%+.3f",z.rows[1][5]),class4(z.rows[1][5])) for z in all_summary4]))
''','Выполнение 30 сочетаний')
md('''## 8 Вывод и ограничения

Вывод ниже формируется по фактическому результату выполнения. Учебный критерий `2s` оценивает отношение сдвига к разбросу базовой метрики, а практический критерий оценивает пользу по PSNR относительно эталона. Рост энергии границ может означать усиление шума; её снижение — как подавление шума, так и размытие полезного контура. PSNR не заменяет визуальный осмотр.''','Интерпретация')
code(r'''
zmain4=all_summary4[3]
dmain4=zmain4.rows[1][5]
fmt4(x)=@sprintf("%.4f",x)
hypothesis_result4=dmain4<0 ? "подтверждена" : "не подтверждена"
conclusion4="## Вывод по варианту 3\n\n"*
"Средний PSNR: $(fmt4(zmain4.rows[1][2])) → $(fmt4(zmain4.rows[1][4])) дБ; Δ=$(fmt4(dmain4)) дБ. По заранее записанному допуску ±1 дБ операция **$(class4(dmain4))** для данной сцены.\n\n"*
"Гипотеза о снижении PSNR $hypothesis_result4. Энергия границ: $(zmain4.rows[2][2]) → $(zmain4.rows[2][4]); контраст: $(zmain4.rows[3][2]) → $(zmain4.rows[3][4]).\n\n"*
"При порогах 0.5, 1 и 2 дБ классификации: $(class4(dmain4,0.5)), $(class4(dmain4,1.0)), $(class4(dmain4,2.0)). Соседняя сцена 2: ΔPSNR=$(all_summary4[9].rows[1][5]) дБ, $(class4(all_summary4[9].rows[1][5])).\n\n"*
"Вывод ограничен синтетической сценой 128×128, пятью реализациями шума, выбранными параметрами фильтра и продолжением крайних значений. Seed не создаёт новую геометрию сцены. Для переноса вывода нужны разные реальные сцены и известные эталоны; на следующих экспериментах полезны больший набор seed и дополнительные метрики структуры."
showmd4(conclusion4)
write(joinpath(LR04_OUT,"conclusion.md"),conclusion4)
''','Автоматический вывод')
md('''## 9 Контрольные вопросы

1. При σₙ=0.05 оценка PSNR равна −20log10(0.05)=26.02 дБ; при 0.10 — 20 дБ: удвоение шума уменьшает PSNR примерно на 6.02 дБ.
2. Гаусс придаёт ближайшим пикселям больший вес. Рост σ расширяет сглаживание и размывает границы; сравнение с усреднением зависит от размеров ядер.
3. Ошибка после сглаживания включает остаточный шум и искажение деталей. При слабом шуме потери на границах могут превысить выигрыш, при сильном — наоборот.
4. Эталон Собеля получают из чистой сцены. Карты сравнивают при одной нормировке на максимум чистого градиента; отдельная нормировка каждой карты скрыла бы различие амплитуд.
5. Предварительное сглаживание подавляет ложные шумовые границы, но может ослабить настоящие; энергия границ обычно снижается.
6. Открытие — эрозия, затем дилатация; удаляет мелкие выступы и включения. Закрытие — дилатация, затем эрозия; заполняет мелкие отверстия и разрывы. Результат зависит от структурного элемента.
7. Объединение содержит 3000+3200−2900=3300 пикселей; IoU=2900/3300≈0.8788.
8. При фиксированной геометрии меняется лишь шум, а метрики усредняют много пикселей: s мал. Поэтому критерий 2s часто срабатывает и не показывает пользу операции.
9. Увеличить число seed, проверить несколько сцен и уровней шума, заранее обосновать допуск, использовать PSNR совместно с визуальной оценкой и метриками структуры. Один рост числа seed не устраняет ограничение одной сцены.
10. Записать среду, версии языка и библиотек, хеши исходников, размер, параметры сцены, seed, эталон, параметры операции, обработку краёв, структурный элемент, метрики и практический допуск.
''','Ответы на вопросы')
md('''## 10 Паспорт и артефакты

Ниже сохраняются фактические версии, хеши, параметры и таблицы. Источники: предоставленные методичка и библиотеки; [документация WorkspaceArray](https://engee.com/helpcenter/stable/ru/guide/workspacearray.html); собственные результаты запуска. Метрики считаются по Float64; файлы `.f64` записаны little-endian по столбцам Julia, PNG квантованы до 8 бит только для просмотра. Библиотеки преподавателя не изменяются.''','Паспорт')
code(r'''
@assert all(isfinite,row[j]) for row in [] for j in []) # заменено ниже явными проверками
''','Проверка результатов')
# Последнюю ячейку задаём без неоднозначных синтаксических сокращений.
cells[-1]['source']=r'''
@assert length(all_perseed4)==150
@assert length(all_summary4)==30
@assert all(all(isfinite,row[2:6]) for z in all_summary4 for row in z.rows)
@assert DEMO_MATCH4
@assert isapprox(mean(r.psnr_after for r in main_series4),zmain4.rows[1][4];atol=1e-10)
passport4=Dict("Engee"=>"26.9.2-H4","status"=>"executed","date"=>string(now()),"started_at"=>LR04_STARTED,"student"=>"Власюк Данил Витальевич","group"=>"Т26ИИКТ-МИК11","variant"=>3,"julia"=>string(VERSION),"platform"=>string(Sys.MACHINE),"Images"=>string(pkgversion(Images)),"seeds"=>collect(SEEDS4),"size"=>[128,128],"noise"=>0.02,"bg"=>[0.1,0.4],"disc"=>0.75,"checker"=>0,"gaussian_sigma"=>3,"border"=>"replicate","practical_threshold_db"=>1.0,"scene_sha256"=>SHA_SCENE4,"demo_match"=>DEMO_MATCH4,"library03_sha256"=>bytes2hex(sha256(read("lab03_lib.jl"))),"library04_sha256"=>bytes2hex(sha256(read("lab04_lib.jl"))),"hypothesis_sha256"=>bytes2hex(sha256(read("hypothesis.md"))),"float64_order"=>"Julia column-major little-endian","main_delta_psnr"=>dmain4,"main_class"=>class4(dmain4))
open(joinpath(LR04_OUT,"passport.toml"),"w") do io;TOML.print(io,passport4);end
open(joinpath(LR04_OUT,"versioninfo.txt"),"w") do io;versioninfo(io);end
passport_md4="# Паспорт эксперимента ЛР4 вариант 3\n\n"*join(["- **$k:** $v" for (k,v) in sort(collect(passport4);by=first)],"\n")
write(joinpath(LR04_OUT,"passport.md"),passport_md4)
showmd4(passport_md4)
Tar.create(LR04_OUT,joinpath(LR04_ROOT,"LR04_variant3_results.tar"))
println("ALL CHECKS PASS; COMPLETE ",now(),"; ARCHIVE ",joinpath(LR04_ROOT,"LR04_variant3_results.tar"))
'''.strip().splitlines(keepends=True)
nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Julia','language':'julia','name':'julia'},'language_info':{'file_extension':'.jl','name':'julia'},'engee':{}},'cells':cells}
prepared=R/'notebooks/prepared'
prepared.mkdir(parents=True,exist_ok=True)
for suffix in ['ngscript','ipynb']:
    (prepared/f'LR04_3.{suffix}').write_text(json.dumps(nb,ensure_ascii=False,indent=2)+'\n')
print(f'Prepared {len(cells)} cells, {sum(c["cell_type"]=="code" for c in cells)} code cells; no execution outputs fabricated')
