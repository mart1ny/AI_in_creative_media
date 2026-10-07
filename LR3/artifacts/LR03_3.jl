# ЛР 3, вариант 3. Запуск: include("LR03_3.jl")
using Images, Random, Statistics, SHA, Plots, TOML, Tar, Dates, InteractiveUtils
include(joinpath(@__DIR__, "lab03_lib.jl"))
const LR03_OUT = joinpath(@__DIR__, "artifacts")
mkpath(LR03_OUT)
println("START ", now(), " Julia ", VERSION)
versioninfo()
img = make_scene(101; scene_preset(1)...)
g = luma_images(img)
g_manual = luma_manual(img)
h2 = apply_factor(g, 2)
h4 = apply_factor(g, 3)
props = describe_image(img)
sha_first = array_sha(g)
sha_repeat = array_sha(luma_images(make_scene(101; scene_preset(1)...)))
@assert sha_first == sha_repeat
@assert maximum(abs.(g .- g_manual)) < 1e-7
@assert size(imresize(g, ratio=0.25)) == (32,32)
@assert size(h4) == size(g)
@assert all(0 .<= h4 .<= 1)
println("DESCRIPTION ", props)
println("MAXDIFF ", maximum(abs.(g .- g_manual)))
println("SHA_FIRST ", sha_first, "\nSHA_REPEAT ", sha_repeat)
save(joinpath(LR03_OUT,"scene_rgb_seed101.png"), RGB{N0f8}.(img))
save(joinpath(LR03_OUT,"gray_before_seed101.png"), Gray{N0f8}.(g))
save(joinpath(LR03_OUT,"gray_after_x2_seed101.png"), Gray{N0f8}.(h2))
save(joinpath(LR03_OUT,"gray_after_x4_seed101.png"), Gray{N0f8}.(h4))
save(joinpath(LR03_OUT,"gray_small32_seed101.png"), Gray{N0f8}.(imresize(g,ratio=0.25)))
# Float64 — для пересчёта без дополнительного квантования PNG; порядок Julia column-major.
for (name,a) in [("before",g),("after_x2",h2),("after_x4",h4)]
    open(joinpath(LR03_OUT,name*"_seed101.f64"),"w") do io
        write(io, vec(a))
    end
end
centers = ((1:32) .- 0.5) ./ 32
p1=bar(centers,hist_counts(g,32);bar_width=1/32,xlabel="Brightness",ylabel="Pixels",title="Before",legend=false,xlims=(0,1),ylims=(0,5500))
p2=bar(centers,hist_counts(h4,32);bar_width=1/32,xlabel="Brightness",ylabel="Pixels",title="Resize 128 -> 32 -> 128",legend=false,xlims=(0,1),ylims=(0,5500))
p=plot(p1,p2;layout=(1,2),size=(1200,450))
savefig(p,joinpath(LR03_OUT,"histograms_before_after.png"))
open(joinpath(LR03_OUT,"histograms_seed101.csv"),"w") do io
 println(io,"bin,left,right,before,after_x2,after_x4")
 for k in 1:32
  println(io,join((k,(k-1)/32,k/32,hist_counts(g,32)[k],hist_counts(h2,32)[k],hist_counts(h4,32)[k]),","))
 end
end
# Основная серия и контроль без шума.
open(joinpath(LR03_OUT,"per_seed.csv"),"w") do io
 println(io,"noise,factor,seed,mean_before,contrast_before,entropy_before,mean_after,contrast_after,entropy_after,mse,psnr,sha_before,sha_after")
 for noise in (0.02,0.0), factor in (2,3), seed in 101:105
  a=luma_images(make_scene(seed; n=128,lo=0.15,hi=0.85,noise=noise,checker=0))
  b=apply_factor(a,factor); mb=metrics3(a); ma=metrics3(b)
  println(io,join((noise,factor,seed,mb.mean,mb.contrast,mb.entropy,ma.mean,ma.contrast,ma.entropy,mse(a,b),psnr_db(a,b),array_sha(a),array_sha(b)),","))
 end
end
open(joinpath(LR03_OUT,"summary.csv"),"w") do io
 println(io,"variant,metric,base,s,after,delta,ratio,stat_significant,relative_change,practical_significant")
 for v in (2,3)
  z=variant_summary(v)
  println("SUMMARY ", z)
  for row in z.rows
   m,b,s,a,d,r,stat=row
   println(io,join((v,m,b,s,a,d,r,stat,abs(d)/abs(b),abs(d)/abs(b)>0.05),","))
  end
 end
end
demo=variant_summary(1)
@assert isapprox(demo.psnr,34.594244830067446;atol=1e-10,rtol=0)
@assert startswith(sha_first,"50567c6b9e5e4ac1")
res=Dict("generated_at"=>string(now()),"julia"=>string(VERSION),"platform"=>string(Sys.MACHINE),"library_sha256"=>bytes2hex(sha256(read(joinpath(@__DIR__,"lab03_lib.jl")))),"size"=>collect(props.size),"eltype"=>props.eltype,"min"=>props.min,"max"=>props.max,"bytes"=>props.bytes,"luma_maxdiff"=>maximum(abs.(g .- g_manual)),"sha_first"=>sha_first,"sha_repeat"=>sha_repeat,"sha_equal"=>sha_first==sha_repeat,"psnr_x2"=>variant_summary(2).psnr,"psnr_x4"=>variant_summary(3).psnr,"demo_psnr"=>demo.psnr,"demo_verified"=>true,"package_versions"=>Dict(string(m)=>string(pkgversion(m)) for m in (Images,Plots)),"practical_relative_threshold"=>0.05,"practical_psnr_threshold_db"=>30.0)
open(joinpath(LR03_OUT,"environment_and_results.toml"),"w") do io; TOML.print(io,res); end
open(joinpath(LR03_OUT,"versioninfo.txt"),"w") do io; versioninfo(io); end
cp(joinpath(@__DIR__,"LR03_3.jl"),joinpath(LR03_OUT,"LR03_3.jl");force=true)
cp(joinpath(@__DIR__,"lab03_lib.jl"),joinpath(LR03_OUT,"lab03_lib.jl");force=true)
Tar.create(LR03_OUT,joinpath(@__DIR__,"LR03_variant3_results.tar"))
println("ALL CHECKS PASS; ARCHIVE: ",joinpath(@__DIR__,"LR03_variant3_results.tar"))
