"""Portable version-pinned revised-cost score entry, without Agent/API calls."""
from pathlib import Path
import argparse,sys,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repro'))
from score import run_case
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--answer',required=True);p.add_argument('--input-dir',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=run_case({'task':'C1','task_root':str(HERE/'tasks/NEW6-C-COST-WORKPAPER-001'),'answer':str(Path(a.answer).resolve()),'input_dir':str(Path(a.input_dir).resolve())},a.out)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result['evaluation_status'] in ['SCORED','OUTPUT_MISSING','MALFORMED_OUTPUT'] else 2)
