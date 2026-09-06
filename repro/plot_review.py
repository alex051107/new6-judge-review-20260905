"""Render review figures from the frozen ledger and weights; never scores a workbook."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/assets'
OUT.mkdir(parents=True, exist_ok=True)
for f in [Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')]:
    if f.exists():
        fm.fontManager.addfont(str(f))
        plt.rcParams['font.family'] = fm.FontProperties(fname=str(f)).get_name()
plt.rcParams.update({'font.size': 12, 'axes.unicode_minus': False, 'svg.fonttype': 'path'})
INK, MUTED, BG = '#172e3b', '#5d6d77', '#f7f9fa'
COLORS = ['#216b82','#438ca0','#63a7b4','#94c4c9','#a17d4d','#caab7e','#6f79a8','#aaaec9']

def save(fig, name):
    fig.savefig(OUT/(name+'.png'), dpi=170, bbox_inches='tight', facecolor=fig.get_facecolor())
    fig.savefig(OUT/(name+'.svg'), bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)

fig, ax = plt.subplots(figsize=(13,7.2));fig.patch.set_facecolor(BG)
ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
ax.text(.02,.96,'NEW6 测什么：让下一位同事接得住这份工作簿',fontsize=22,weight='bold',color=INK)
ax.text(.02,.90,'以下用常见单步操作作对比，说明任务范围；不代表对其他评测的实测结论。',color=MUTED,fontsize=11)
rows=[('A · 专业模型','填出当前估值或 GDP','恢复计算关系与年度时序','预测 → 再投资 / 资本 → 现金流 / 产出 → 结果','A1 / A2：改假设后，完整结果正确更新'),
      ('B · 完整分析','汇总销售额或筛出一份名单','把同一批对象算全、解释清楚','明细 / 地区 → 口径 → 汇总 / 名单 → 图文与证据','B1 / B2：接受正确静态分析，重点是跨层一致'),
      ('C · 文档规则','把 PDF 里的金额抄入 Excel','保留层级、限定语和计价规则','原文事实 → 有效范围 / 边界 → 工作计算 / 报价','C1 / C2：改价格、重量或区域后，结果仍可核对')]
for i,(track,basic,main,chain,use) in enumerate(rows):
    y=.70-i*.255
    for x,w,color in [(.02,.26,'#e9eef1'),(.32,.66,'#ffffff')]:
        ax.add_patch(FancyBboxPatch((x,y-.105),w,.205,boxstyle='round,pad=0.012',facecolor=color,edgecolor='none'))
    ax.text(.04,y+.053,track,weight='bold',color=INK,fontsize=14)
    ax.text(.04,y-.018,basic,color=MUTED,fontsize=12)
    ax.annotate('',xy=(.316,y),xytext=(.288,y),arrowprops={'arrowstyle':'->','color':'#74909a','lw':2})
    ax.text(.345,y+.052,main,weight='bold',color='#216b82',fontsize=15)
    ax.text(.345,y-.012,chain,color=INK,fontsize=12)
    ax.text(.345,y-.067,use,color=MUTED,fontsize=11)
ax.text(.02,.016,'基础 / 重点 = 业务关注的层次     静态 / 动态 = 取得证据的方式；两组概念分别说明。',color=MUTED,fontsize=11)
save(fig,'abilities')

release=json.loads((ROOT/'release.json').read_text())
labels={
 'A1':['源值','年度预测','现金流与估值','输入变化','保护','比较结论'],
 'A2':['初始输入','年度递推','GDP结果','输入变化','保护','图文引用'],
 'B1':['完整记录','交易政策','发票','国家汇总','图文','保护追溯','贡献桥','SKU支撑'],
 'B2':['来源与口径','完整名单','支撑数值','名单变化与图文','保护追溯'],
 'C1':['原文范围','报价版本','成本计算','差额','输入变化','追溯'],
 'C2':['完整价格网格','单位边界','当前报价','输入变化','保护','追溯']}
fig, axs=plt.subplots(6,1,figsize=(13,8.6));fig.patch.set_facecolor(BG)
fig.suptitle('六题主配重：每项按实际业务事实给部分信用',x=.025,y=.99,ha='left',fontsize=21,color=INK,weight='bold')
fig.text(.025,.941,'正式计分权重：确定性程序 100% · LLM / 视觉模型 0%   |   每题合计 100%，未增加新分组或新权重',color=MUTED,fontsize=11)
for ax,(task,t) in zip(axs,release['tasks'].items()):
    ax.set_facecolor(BG);left=0;weights=list(t['primary_weights'].values())
    for i,w in enumerate(weights):
        ax.barh(0,w,left=left,height=.40,color=COLORS[i],edgecolor=BG,linewidth=2)
        ax.text(left+w/2,0,str(w),ha='center',va='center',color='white' if i in [0,1,4,6] else INK,weight='bold',fontsize=12)
        left+=w
    ax.text(-3,0,task,ha='right',va='center',color=INK,weight='bold',fontsize=15)
    ax.text(0,-.39,'  ·  '.join(f'{n} {w}%' for n,w in zip(labels[task],weights)),color=MUTED,fontsize=10)
    ax.set(xlim=(-1,101),ylim=(-.65,.4));ax.axis('off')
fig.subplots_adjust(top=.90,left=.065,right=.985,hspace=.15,bottom=.02)
save(fig,'judge_weights')

rows=json.loads((ROOT/'results/trials.json').read_text())
systems=['codex','claude','qwen'];names={'codex':'GPT-5.6 sol','claude':'Opus 5','qwen':'Qwen 3.8'}
colors={'codex':'#216b82','claude':'#8864aa','qwen':'#a27b42'}
flagged={'A1-claude-R03','C2-codex-R02','C2-codex-R08'}
fig,axs=plt.subplots(3,2,figsize=(13,8.7));fig.patch.set_facecolor(BG)
fig.suptitle('已有答卷的主方案分数',x=.035,y=.995,ha='left',fontsize=22,weight='bold',color=INK)
fig.text(.035,.946,'每点一份已评分原件；按题展示，不把不同配置合成均分。虚线为 70 分通过线。',fontsize=11,color=MUTED)
for ax,task in zip(axs.flat,release['tasks']):
    ax.set_facecolor('white');ax.axvline(70,color='#b9c2c8',lw=1,ls='--')
    for i,sys in enumerate(systems):
        rr=sorted([x for x in rows if x['task']==task and x['system']==sys and x['status']=='SCORED'],key=lambda x:x['id'])
        for j,r in enumerate(rr):
            yy=i+(j-(len(rr)-1)/2)*.047
            ax.scatter(float(r['score_decimal'])*100,yy,s=55,facecolors='white' if r['id'] in flagged else colors[sys],edgecolors=colors[sys],linewidths=1.7,zorder=3)
        ax.text(103,i,f'n={len(rr)}',va='center',fontsize=10,color=MUTED)
    ax.set_yticks(range(3),[names[x] for x in systems]);ax.invert_yaxis();ax.set_ylim(2.55,-.6)
    ax.set_xlim(0,114);ax.set_xticks([0,25,50,70,100]);ax.tick_params(length=0,labelsize=10,pad=6)
    ax.set_title(task,loc='left',weight='bold',color=INK,pad=9)
    ax.spines[['top','right','left']].set_visible(False);ax.spines['bottom'].set_color('#d5dde0')
    ax.grid(axis='x',color='#eef1f3',zorder=0)
fig.text(.035,.032,'空心点：已标记评分解释待复核的原件。未交付与待判未画成业务低分；Qwen 当前仅 C2 有 2 份可评分原件。',fontsize=10,color=MUTED)
fig.text(.035,.005,'来源：results/trials.json · 固定发布 new6-final-review-20260906-v1 · 数值为原回执，未在此重评',fontsize=10,color=MUTED)
fig.subplots_adjust(top=.88,left=.125,right=.97,bottom=.11,hspace=.53,wspace=.35)
save(fig,'score_distribution')
print('Generated 3 figures from frozen release inputs.')
