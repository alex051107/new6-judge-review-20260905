"""Activate public v2 after v1 is frozen. Preserve old fixture receipts."""
from pathlib import Path
import json,shutil,hashlib
P=Path(__file__).resolve().parent;T=P.parents[1]
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
o=read(P/'bridge_oracle.json')
shutil.copyfile(P/'bridge_oracle.json',T/'solution/bridge_oracle.json')
shutil.copyfile(P/'september_extract_private.csv',T/'data/input_files/september_extract.csv')
plan=read(T/'metadata/reference_plan.json')
plan['sheets']=[s for s in plan['sheets'] if s['name'] not in ['Monthly bridge','SKU comparison']]
plan['sheets'].extend([
 {'name':'Monthly bridge','rows':[o['bridge_headers']]+[[k,float(v)] for k,v in o['bridge']]+[['Interpretation',o['interpretation']],['Source','UCI Online Retail, DOI 10.24432/C5BW33; complete September and October 2011, ordinary sales only for SKU effects; credits separately.']]},
 {'name':'SKU comparison','rows':[o['sku_headers']]+[[v if j<2 or v is None else float(v) for j,v in enumerate(r)] for r in o['sku_schedule']]}
])
for s in plan['sheets']:
 if s['name']=='Trading report':
  s['rows']=[r for r in s['rows'] if r[0]!='Monthly comparison']
  s['rows'].append(['Monthly comparison','Net recorded value rose by GBP 51,017.05. New SKU sales contributed GBP 98,404.21; the signed-credit change reduced the movement by GBP 45,372.08. See Monthly bridge and SKU comparison for the full arithmetic attribution.'])
write(T/'metadata/reference_plan.json',plan)
r=read(T/'rubric.json');r['task_version']='new6-b1-v2';r['judge_version']='new6-b1-bridge-facts-v2';r['status']='CALIBRATION_IN_PROGRESS'
r['criteria']=[c for c in r['criteria'] if c['id'] not in ['R007','R008']]+[
 {'id':'R007','description_zh':'九至十月五项贡献、两端净額与闭合事实','type':'positive','weight':25,'scoring':'Nine independently bound numerical claims and candidate-only bridge closure; visible comparison convention.'},
 {'id':'R008','description_zh':'SKU两月数量、销售额、群组和贡献可追溯','type':'positive','weight':10,'scoring':'Fixed source SKU population and nine factual units per SKU; September source facts retained. Weighted unit prices may be recoverable rather than displayed.'}]
r['profiles']={'capability_first':dict(zip([f'R{i:03}' for i in range(1,9)],[10,15,10,15,8,7,25,10])),
 'balanced':dict(zip([f'R{i:03}' for i in range(1,9)],[15,15,15,10,8,7,20,10])),
 'ongoing_use':dict(zip([f'R{i:03}' for i in range(1,9)],[10,12,10,15,8,10,20,15]))}
for c in r['criteria']:c['weight']=r['profiles']['capability_first'][c['id']]
r['weight_basis']='Primary profile assigns 35% to the newly requested source-based arithmetic attribution and its SKU evidence. October close retains 65%. Weights express target analysis ability, not an observed score target; no Agent v2 results existed when fixed.'
write(T/'rubric.json',r)
m=read(T/'metadata/source_manifest.json');m['task_version']='new6-b1-v2'
m['comparison_extract']={'file':'september_extract.csv','source_workbook':'Online Retail.xlsx','physical_occurrences':o['september_occurrences'],'transformation':'Every original row dated 2011-09-01 inclusive to 2011-10-01 exclusive; original physical source_row_id and all business columns retained. Overlap with October context is explicitly disclosed.','oracle_gate':'PASSED exact rational bridge and independent reversed Decimal source aggregation'}
m['input_files']=[x for x in m['input_files'] if x['filename']!='september_extract.csv']+[{'filename':'september_extract.csv','sha256':hashlib.sha256((T/'data/input_files/september_extract.csv').read_bytes()).hexdigest(),'size':(T/'data/input_files/september_extract.csv').stat().st_size}]
write(T/'metadata/source_manifest.json',m)
s=read(T/'metadata/build_status.json');s.update(task_version='new6-b1-v2',reference_ready=False,evaluator_ready=False,calibration_passed=False,fixture_count_v1=20,agent_runs=0,formal_difficulty_verified=False,difficulty_status='NO_V2_AGENT_ATTEMPTS');write(T/'metadata/build_status.json',s)
shutil.copyfile(T/'metadata/validation_receipt.json',T/'metadata/validation_receipt_v1.json')
b=read(T/'metadata/requirements_basis.json');b['task_version']='new6-b1-v2';b['basis']['R007']='instruction requests September-to-October reconciled bridge; visible brief defines five factors, endpoints, total change and residual';b['basis']['R008']='visible brief requests every ordinary-sales SKU, two-month quantities/values, cohort and applicable effects; original source facts remain reviewable';write(T/'metadata/requirements_basis.json',b)
d=read(T/'metadata/downstream_use_review.json');d['new_functionality']='v2 adds the publicly defined September-to-October arithmetic bridge and SKU schedule. v1 frozen at 683cdda and its first Agent attempt is v1 only.';write(T/'metadata/downstream_use_review.json',d)
n=read(T/'metadata/natural_prompt_review_receipt.json');n['task_version']='new6-b1-v2';n['judge_alignment']+=' Public mathematical convention defines a requested business attribution, without worksheet/coordinate mandates.';write(T/'metadata/natural_prompt_review_receipt.json',n)
print('v2 activated; old fixture receipts preserved; reference and calibration pending')
