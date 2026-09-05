"""Bounded offline regrade of three collected C1 attempts; never an agent call."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
NEW6=ROOT.parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from evaluate import evaluate

TRIALS=['y2JFhCx','PSW5qZb','NLbnwXz']
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--evidence-dir',default='/tmp/new6-c1-current-rejudge');args=parser.parse_args()
    out=Path(args.evidence_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    answers=ROOT/'metadata/current_rejudge_batch_v11/answers'
    snapshot=json.loads((answers/'manifest.json').read_text())
    rows=[]
    for suffix in TRIALS:
        matches=[x for x in snapshot['records'] if x['trial'].endswith('__'+suffix)]
        if len(matches)!=1:raise ValueError('Expected exactly one archived C1 trial: '+suffix)
        entry=matches[0];answer=answers/entry['file']
        if hashlib.sha256(answer.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Copied original hash mismatch: '+suffix)
        result=evaluate(answer,out/suffix,True)
        row={'trial':entry['trial'],'attempt':entry['attempt'],'old_status':entry['old_status'],
          'evaluation_status':result['evaluation_status'],'score_decimal':result.get('score_decimal'),
          'criterion_scores':result.get('criterion_scores'),
          'profiles':{k:v.get('score_decimal') for k,v in result['profiles'].items()},
          'error':result.get('evidence',{}).get('error'),'receipt':str(out/suffix/'evaluation.json'),
          'original_unchanged':result.get('evidence',{}).get('base_native_receipt',{}).get('original_unchanged')}
        native_receipts=list((out/suffix/'base').glob('recalc-*/recalc_receipt.json'))
        if native_receipts:
            native=json.loads(native_receipts[-1].read_text())
            for k in ['original_unchanged','source_sha256_before','source_sha256_after']:row[k]=native[k]
            row['native_recalc_receipt']=str(native_receipts[-1])
        rows.append(row)
        (out/'receipt.json').write_text(json.dumps({'judge_version':'new6-c1-facts-v1.2-controls-and-notes','snapshot_at':snapshot['snapshot_at'],'fixed_trial_count':3,'agent_calls':0,'records':rows},indent=2))
        print(json.dumps(row),flush=True)
if __name__=='__main__':main()
