"""Deterministic score aggregator ONLY; not a workbook parser/evaluator."""
import json
from decimal import Decimal, localcontext
from pathlib import Path

STATES = {'SCORED','JUDGE_ERROR','TASK_INVALID','NATIVE_RECALC_REQUIRED',
          'OUTPUT_MISSING','MALFORMED_OUTPUT','INFRA_ERROR'}
OUTCOME_POLICY_VERSION = 'new6-outcome-v2-delivery-zero'
def score(rubric, facts, profile='capability_first', status='SCORED'):
    if status not in STATES:
        raise ValueError('Unknown evaluation state')
    if status != 'SCORED':
        delivery_failure = status in {'OUTPUT_MISSING','MALFORMED_OUTPUT'}
        # Zero is the observed delivery outcome, not fabricated per-criterion facts.
        # The campaign collector must still exclude provider/runner/collection errors.
        return {'evaluation_status':status,'profile':profile,
                'normalized_score':0.0 if delivery_failure else None,
                'score_decimal':'0' if delivery_failure else None,
                'pass':False if delivery_failure else None,
                'sample_countable':delivery_failure,
                'outcome_policy_version':OUTCOME_POLICY_VERSION}
    weights= rubric['profiles'][profile]
    if set(facts) != set(weights):
        raise ValueError('Missing or unexpected factual criterion; do not silently fill zero')
    with localcontext() as ctx:
        ctx.prec=50
        total=Decimal(0);denom=Decimal(0);contributions={}
        for cid,w in weights.items():
            v=Decimal(str(facts[cid]));weight=Decimal(str(w))
            if not v.is_finite() or not Decimal(0)<=v<=Decimal(1):
                raise ValueError('Invalid factual score: '+cid)
            if not weight.is_finite() or weight<0:
                raise ValueError('Invalid positive weight')
            contributions[cid]=str(weight*v);total+=weight*v;denom+=weight
        if denom != Decimal(100):
            raise ValueError('Profile weights must total exactly 100')
        result=total/denom
        # This starter has no penalties. Add approved non-overlapping policies
        # explicitly; never migrate an old -7 into a new 100-point denominator.
        return {'evaluation_status':'SCORED','profile':profile,
                'normalized_score':float(result),'score_decimal':str(result),
                'pass':result>=Decimal('0.70'),'criterion_scores':facts,
                'contributions_raw':contributions}
