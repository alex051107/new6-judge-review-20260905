#!/usr/bin/env python3
"""One source of truth: fixed trial ledger; no hand-entered means."""
import json,csv,math,pathlib,collections
from decimal import Decimal as D
ROOT=pathlib.Path(__file__).resolve().parents[1]
DISPLAY={'codex':'GPT-5.6 sol','claude':'Opus 5','qwen':'Qwen 3.8'}
def csvwrite(name,rows):
 if not rows:return
 with (ROOT/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 rows=json.loads((ROOT/'results/trials.json').read_text());groups=collections.defaultdict(list);criteria=[]
 for r in rows:
  # Display aliases never erase actual response/configuration distinctions.
  group=(r['task'],r['system'],r['generation_config_id'],','.join(r['actual_model_ids']) or 'requested_only')
  groups[group].append(r)
  weights=json.loads((ROOT/'release.json').read_text())['tasks'][r['task']]['primary_weights']
  for c,v in (r['criterion_scores'] or {}).items():criteria.append({'trial':r['id'],'task':r['task'],'system':DISPLAY[r['system']],'criterion':c,'credit':v,'weight':weights[c],'contribution':str(D(str(v))*D(str(weights[c]))/100),'receipt':r['receipt']})
 summary=[]
 for (task,sys,config,actual),rr in sorted(groups.items()):
  valid=[r for r in rr if r['status'] in ['SCORED','OUTPUT_MISSING','MALFORMED_OUTPUT'] and r['score_decimal'] is not None];n=len(valid);wins=sum(D(r['score_decimal'])>=D('.70') for r in valid);scored=sum(r['status']=='SCORED' for r in rr);missing=sum(r['status'] in ['OUTPUT_MISSING','MALFORMED_OUTPUT'] for r in rr);infra=sum(r['status']=='INFRASTRUCTURE_FAILURE' for r in rr);pending=len(rr)-scored-missing-infra
  all_complete=n==len(rr);applicable=all_complete and n>=8 and sys!='qwen';p8=D(1)-D(math.comb(n-wins,8) if n-wins>=8 else 0)/D(math.comb(n,8)) if applicable else None
  item={'task':task,'system':DISPLAY[sys],'configuration':config,'actual_model_ids':actual,'attempts':len(rr),'scoreable_workbooks':scored,'confirmed_nondelivery':missing,'infra_failures':infra,'pending':pending,'mean_denominator':n,'mean_score':str(sum((D(r['score_decimal']) for r in valid),D(0))/n) if n else None,'passes':wins,'pass_at_1':str(D(wins)/n) if n and all_complete else None,'pass_at_8':str(p8) if p8 is not None else None,'pass_at_k_note':'complete homogeneous group' if applicable else 'unresolved outcomes, fewer than 8 same-configuration samples, or unverified Qwen identity; no pass@8','difficulty_result':'NOT_VERIFIED','ability_interpretation':'C2 Judge false-negative found; no low-ability conclusion' if task=='C2' else 'See low-score audit; unreviewed totals are not proof of ability'}
  summary.append(item)
 csvwrite('results/summary.csv',summary);(ROOT/'results/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 csvwrite('results/criteria.csv',criteria)
 flat=[];profiles=[]
 for r in rows:
  flat.append({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items() if k not in ['profiles','criterion_scores']})
  for name,p in (r['profiles'] or {}).items():profiles.append({'trial':r['id'],'task':r['task'],'system':DISPLAY[r['system']],'profile':name,'score_decimal':p.get('score_decimal'),'pass':p.get('pass')})
 csvwrite('results/trials.csv',flat);csvwrite('results/alternate_profiles.csv',profiles)
 lines=['# 当前主方案结果','', '数据来自固定的逐次表；运行未结束的后续结果不自动追加。本表记录现有 Judge 的实际输出，C2 已发现判分误差，不能据此作低能力或难度结论。','','展示名称统一，不同实际返回身份与配置仍分行。完整模型 ID 见逐次表；下表配置号可在 configs 中定位。均分分母为可评分工作簿加确认未交付，未知状态不补零。','','| 题 | 系统 | 配置/响应组 | 尝试 | 可评分 | 未交付 | 环境失败 | 待判 | 均分 /100（n） | 通过 | pass@1 | pass@8 |','|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 seen=collections.defaultdict(int)
 for r in summary:
  key=(r['task'],r['system']);seen[key]+=1;group=r['configuration'][:6]+f'/{seen[key]}'
  mean='—' if r['mean_score'] is None else f"{float(r['mean_score'])*100:.2f} ({r['mean_denominator']})"
  pct=lambda x:'—' if x is None else f'{float(x)*100:.1f}%'
  lines.append(f"| {r['task']} | {r['system']} | {group} | {r['attempts']} | {r['scoreable_workbooks']} | {r['confirmed_nondelivery']} | {r['infra_failures']} | {r['pending']} | {mean} | {r['passes']} | {pct(r['pass_at_1'])} | {pct(r['pass_at_8'])} |")
 lines+=['','pass@k 使用无放回估计 1−C(n−c,k)/C(n,k)，n 是同题、同生成配置的已判定独立 Agent 尝试，c 为通过次数。n=8 时 pass@8 是这组八次至少成功一次的指示量，不是通过次数除以8。缺少足够同配置样本、仍有待判或模型身份不明时留空。pass@1 也不对未完整判定的组给正式估计，避免只取可评分子集。','','正式难度要求每题至少两个指定系统分别同时满足 pass@8<70% 和 avg score<0.6。当前六题均为**待验收**；Opus 5 的替代确认、Qwen 实际身份、独立 Qwen3 验收及 Judge 缺陷尚未全部解决。','','[逐次表](trials.csv) · [完整分组数据](summary.csv) · [逐项信用](criteria.csv) · [另两套配重](alternate_profiles.csv) · [低分核对](LOW_SCORE_AUDIT.md)']
 (ROOT/'results/SUMMARY.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'trials':len(rows),'statuses':dict(collections.Counter(r['status'] for r in rows)),'groups':len(summary)},ensure_ascii=False))
if __name__=='__main__':main()
