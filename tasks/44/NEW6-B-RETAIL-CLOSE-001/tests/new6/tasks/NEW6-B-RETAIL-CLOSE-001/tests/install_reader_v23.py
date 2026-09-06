"""Freeze the B1 reader alone; an existing scorer reloads the pointer next wave."""
from pathlib import Path
import argparse,json,shutil,os
T=Path(__file__).resolve().parents[1];R=T.parents[2]
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,default=R/'new6/campaigns/new6-current-v3-144/runtime');p.add_argument('--activate',action='store_true');a=p.parse_args();runtime=a.runtime.resolve();manifest=runtime/'campaign.json';m=json.loads(manifest.read_text());source=Path(m['frozen_wrappers']['B1']);dest=runtime/'reader-updates/b1-v23'/T.name
 if dest.exists():raise SystemExit('Immutable override already exists; do not overwrite it.')
 if not all(json.loads((T/'metadata/reader_v23'/name).read_text())['status']=='CALIBRATION_PASSED' for name in ['calibration_all.json','semantic_calibration.json']):raise SystemExit('Focused calibration is incomplete')
 shutil.copytree(source,dest);nested=dest/'tests/new6/tasks'/T.name
 shutil.copytree(T/'tests',nested/'tests',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
 shutil.copy2(T/'rubric.json',nested/'rubric.json');meta=nested/'metadata/reader_v23';meta.mkdir(parents=True,exist_ok=True);shutil.copy2(T/'metadata/reader_v23/visual_claims.json',meta/'visual_claims.json')
 receipt={'judge_version':'new6-b1-reader-v2.3','override':str(dest),'activation_requested':a.activate,'api_calls':0,'paid_campaign_unchanged':True}
 if a.activate:
  # Re-read latest state so simultaneous changes to other task pointers survive.
  current=json.loads(manifest.read_text());current.setdefault('judge_overrides',{})['B1']=str(dest);temp=manifest.with_name('campaign.b1-v23.tmp');temp.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n');os.replace(temp,manifest)
 print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
