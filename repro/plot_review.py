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
    svg = OUT / (name + '.svg')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    plt.close(fig)

fig, ax = plt.subplots(figsize=(14,10.1));fig.patch.set_facecolor(BG)
ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
ax.text(.02,.965,'从单步操作，到一份经得起核对的业务交付',fontsize=23,weight='bold',color=INK)
ax.text(.02,.92,'NEW6 在前 15 题的基础上重新选材：把业务要求、能力目标与核对方式放到同一道题里。',color=MUTED,fontsize=12)
ax.text(.02,.866,'接到的工作',color=MUTED,fontsize=12)
ax.text(.24,.866,'交付中必须成立的关系',color=MUTED,fontsize=12)
ax.text(.78,.866,'怎样核对',color=MUTED,fontsize=12)
rows=[
 ('A1  估值审阅','年度经营预测','再投资与现金流','估值与情景差额','改增长率或折现率\n逐年检查结果更新'),
 ('A2  增长情景','投资目标与过渡年','资本逐年积累','GDP及人均结果','改投资路径\n核对年度递推'),
 ('B1  零售复盘','完整交易与贷项','发票 / 国家 / SKU','两月净额与贡献','从汇总追到原交易\n接受正确静态分析'),
 ('B2  统计简报','三期可比地区数据','连续两段变化','名单与进出解释','逐地区核对条件\n接受正确静态分析'),
 ('C1  工程成本','原估算与修订往来','有效报价与费用基数','当前成本与调节','改报价或费率\n检查总额与调节'),
 ('C2  包裹报价','服务 / 重量 / 分区','完整价格与边界规则','逐件报价与合计','改重量或分区\n检查报价与范围')]
for i,(task,a,b,c,check) in enumerate(rows):
 y=.765-i*.127; color=['#216b82','#216b82','#626d9c','#626d9c','#977444','#977444'][i]
 ax.add_patch(FancyBboxPatch((.015,y-.052),.97,.102,boxstyle='round,pad=0.01',facecolor='white',edgecolor='#e3e9ec'))
 ax.text(.03,y,task,fontsize=14,weight='bold',color=color,va='center')
 for x,txt in zip([.245,.425,.605],[a,b,c]):
  ax.text(x,y,txt,fontsize=11.5,color=INK,va='center')
 for x in [.403,.584]:
  ax.annotate('',xy=(x+.013,y),xytext=(x-.011,y),arrowprops={'arrowstyle':'->','color':color,'lw':1.4})
 ax.text(.795,y,check,fontsize=11.5,color=color,va='center',linespacing=1.6)
ax.text(.025,.031,'A 看计算关系与年度时序    ·    B 看对象、口径和证据一致    ·    C 看文档条件如何进入计算',fontsize=13,color=INK)
ax.text(.025,.001,'对比单步操作用于解释任务范围；动态更新按实际业务要求检查，不是六题统一标签。',fontsize=11,color=MUTED)
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

# Numeric companion table: preserve score range and count without merging means.
systems = ['codex', 'claude', 'qwen']
lines = ['# 已评分原件的分数范围', '', '表中为已评分原件的最低—最高分，满分100，括号内为份数；只有一份时列单个分数。它展示已有分数跨度，不是均分或pass@8。未交付、待判和运行失败不进入这个范围；完整配置分组与均分见结果附件。', '', '| 题目 | GPT-5.6 sol | Opus 5 | Qwen 3.8 |', '|---|---|---|---|']
for task in release['tasks']:
    cells = [task]
    for sys in systems:
        vals = [float(r['score_decimal']) * 100 for r in rows if r['task'] == task and r['system'] == sys and r['status'] == 'SCORED']
        cells.append((f'{min(vals):.2f}–{max(vals):.2f}（{len(vals)}份）' if len(vals)>1 else f'{vals[0]:.2f}（1份）') if vals else '暂无可评分答卷')
    lines.append('| ' + ' | '.join(cells) + ' |')
(ROOT / 'results/SCORE_RANGES.md').write_text('\n'.join(lines) + '\n')
