"""Pairwise, offline task-grounded weight sweep; facts and penalties stay fixed."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import csv,json
HERE=Path(__file__).resolve().parent
FOCUS={
'P15-A-ENG-SIZING-001':(['R006','R007','R008','R012'],'约束下的设备选择与两种输入变化'),
'P15-A-FIN-DCF-001':(['R007','R008','R009','R010'],'估值桥、敏感性和输入变化传播'),
'P15-A-FIN-DEBUG-001':(['R002','R006','R009','R012'],'根因修复、局部性与传播'),
'P15-A-POLICY-EIA-001':(['R004','R005','R008','R009','R012'],'政策平衡、排放和情景传播（旧合同问题标记）'),
'P15-A-STAT-EXPERIMENT-001':(['R004','R005','R006','R010'],'配对推断、区间和结论一致性'),
'P15-B-FIN-RECON-001':(['R003','R004','R006','R007'],'匹配、批准调整、异常和闭合'),
'P15-B-HEALTH-REPORT-001':(['R003','R006','R007'],'数据支持的指标、报告和图表'),
'P15-B-OPS-CLEAN-JOIN-001':(['R002','R003','R007'],'清洗政策、连接身份与异常'),
'P15-B-PUBLIC-PIVOT-001':(['R003','R007','R009'],'原生源绑定、刷新与透视图关系'),
'P15-B-SALES-DISCOVERY-001':(['R002','R003','R005','R006'],'正确版本、记录范围与选择证据'),
'P15-C-INVOICE-001':(['R003','R005','R006','R007'],'行身份、应付关系与更新'),
'P15-C-PO-ADDENDUM-001':(['R003','R004','R007','R008'],'修订范围、保护未改项与前后证据'),
'P15-C-QUOTE-001':(['R003','R004','R005','R007'],'范围身份、包含排除与一致性'),
'P15-C-RECEIPTS-001':(['R002','R003','R004','R008'],'票据和明细身份、完整性与来源'),
'P15-C-STATEMENT-001':(['R003','R004','R006','R009'],'交易方向、完整性与余额来源闭合'),
'A1':(['R004'],'估值输入变化传播'),'A2':(['R004'],'投资目标和过渡年的情景传播'),
'B1':(['R007','R008'],'跨月贡献解释和SKU闭合'),'B2':(['R004','R005'],'旧简报更新与可复核'),
'C1':(['R005'],'会议改价后成本链更新'),'C2':(['R004'],'改请求后报价、选择与总额更新')}
def mean(x):return sum(x)/len(x) if x else None
def score(f,w):return max(F(0),min(F(1),sum(F(str(f[k]))*v for k,v in w.items())/100))
def weights(original,focus,target,p15):
 pos={k:v for k,v in original.items() if v>0};neg={k:v for k,v in original.items() if v<0};total=sum(pos.values());out={k:v*100/total for k,v in neg.items()}
 groups=[(set(focus),F(target))]
 if p15:groups += [({'R001'},F(2)),(set(pos)-set(focus)-{'R001'},F(98-target))]
 else:groups += [(set(pos)-set(focus),F(100-target))]
 for keys,budget in groups:
  old=sum(pos[k] for k in keys);assert old>0
  out.update({k:pos[k]*budget/old for k in keys})
 assert sum(v for v in out.values() if v>0)==100
 return out
def outjson(x):return float(x) if isinstance(x,F) else x

def run():
 data=json.loads((HERE/'frozen_facts.json').read_text());allrows=[];summaries=[];configs={};errors=[];checks=Counter()
 for dataset,d in data.items():
  for task,c in d['configs'].items():
   original={k:F(str(v)) for k,v in c['weights'].items()};total=sum(v for v in original.values() if v>0);profiles={'original':{k:v*100/total for k,v in original.items()}}
   for target in (50,60,70):profiles[f'focus_{target}']=weights(original,FOCUS[task][0],target,task.startswith('P15'))
   for name,w in profiles.items():
    assert score({k:int(v>0) for k,v in w.items()},w)==1
    assert score({k:0 for k in w},w)==0
    assert all(w[k]>0 for k in FOCUS[task][0]);checks['weight_profiles']+=1
   configs[dataset+'/'+task]={'focus':FOCUS[task][0],'ability':FOCUS[task][1],'profiles':profiles,'descriptions':c['descriptions']}
  for r in d['rows']:
   row={**r,'dataset':dataset,'scores':None}
   if r['status'].startswith('SCORED'):
    p=configs[dataset+'/'+r['task_id']]['profiles'];f=r['facts'];assert set(f)==set(p['original']);assert all(0<=F(str(v))<=1 for v in f.values())
    row['scores']={k:score(f,w) for k,w in p.items()}
    assert abs(row['scores']['original']-F(str(r['recorded_score'])))<=F('0.000001'),(dataset,r['trial_name'],'baseline')
    checks['reconstructed_scores']+=1
    row['all_positive_full_credit']=all(F(str(f[k]))==1 for k,v in p['original'].items() if v>0)
   allrows.append(row)
  for task in d['configs']:
   for system in sorted({r['system'] for r in d['rows']}):
    group=[r for r in allrows if r['dataset']==dataset and r['task_id']==task and r['system']==system];scored=[r for r in group if r['scores']]
    for profile in ('original','focus_50','focus_60','focus_70'):
     vals=[r['scores'][profile] for r in scored];avg=mean(vals);loo=max((sum(vals)-v)/(len(vals)-1) for v in vals) if len(vals)>1 else None
     summaries.append({'dataset':dataset,'task':task,'system':system,'profile':profile,'n':len(vals),'slots':len(group),'mean':avg,'max_leave_one_out':loo,'below_060':avg is not None and avg<F('.60'),'loo_below_060':loo is not None and loo<F('.60'),'full_credit_vectors':sum(r.get('all_positive_full_credit',False) for r in scored),'contract_flagged':any(r.get('contract_issue') or 'LEGACY_CONTRACT' in r['status'] for r in group),'statuses':dict(Counter(r['status'] for r in group))})
 # Selection shows all evaluated alternatives, never searches arbitrary weights.
 selection=[]
 for key,c in configs.items():
  dataset,task=key.split('/');v={}
  for profile in ('original','focus_50','focus_60','focus_70'):
   ss=[s for s in summaries if s['dataset']==dataset and s['task']==task and s['profile']==profile]
   v[profile]={'low_groups':[s['system'] for s in ss if s['below_060']],'loo_low_groups':[s['system'] for s in ss if s['loo_below_060']],'complete_n8':all(s['n']==8 for s in ss),'contract_flagged':any(s['contract_flagged'] for s in ss)}
  selection.append({'dataset':dataset,'task':task,'ability':c['ability'],'profiles':v})
 result={'configs':configs,'records':allrows,'summaries':summaries,'selection':selection,'checks':dict(checks),'model_calls':0,'native_recalculations':0,'formal_weights_modified':False,'interpretation':'Posthoc development sensitivity. P15 V3 and V4 reuse overlapping answers, not independent task sets. Legacy-contract flagged scores remain numeric but separate in qualification.'}
 (HERE/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,default=outjson)+'\n')
 with (HERE/'scores_by_task_model.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(summaries[0]));writer.writeheader();writer.writerows({k:float(v) if isinstance(v,F) else json.dumps(v) if isinstance(v,dict) else v for k,v in s.items()} for s in summaries)
 flagged=[r for r in allrows if r['dataset']=='P15_V3' and r.get('contract_issue')]
 assert len(flagged)==24 and all(r['scores'] is not None for r in flagged)
 with (HERE/'legacy_contract_24_scores.csv').open('w',newline='',encoding='utf-8-sig') as f:
  fields=['task_id','system','slot','trial_name','original','focus_50','focus_60','focus_70','contract_issue','fact_source']
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
  for r in flagged:writer.writerow({**{k:r.get(k,'') for k in fields if k not in r['scores']},**{k:float(v)*100 for k,v in r['scores'].items()}})
 lines=['# 能力权重快速复算','', '原15题360个槽位；同一事实向量下算原分、重点50%、60%、70%。P15文件可用性占2分；既有负向项比例不加重。带旧合同问题的24份有数值、也保留问题标记。','']
 for dataset in data:
  lines+=['## '+dataset,'','|题目|Codex 原→50%|Claude 原→50%|Qwen 原→50%|50/60/70下低于0.60的组数|','|---|---:|---:|---:|---|']
  names=['codex','claude','qwen'] if dataset=='NEW6_REPAIRED' else ['codex_gpt56sol','claude_opus5','qwen38max']
  for task in data[dataset]['configs']:
   cells=[]
   for system in names:
    a=next(s for s in summaries if s['dataset']==dataset and s['task']==task and s['system']==system and s['profile']=='original');b=next(s for s in summaries if s['dataset']==dataset and s['task']==task and s['system']==system and s['profile']=='focus_50')
    cells.append(f"{float(a['mean'])*100:.2f} → {float(b['mean'])*100:.2f}（{b['n']}）" if b['n'] else '无可评分事实')
   sel=next(s for s in selection if s['dataset']==dataset and s['task']==task);flag=' ⚑旧合同' if sel['profiles']['focus_50']['contract_flagged'] else ''
   lines.append('|'+task+flag+'|'+'|'.join(cells)+'|'+ '/'.join(str(len(sel['profiles'][p]['low_groups'])) for p in ('focus_50','focus_60','focus_70'))+'|')
  lines.append('')
 lines+=['完整各档分数、分母、去一敏感性、权重和来源见 results.json / scores_by_task_model.csv。0次模型调用、0次新增原生重算。', '外部依据：[SpreadsheetBench](https://arxiv.org/abs/2406.14991) 的真实任务与多输入验证；[GDPval](https://openai.com/index/gdpval/) 的工作产物和专家评分要求。具体百分比是本轮设定，不是外部标准。']
 (HERE/'REPORT_ZH.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines));print('CHECKS',dict(checks))
if __name__=='__main__':run()
