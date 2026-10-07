from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
R=Path(__file__).resolve().parents[1]; A=R/'artifacts'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,4,figsize=(12,3.5),layout='constrained')
for ax,name,title in zip(axs,['scene_rgb_seed101.png','gray_before_seed101.png','gray_after_x2_seed101.png','gray_after_x4_seed101.png'],['Исходная RGB','Яркость до','Уменьшение в 2 раза','Уменьшение в 4 раза']):
 ax.imshow(Image.open(A/name),cmap='gray',vmin=0,vmax=255,interpolation='nearest');ax.set_title(title);ax.set_axis_off()
fig.savefig(A/'comparison_scene.png',dpi=180);plt.close(fig)
h=list(csv.DictReader((A/'histograms_seed101.csv').open()))
fig,axs=plt.subplots(1,3,figsize=(12,3.6),layout='constrained',sharey=True)
for ax,key,title in zip(axs,['before','after_x2','after_x4'],['До воздействия','128 → 64 → 128','128 → 32 → 128']):
 x=[(float(r['left'])+float(r['right']))/2 for r in h]
 ax.bar(x,[int(r[key]) for r in h],width=1/32,color='#4a738c',edgecolor='white',linewidth=.5)
 ax.set_xlim(0,1);ax.set_ylim(0,4000);ax.set_xlabel('Яркость');ax.set_title(title);ax.grid(axis='y',alpha=.2)
axs[0].set_ylabel('Число пикселей')
fig.savefig(A/'histograms_comparison.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(10,3.7),layout='constrained')
for ax,name,title in zip(axs,['gray_before_seed101.png','gray_after_x2_seed101.png','gray_after_x4_seed101.png'],['До','После ×2','После ×4']):
 a=np.array(Image.open(A/name));ax.imshow(a[26:58,44:76],cmap='gray',vmin=0,vmax=255,interpolation='nearest');ax.set_axis_off();ax.set_title(title)
fig.savefig(A/'circle_edge_detail.png',dpi=180);plt.close(fig)
