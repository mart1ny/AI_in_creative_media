# Исполненные ячейки ЛР4 варианта 3. Engee, Julia 1.12.4.

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

demo4=variant_summary4(1)
expected4=[(33.982103137714965,0.07450305641014086,29.19575338868147,-4.786349749033494),
(0.01692548814288977,0.00012750148456890567,0.008424262473284544,-0.008501225669605225),
(0.20774642267754806,0.00017156629178605263,0.20065402164009138,-0.007092401037456675)]
DEMO_MATCH4=all(isapprox(demo4.rows[i][j+1],expected4[i][j];atol=1e-10,rtol=0) for i in 1:3,j in 1:4)
println("MATCH_DEMO=",DEMO_MATCH4)
@assert DEMO_MATCH4
showmd4(summarytable4(demo4))

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

a4_1,b4_1,ref4_1=pair4(x4,clean_scene4,1)
z4_1=variant_summary4(1)
showmd4("**"*OPNAMES4[1]*"**\n\n"*summarytable4(z4_1))
println("ΔPSNR=",z4_1.rows[1][5]," дБ; операция ",class4(z4_1.rows[1][5]))
saveimage4("op1_result_seed101",a4_1)
saveimage4("op1_base_seed101",b4_1)
saveimage4("op1_reference",ref4_1)
display(Gray{N0f8}.(repeat(hcat(b4_1,a4_1,ref4_1),inner=(2,2))))

a4_2,b4_2,ref4_2=pair4(x4,clean_scene4,2)
z4_2=variant_summary4(2)
showmd4("**"*OPNAMES4[2]*"**\n\n"*summarytable4(z4_2))
println("ΔPSNR=",z4_2.rows[1][5]," дБ; операция ",class4(z4_2.rows[1][5]))
saveimage4("op2_result_seed101",a4_2)
saveimage4("op2_base_seed101",b4_2)
saveimage4("op2_reference",ref4_2)
display(Gray{N0f8}.(repeat(hcat(b4_2,a4_2,ref4_2),inner=(2,2))))

a4_3,b4_3,ref4_3=pair4(x4,clean_scene4,3)
z4_3=variant_summary4(3)
showmd4("**"*OPNAMES4[3]*"**\n\n"*summarytable4(z4_3))
println("ΔPSNR=",z4_3.rows[1][5]," дБ; операция ",class4(z4_3.rows[1][5]))
saveimage4("op3_result_seed101",a4_3)
saveimage4("op3_base_seed101",b4_3)
saveimage4("op3_reference",ref4_3)
display(Gray{N0f8}.(repeat(hcat(b4_3,a4_3,ref4_3),inner=(2,2))))

a4_4,b4_4,ref4_4=pair4(x4,clean_scene4,4)
z4_4=variant_summary4(4)
showmd4("**"*OPNAMES4[4]*"**\n\n"*summarytable4(z4_4))
println("ΔPSNR=",z4_4.rows[1][5]," дБ; операция ",class4(z4_4.rows[1][5]))
saveimage4("op4_result_seed101",a4_4)
saveimage4("op4_base_seed101",b4_4)
saveimage4("op4_reference",ref4_4)
display(Gray{N0f8}.(repeat(hcat(b4_4,a4_4,ref4_4),inner=(2,2))))

a4_5,b4_5,ref4_5=pair4(x4,clean_scene4,5)
z4_5=variant_summary4(5)
showmd4("**"*OPNAMES4[5]*"**\n\n"*summarytable4(z4_5))
println("ΔPSNR=",z4_5.rows[1][5]," дБ; операция ",class4(z4_5.rows[1][5]))
saveimage4("op5_result_seed101",a4_5)
saveimage4("op5_base_seed101",b4_5)
saveimage4("op5_reference",ref4_5)
display(Gray{N0f8}.(repeat(hcat(b4_5,a4_5,ref4_5),inner=(2,2))))

a4_6,b4_6,ref4_6=pair4(x4,clean_scene4,6)
z4_6=variant_summary4(6)
showmd4("**"*OPNAMES4[6]*"**\n\n"*summarytable4(z4_6))
println("ΔPSNR=",z4_6.rows[1][5]," дБ; операция ",class4(z4_6.rows[1][5]))
saveimage4("op6_result_seed101",a4_6)
saveimage4("op6_base_seed101",b4_6)
saveimage4("op6_reference",ref4_6)
display(Gray{N0f8}.(repeat(hcat(b4_6,a4_6,ref4_6),inner=(2,2))))
println("Средний IoU после открытия=",z4_6.iou)

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

all_summary4=[variant_summary4(n) for n in 1:30]
all_perseed4=[r for c in 1:5 for k in 1:6 for r in perseed4(c,k)]
headers4=collect(keys(first(all_perseed4)))
csv4("per_seed.csv",headers4,[Tuple(r) for r in all_perseed4])
summary_rows4=[(z.variant,z.ctx,z.fac,row...,z.iou) for z in all_summary4 for row in z.rows]
csv4("summary.csv",["variant","scene","operation","metric","base","s","after","delta","ratio","stat_significant","iou_after"],summary_rows4)
showmd4(mdtable4(["Вариант","Операция","PSNR до","PSNR после","Δ дБ","Класс"],[(z.variant,OPNAMES4[z.fac],@sprintf("%.3f",z.rows[1][2]),@sprintf("%.3f",z.rows[1][4]),@sprintf("%+.3f",z.rows[1][5]),class4(z.rows[1][5])) for z in all_summary4]))

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
