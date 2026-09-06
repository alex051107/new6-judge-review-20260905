"""One scoped baseline: shared source/date legality versus actual citation errors."""
import copy,json
from collections import Counter
from evaluate import ROOT,parse,source_facts,effective_date_fact,quote_facts,rkey,dec,ParsePending,require_native_results
from runtime import recalculate_xlsx

def main():
    out=ROOT/'metadata/source_trace_repair';out.mkdir(exist_ok=True)
    fresh,recalc=recalculate_xlsx(ROOT/'fixtures/shared_source.xlsx',out/'baseline')
    require_native_results(fresh);shared=parse(fresh)
    original=parse(ROOT/'solution/reference.xlsx');wrong=parse(ROOT/'fixtures/wrong_page.xlsx');missing=parse(ROOT/'fixtures/missing_source.xlsx')
    bands={(r['service'],dec(r['upper_bound']),r['weight_unit']) for r in original['rates']}
    def check(candidate):
        units={'R006':[]};source_facts(candidate,bands,units);assert len(units['R006'])==26
        return units['R006']
    good=check(shared);assert all(x['correct'] for x in good)
    assert effective_date_fact(shared)[0] and effective_date_fact(original)[0]
    for candidate in (shared,wrong,missing):
        assert Counter((rkey(r),str(r['usd'])) for r in candidate['rates'])==Counter((rkey(r),str(r['usd'])) for r in original['rates'])
        assert [(q['request_id'],q['weight'],q['weight_unit'],q['zone']) for q in candidate['quotes']]==[(q['request_id'],q['weight'],q['weight_unit'],q['zone']) for q in original['quotes']]
    units={'R003':[]};quote_facts(shared,json.loads((ROOT/'metadata/oracle_expected.json').read_text()),units,'R003')
    assert len(units['R003'])==49 and all(x['correct'] for x in units['R003'])
    wrong_facts=check(wrong)
    assert sum(x['correct'] for x in wrong_facts)==16
    assert all(x['correct'] for x in wrong_facts if 'ground' in x['fact'] or x['fact'] in ('request_source_trace','pdf_identity_trace'))
    missing_facts=check(missing)
    assert sum(x['correct'] for x in missing_facts)==2
    assert all(x['correct'] for x in missing_facts[-2:])
    unresolved=copy.deepcopy(shared)
    for entry in unresolved['visible_rows']:
        if 'Source:' in entry['text']:
            entry['text']='Source: Notice 123, pages 5 and 7';entry['values']=[entry['text']]
    try:check(unresolved)
    except ParsePending as exc:assert not exc.details['oracle_values_used_for_discovery']
    else:raise AssertionError('Substantive unbound citation must remain pending')
    global_excel_date=copy.deepcopy(shared)
    from datetime import datetime
    for entry in global_excel_date['visible_rows']:
        if 'Effective date' in entry['text']:
            entry['values']=['Effective date',datetime(2026,7,12)];entry['text']='Effective date | 2026-07-12 00:00:00'
    assert effective_date_fact(global_excel_date)[0]
    receipt={'judge_version':'new6-usps-facts-v1.2-shared-source','passed':True,'native_baseline_runs':1,'dynamic_recalculations':0,'full_judge_runs':0,'agent_calls':0,'assertions':{'legal_shared_sources':'26/26 R006 facts; Priority printed-page locator and Ground equivalent Retail service/weight-table locator','global_effective_date':'07/12/2026 and native Excel datetime both accepted without per-row dates','baseline_quotes':'49/49 unchanged correct quote outputs','prices_and_request_identity':'192 rate prices and 12 request identities unchanged in all three fixtures','wrong_page':'Only 10 Priority band-source facts lose credit;14 Ground bands and both origin facts remain correct','missing_source':'24 band source facts lose credit; both origin facts retained','substantive_unbound_reference':'ParsePending for semantic binding, not business zero'},'recalc':recalc,'scope':'Weights, denominators, input obligations, frozen wrapper and historical OUTPUT_MISSING result unchanged','limits':'Not a general layout or citation language interpreter; unresolved substantive source locators remain pending'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2,default=str));print(json.dumps(receipt,indent=2,default=str))
if __name__=='__main__':main()
