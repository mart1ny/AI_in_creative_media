"""Write numerical report sections from actual downloaded artifacts only."""
from pathlib import Path
import json
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'artifacts'
def read(f):return json.loads((A/f).read_text())
cl=read('classification.json');rr={r['metric']:r for r in cl};diag=read('diagnostic.json');per=read('r2_per_factor.json');controls=read('ae_vae_controls.json');collapse=read('collapse_records.json')
factors={cond:{k:float(np.mean([r[k] for r in per if r['condition']==cond])) for k in ['r2_x','r2_y','r2_radius']} for cond in ['A','B']}
deltas={k:factors['B'][k]-factors['A'][k] for k in factors['A']}
lines=['# Анализ диагностики']
for cond in ['A','B']:
 rows=[r for r in diag if r['condition']==cond]
 lines.append(f"Режим {cond}: активные оси по seed101–105: "+', '.join(f"{r['active']}/{r['d']}" for r in rows)+'.')
lines.append('По факторам сцены (средние R² по пяти seed): '+ '; '.join(f"{k}: A={factors['A'][k]:.5f}, B={factors['B'][k]:.5f}, Δ={deltas[k]:+.5f}" for k in factors['A'])+'.')
worst=min(deltas,key=deltas.get)
lines.append('Наибольшее падение линейной восстанавливаемости имеет '+{'r2_x':'координата x','r2_y':'координата y','r2_radius':'радиус'}[worst]+'. '+('Это согласуется с ожиданием о потере информации о радиусе.' if worst=='r2_radius' else 'Ожидание, что сильнее всего пострадает радиус, не подтверждается этим показателем.'))
lines.append('R² измеряет линейное восстановление факторов, а не всю доступную информацию. Низкий R² радиуса не доказывает его полного отсутствия в нелинейном коде. Активные оси не обязательно совпадают с независимыми семантическими факторами; две оси могут смешивать положение и радиус.')
(R/'reports/diagnostic_analysis.md').write_text('\n\n'.join(lines)+'\n')
data=np.load(A/'dataset.npz');mean=data['train'].mean(0,keepdims=True,dtype=np.float64);mse=((data['test'].astype(float)-mean)**2).reshape(1024,-1).mean(1);baseline=float(np.mean(10*np.log10(1/mse)))
(R/'reports/mean_image_baseline.json').write_text(json.dumps(dict(psnr=baseline,provenance='Independent NumPy float64 recomputation from LR8 train mean and held-out test images'),indent=2)+'\n')
c0,c1=collapse[:5],collapse[5:];lo=min(c0,key=lambda r:r['metrics']['recon']);paired=next(r for r in c1 if r['seed']==lo['seed'])
text=f'''# Анализ схлопывания

Без разогрева худший seed {lo['seed']} дал реконструкцию {lo['metrics']['recon']:.4f} дБ; с warmup10 тот же seed дал {paired['metrics']['recon']:.4f} дБ. Для ориентира средняя train-картинка, заново оценённая по данным ЛР8 на test, даёт {baseline:.4f} дБ. В этой диагностике провал без warmup близок к тривиальному ответу, а разогрев его устранил в проверенной паре.

Это наблюдение согласуется с описанным в методичке схлопыванием. Сам по себе низкий PSNR не является исчерпывающим доказательством posterior collapse: для дополнительной серии сохранены метрики, но полные распределения каждого такого запуска отдельно не исследуются. Гарантии, что warmup исключает все будущие провалы, не даются. Новая сессия отдельно не проверялась.
'''
(R/'reports/collapse_analysis.md').write_text(text)
recon_ok=rr['recon']['delta'] < -1;r2_ok=rr['r2']['delta'] < -.05
lines=['# Итоговый вывод',f"Ожидание падения реконструкции более 1 дБ {'подтвердилось' if recon_ok else 'не подтвердилось'}, ожидание падения среднего R² более 0,05 {'подтвердилось' if r2_ok else 'не подтвердилось'} в данной серии. Менялось только d: 8→2; β, обучение, данные, seed и методы оценки сохранены."]
for metric in ['recon','interp','sample','r2']:
 r=rr[metric];lines.append(f"{metric}: A={r['A']:.5f}, B={r['B']:.5f}, Δ={r['delta']:+.5f}; |Δ|/s_A={r['ratio']:.3f}. Класс по допуску {r['tolerance']:.2f}: «{r['label']}». Критерий 2s {'выполнен' if r['over_2s'] else 'не выполнен'}; {'расходится' if r['criteria_disagree'] else 'согласуется'} с признаком превышения практического допуска.")
lines.append('Узкое место изменяет компромисс между точностью конкретной сцены и свойствами латентного пространства. Не требуется, чтобы все четыре метрики ухудшались одновременно. Среднее по seed показывает картину этой серии, а не универсальное свойство любого VAE.')
lines.append(f"Диагностика AE/VAE seed101: сэмплы AE β=0 имеют PSNR {controls[0]['metrics']['sample']:.4f}, VAE β=1 — {controls[1]['metrics']['sample']:.4f}. Это показывает практический смысл согласования с prior в этих условиях. Метрика ближайшего соседа не измеряет разнообразия и не исключает повторяющиеся сэмплы.")
lines.append('Для объяснения потерь используются R² каждого фактора и визуальный путь, но три порождающих фактора сами по себе не доказывают строгую минимальную размерность дискретных изображений. Линейная регрессия не равна полной оценке информации. Пять seed, один синтетический набор и одна архитектура не позволяют переносить результат на фотографии. Критерий 2s не является формальным тестом. CPU-обучение и время не обещают побитовой воспроизводимости; новый сеанс отдельно не проверен.')
(R/'reports/final_conclusion.md').write_text('\n\n'.join(lines)+'\n')
print('Report sections generated from actual values')
