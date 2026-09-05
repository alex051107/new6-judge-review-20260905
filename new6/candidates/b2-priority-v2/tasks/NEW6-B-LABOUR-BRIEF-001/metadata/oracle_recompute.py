"""Independent Decimal screening oracle, recomputed from both original sources."""
from pathlib import Path
from decimal import Decimal
import json
from oracle_base import recompute
TASK=Path(__file__).resolve().parents[1]
def oracle():
    base=recompute()
    scenarios={}; register={r[0]:{} for r in base['panel']}
    for scenario,threshold in [('baseline','1.0'),('relaxed','0.5'),('strict','2.0')]:
        t=Decimal(threshold);eligible=[]
        for r in base['panel']:
            available=r[6] is not None and r[7] is not None
            yes=available and Decimal(r[7])>=t and Decimal(r[6])<=-t
            register[r[0]][scenario+'_eligible']='unavailable' if not available else 'yes' if yes else 'no'
            if yes:eligible.append(r)
        ranked=sorted(eligible,key=lambda r:(-Decimal(r[7]),Decimal(r[6]),r[0]))[:5]
        selected={r[0] for r in ranked}
        scenarios[scenario]=[{'order':i+1,'code':r[0],'employment_change':r[6],'unemployment_change':r[7]} for i,r in enumerate(ranked)]
        for code,row in register.items():row[scenario+'_selected']='yes' if code in selected else 'no'
    baseline={r['code'] for r in scenarios['baseline']}
    movements={s:{'entered':sorted({r['code'] for r in rows}-baseline),'left':sorted(baseline-{r['code'] for r in rows})} for s,rows in scenarios.items()}
    return {'register':register,'shortlists':scenarios,'movements':movements,'counts':{s:len(rows) for s,rows in scenarios.items()},'verification':'Original ONS rates independently reconciled against raw OOXML by oracle_base; Decimal thresholds and lexicographic ordering. Reference screening is separately calculated in JavaScript integer tenths.'}
if __name__=='__main__':
    out=oracle();(TASK/'solution/priority_oracle.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({'counts':out['counts'],'movements':out['movements']}))
