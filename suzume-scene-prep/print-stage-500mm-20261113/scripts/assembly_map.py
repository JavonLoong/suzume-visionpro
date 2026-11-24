"""Actual, dimensioned assembly and packing diagrams, generated from STL meshes."""
import json,sys
from pathlib import Path
import numpy as np,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as PlotPath
from matplotlib.patches import PathPatch,Circle,Rectangle
from matplotlib.font_manager import FontProperties
R=Path(__file__).resolve().parents[1];A=R/'analysis'
sys.path.insert(0,str(R.parent/'print-400mm-20261030/.deps'));import manifold3d as mf
font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams['font.family']=font.get_name();plt.rcParams['axes.unicode_minus']=False
data=json.loads((A/'slim_manifest.json').read_text(encoding='utf8'));pack=json.loads((A/'packed_manifest.json').read_text(encoding='utf8'))
colors=['#bcdce7','#c5dfce','#ead7ad','#d3cbe4','#e8c5c2','#bfdacf','#cbd7e7']
def manifold(mesh):return mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices,dtype=np.float64),np.asarray(mesh.faces,dtype=np.uint64)))
def path(polys):
    ps=[]
    for poly in polys:
        q=np.vstack([poly,poly[0]]);codes=[PlotPath.MOVETO]+[PlotPath.LINETO]*(len(q)-2)+[PlotPath.CLOSEPOLY];ps.append(PlotPath(q,codes))
    return PlotPath.make_compound_path(*ps)
fig,ax=plt.subplots(figsize=(9,9));fig.patch.set_facecolor('#f8fafb');ax.set_facecolor('#f8fafb')
for n,row in enumerate(pack[:7]):
    for p in row['placements']:
        if not p['id'].startswith('薄底板'):continue
        d=np.load(A/'assembly'/(p['id']+'.npz'));m=trimesh.Trimesh(d['vertices'],d['faces'],process=False)
        polys=manifold(m).slice(7.7).to_polygons();ax.add_patch(PathPatch(path(polys),facecolor=colors[n],edgecolor='#48606c',lw=.55))
        rr,cc=[int(i) for i in p['id'][-2:]];x=[-154,0,154][cc-1];y=[-154,0,154][rr-1]
        if rr==2 and cc==2:y=-50
        ax.text(x,y,f'板 {rr}{cc}\n第 {n+1} 盘',ha='center',va='center',fontsize=12,color='#203942',bbox=dict(boxstyle='round,pad=.25',facecolor='white',alpha=.92,edgecolor='none'))
ax.add_patch(Circle((0,0),200,fill=False,edgecolor='#536f78',ls=(0,(5,4)),lw=1.4));ax.text(0,205,'庭院外径 400 mm',ha='center',fontsize=11,color='#365b66',bbox=dict(fc='white',ec='none',alpha=.9))
ax.annotate('',(-250,-278),(250,-278),arrowprops=dict(arrowstyle='<->',color='#334c59',lw=1.1));ax.text(0,-272,'底座外径 500 mm',ha='center',fontsize=12,color='#243d48')
for x in (-250,250):ax.plot([x,x],[-255,-285],color='#334c59',lw=.8)
ax.annotate('',(200,0),(250,0),arrowprops=dict(arrowstyle='<->',color='#334c59',lw=1));ax.text(226,15,'50',ha='center',fontsize=10,color='#243d48')
ax.set_aspect('equal');ax.set_xlim(-285,285);ax.set_ylim(-298,285);ax.axis('off')
fig.suptitle('50 厘米底座 · 顶面装配图',fontsize=20,fontweight='bold',y=.98,color='#203942');fig.text(.5,.02,'同色底板来自同一盘；按凹槽位置装配。尺寸单位：毫米。',ha='center',fontsize=11,color='#435e68')
fig.tight_layout(rect=(0,.045,1,.95));fig.savefig(R/'50厘米装配图.png',dpi=170);plt.close(fig)
fig,axes=plt.subplots(2,4,figsize=(13,7.5));fig.patch.set_facecolor('#f8fafb')
for i,ax in enumerate(axes.flat):
    if i>=7:ax.axis('off');ax.text(.06,.87,'7 盘，共 9 块底板\n接缝条 12 件，脚垫 12 件\n每个 STL 打印一次\n\n保留原排布与 100% 尺寸',transform=ax.transAxes,va='top',fontsize=12,linespacing=1.55,color='#203942');continue
    m=trimesh.load(pack[i]['stl_path'],force='mesh');polys=manifold(m).project().to_polygons()
    ax.add_patch(Rectangle((0,0),256,256,fc='white',ec='#a8b8bf',lw=.8));ax.add_patch(Rectangle((0,0),18,28,fc='#edc5c5',ec='#bb7474',lw=.7))
    ax.add_patch(PathPatch(path(polys),facecolor=colors[i],edgecolor='#48606c',lw=.5));ax.set_xlim(-5,261);ax.set_ylim(-5,261);ax.set_aspect('equal');ax.axis('off');ax.set_title(f'底座{i+1}.stl',fontsize=13,color='#203942')
fig.suptitle('50 厘米底座 · 7 盘排布',fontsize=20,fontweight='bold',color='#203942');fig.text(.02,.015,'红色区域为前左禁区。已按 3 mm 边裙检查边界与零件间距。',fontsize=11,color='#435e68');fig.subplots_adjust(left=.025,right=.985,bottom=.09,top=.87,wspace=.16,hspace=.32);fig.savefig(R/'七盘排布.png',dpi=160);plt.close(fig)
print('ASSEMBLY_AND_PACKING_DIAGRAMS_COMPLETE')
