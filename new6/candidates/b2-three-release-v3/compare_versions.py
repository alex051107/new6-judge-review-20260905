"""Compare archived observed scores; never apply new obligations to old answers."""
from pathlib import Path
from decimal import Decimal
import json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCES=[('two-release-static',HERE/'comparison/old_static_result.json'),
 ('two-release-dynamic',ROOT/'candidates/b2-priority-v2/validation/portable_chart_v21/actual_final/evaluation.json'),
 ('three-release-handover',HERE/'samples/first_attempt/judge_result.json')]
if __name__=='__main__':
    rows=[]
    for version,path in SOURCES:
        x=json.loads(path.read_text());assert x['evaluation_status']=='SCORED'
        values={k:str(Decimal(v['score_decimal'])*100) for k,v in x['profiles'].items()}
        rows.append({'version':version,'source':str(path.relative_to(ROOT)),'scores_out_of_100':values,'highest_profile':max(values,key=lambda k:Decimal(values[k]))})
    out=HERE/'comparison';out.mkdir(exist_ok=True);(out/'results.json').write_text(json.dumps({'rows':rows,'primary_profile':'capability_first','different_task_versions':True,'natural_attempts_per_version':1,'api_calls':0},indent=2))
    print(json.dumps(rows,ensure_ascii=False,indent=2))
