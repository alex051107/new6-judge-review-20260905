import collections, importlib.util, json, sys, time
from pathlib import Path
sys.path.insert(0,'/workspace/new6/offline_judge_repair')
from freeze import verify
lock=verify()
spec=importlib.util.spec_from_file_location('fixed_score','/workspace/new6/repro/score.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rows=json.loads(Path('/results/selected.json').read_text());done=[]
for row in rows:
    case=row['case'];out=Path('/results/scores')/case;start=time.monotonic()
    try:
        result=module.run_case({'task':row['task'],'task_root':row['task_root'],
            'answer':'/cases/'+case+'/answer.xlsx','input_dir':'/cases/'+case+'/input'},out)
    except Exception as e:
        result={'evaluation_status':'JUDGE_EXECUTION_ERROR','score_decimal':None,'evidence':{'error':str(e)}}
        out.mkdir(parents=True,exist_ok=True);(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    item={'case':case,'status':result['evaluation_status'],'score_decimal':result.get('score_decimal'),
        'elapsed_seconds':round(time.monotonic()-start,3)}
    done.append(item)
    Path('/results/summary.json').write_text(json.dumps({'judge_commit':'34374f08f331e7184010c40b401f1630a49df394',
        'lock':lock,'results':done,'counts':dict(collections.Counter(r['status'] for r in done)),
        'api_calls':0,'agent_calls':0},ensure_ascii=False,indent=2))
    print(json.dumps(item,ensure_ascii=False),flush=True)
