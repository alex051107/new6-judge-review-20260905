"""One combined NEW6 retail calibration with exact expected facts per case."""
from pathlib import Path
from decimal import Decimal
from collections import Counter
import json,shutil,sys,csv
from fixture_xml import Fixture
from evaluate import evaluate
TASK=Path(__file__).resolve().parents[1];FIX=TASK/'fixtures';REF=TASK/'solution/reference.xlsx'
CRITERIA={f'R{i:03}' for i in range(1,7)}

def main():
    FIX.mkdir(exist_ok=True);cases=[];truth=json.loads((TASK/'solution/oracle.json').read_text())
    credit=next((i+2,r) for i,r in enumerate(truth['classified']) if r[9]=='credit')
    outside=next((i+2,r) for i,r in enumerate(truth['classified']) if r[9]=='outside_scope')
    seen=set();repeated=None
    for i,r in enumerate(truth['classified']):
        key=tuple(r[1:9])
        if key in seen and r[9]=='sale':repeated=(i+2,r);break
        seen.add(key)
    assert repeated,'Fixture requires a real repeated-looking source occurrence'
    def add(name,mutator=None,loss=(),status='SCORED',input_dir=None):
        path=FIX/(name+'.xlsx')
        if status=='OUTPUT_MISSING':pass
        elif status=='MALFORMED_OUTPUT':path.write_text('This is not an XLSX file.')
        elif mutator:mutator(Fixture(REF)).save(path)
        else:shutil.copyfile(REF,path)
        cases.append({'name':name,'path':str(path),'expected_status':status,'loss':list(loss),
          'unchanged':sorted(CRITERIA-set(loss)) if status=='SCORED' else [],'input_dir':str(input_dir or TASK/'data/input_files')})
    add('reference')
    add('equivalent_layout',lambda f:f.layout())
    add('equivalent_formula',lambda f:f.cell('Classified records','K2',float(truth['classified'][0][10]),formula='E2*G2'))
    def free_text(f):
        f.cell('Trading report','A1','October 2011 trading close, GBP').cell('Trading report','B1',None)
        for row,label in [(2,'Review month'),(3,'Money units'),(4,'Total sales GBP'),(5,'Credit value'),(6,'Net trading value'),(7,'Exception value'),(8,'Total extract rows'),(9,'October occurrence count'),(10,'Outside October count'),(11,'Unknown customer rows')]:f.cell('Trading report',f'A{row}',label)
        return f
    add('equivalent_free_text_report',free_text)
    add('partial_parse_core_table',lambda f:f.cell('Classified records','J1','Treatment disposition'),status='JUDGE_ERROR')
    add('missing_core_table',lambda f:f.clear_sheet('Classified records'),['R001','R002','R004','R006'])
    scope_rows={i+2 for i,r in enumerate(truth['classified']) if r[9]!='outside_scope'}
    add('equivalent_compact_in_scope_register',lambda f:f.project_register('Classified records',['A','J','K'],scope_rows))
    add('credit_sign_flip',lambda f:f.cell('Classified records',f'J{credit[0]}','sale').cell('Classified records',f'K{credit[0]}',abs(float(credit[1][10]))),['R002','R004'])
    add('wrong_report_net',lambda f:f.cell('Trading report','B6',float(truth['net_recorded_value'])+100),['R005'])
    add('drop_repeated_occurrence',lambda f:f.remove_row('Classified records',repeated[0]),['R001','R002','R004','R006'])
    add('duplicate_occurrence',lambda f:f.duplicate_row('Classified records',repeated[0]),['R001','R004'])
    add('outside_period_leak',lambda f:f.cell('Classified records',f'J{outside[0]}','sale'),['R001','R004'])
    add('mixed_final_report',lambda f:f.duplicate_row('Trading report',6,{'B':99}),['R005'])
    add('fabricated_credit_link',lambda f:f.cell('Classified records','N1','Original Invoice').cell('Classified records',f'N{credit[0]}','UNSUPPORTED-LINK'),['R006'])
    add('stale_chart_cache',lambda f:f.stale_cache(),['R005'])
    changed=FIX/'changed_inputs';changed.mkdir(exist_ok=True);src=TASK/'data/input_files/retail_extract.csv'
    with src.open(newline='') as fh:r=list(csv.reader(fh))
    r[1][4]=str(Decimal(r[1][4])+1)
    with (changed/src.name).open('w',newline='') as fh:csv.writer(fh).writerows(r)
    add('source_mutated',loss=['R006'],input_dir=changed)
    encoded=FIX/'equivalent_encoded_inputs';encoded.mkdir(exist_ok=True)
    with src.open(newline='') as fh:original=list(csv.reader(fh))
    with (encoded/src.name).open('w',encoding='utf-8-sig',newline='') as fh:csv.writer(fh,lineterminator='\n').writerows([list(reversed(row)) for row in original])
    add('equivalent_source_encoding',input_dir=encoded)
    add('output_missing',status='OUTPUT_MISSING')
    add('malformed_file',status='MALFORMED_OUTPUT')
    add('legitimate_uncached_formula',lambda f:f.cell('Classified records','K2',None,formula='_xlfn.LET(q,E2,q*G2)',uncached=True),status='JUDGE_ERROR')
    for case in cases:
        if not isinstance(case['loss'],list) or not set(case['loss'])<=CRITERIA:raise ValueError('Invalid loss assertion')
        if case['expected_status']=='SCORED' and set(case['loss'])|set(case['unchanged'])!=CRITERIA:raise ValueError('Incomplete criterion assertions')
        if set(case['loss'])&set(case['unchanged']):raise ValueError('Contradictory assertions')
    (FIX/'manifest.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2))
    for case in cases:
        if len(sys.argv)>1 and case['name'] not in sys.argv[1:]:continue
        result=evaluate(Path(case['path']),case['input_dir']);checks=[result['evaluation_status']==case['expected_status']]
        if case['expected_status']=='SCORED' and result['evaluation_status']=='SCORED':
            facts=result['criterion_scores'];checks.extend(facts[k]<1 for k in case['loss']);checks.extend(facts[k]==1 for k in case['unchanged'])
            if not case['loss']:checks.append(result['score_decimal']=='1.0')
            checks.append(all(p['criterion_scores']==facts for p in result['profiles'].values()))
        else:
            checks.append(result['normalized_score'] is None);checks.append(result['pass'] is (False if case['expected_status'] in ['OUTPUT_MISSING','MALFORMED_OUTPUT'] else None))
        good=all(checks);receipt={'fixture':case['name'],'assertions_passed':good,'expected':case,'result':result}
        print(case['name'],good,result.get('criterion_scores'),result['evaluation_status'],flush=True)
        (FIX/(case['name']+'.receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    all_receipts=[json.loads((FIX/(c['name']+'.receipt.json')).read_text()) for c in cases if (FIX/(c['name']+'.receipt.json')).exists()]
    failed=[r['fixture'] for r in all_receipts if not r['assertions_passed']];missing=[c['name'] for c in cases if not (FIX/(c['name']+'.receipt.json')).exists()]
    summary={'task_id':TASK.name,'status':'CALIBRATION_PASSED' if not failed and not missing else 'CALIBRATION_FAILED','fixture_count':len(cases),'failed':failed,'missing':missing,'agent_attempts':0,
      'profiles':'same candidate facts, fixed 3 profiles; only raw >=0.70 is pass',
      'actual_checks':'one combined runner covering the declared categories; after defects rerun affected cases only',
      'source_oracle':'All source occurrences classified and forward Decimal results independently checked using reverse document-first grouping.',
      'real_fixture_anchors':{'credit':credit[1][0],'repeated_looking_occurrence':repeated[1][0],'outside':outside[1][0]}}
    (TASK/'metadata/validation_receipt.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    if failed or missing:raise SystemExit(1)
if __name__=='__main__':main()
