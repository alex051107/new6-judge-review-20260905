"""One predeclared combined calibration, with exact changed/preserved criteria.

Fixtures are generated from private reference copies and never classified by
filename. Every case must have valid expected state and itemwise assertions.
"""
from pathlib import Path
import json,shutil,sys
from fixture_xml import Fixture
from evaluate import evaluate
TASK=Path(__file__).resolve().parents[1];FIX=TASK/'fixtures';REF=TASK/'solution/reference.xlsx'
CRITERIA={f'R{i:03}' for i in range(1,7)}

def main():
    FIX.mkdir(exist_ok=True);cases=[]
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
    add('equivalent_formula',lambda f:f.cell('Authority panel','G2',-0.1,formula='D2-C2'))
    def free_text(f):
        f.cell('Briefing','A1','Local labour-market comparison').cell('Briefing','B1',None)
        for row,label in [(2,'First release'),(3,'Second release'),(4,'Survey coverage A'),(5,'Survey coverage B'),(6,'Who is counted for employment'),(7,'Who is counted for unemployment'),(8,'How changes are expressed'),(13,'Reading these estimates')]:f.cell('Briefing',f'A{row}',label)
        return f
    add('equivalent_free_text_brief',free_text)
    add('partial_parse_core_table',lambda f:f.cell('Authority panel','C1','People employed before, percent'),status='JUDGE_ERROR')
    add('missing_core_table',lambda f:f.clear_sheet('Authority panel'),['R001','R002','R003','R004'])
    add('equivalent_shared_chart_categories',lambda f:f.shared_categories())
    def rich_top(f):
        source={r[0]:r for r in json.loads((TASK/'solution/oracle.json').read_text())['panel']}
        top=json.loads((TASK/'solution/oracle.json').read_text())['top5']
        for col,h in [('F','Employment rate earlier'),('G','Employment rate later'),('H','Unemployment rate earlier'),('I','Unemployment rate later')]:f.cell('Top five',col+'1',h)
        for row,t in enumerate(top,2):
            for col,i in [('F',2),('G',3),('H',4),('I',5)]:f.cell('Top five',f'{col}{row}',float(source[t[1]][i]))
        return f
    add('equivalent_top5_with_all_rates',rich_top)
    def comparable_only(f):
        panel=json.loads((TASK/'solution/oracle.json').read_text())['panel']
        for i,r in enumerate(panel,2):
            if r[6] is None or r[7] is None:f.remove_row('Authority panel',i)
        f.clear_sheet('Source trace')
        for row,(a,b) in enumerate([('Source context','Original LI01 files preserved; match geography code and rate heading'),('Earlier source','ons_li01_january2024.xlsx'),('Later source','ons_li01_january2025.xlsx')],1):f.cell('Source trace',f'A{row}',a).cell('Source trace',f'B{row}',b)
        return f.remove_row('Briefing',13)
    add('equivalent_comparable_only_indirect_sources',comparable_only)
    def free_exclusions(f):
        for row in [2,4]:f.cell('Exclusions',f'C{row}',None).cell('Exclusions',f'D{row}','Employment unavailable/suppressed; unemployment unavailable/suppressed')
        return f.cell('Exclusions','C1',None).remove_row('Exclusions',3).remove_row('Exclusions',5)
    add('equivalent_exclusions_in_reason_text',free_exclusions)
    add('wrong_identity',lambda f:f.cell('Authority panel','B2','Wrong authority'),['R001'])
    add('wrong_percentage_point',lambda f:f.cell('Authority panel','H2',0.1),['R003'])
    add('omitted_authority',lambda f:f.remove_row('Authority panel',2),['R001','R002','R003'])
    add('duplicate_authority',lambda f:f.duplicate_row('Authority panel',2),['R002'])
    panel=json.loads((TASK/'solution/oracle.json').read_text())['panel']
    suppressed=next(i+2 for i,r in enumerate(panel) if r[0]=='E06000053')
    def suppress_zero(f):
        for col in ['C','D','E','F','G','H']:f.cell('Authority panel',f'{col}{suppressed}',0)
        return f.remove_row('Exclusions',2).remove_row('Exclusions',3)
    add('suppression_zero',suppress_zero,['R002','R003'])
    add('aggregate_in_top5',lambda f:f.cell('Top five','B2','E92000001').cell('Top five','C2','England'),['R004','R005'])
    add('mixed_final_representation',lambda f:f.duplicate_row('Top five',2,{'D':99}),['R004'])
    add('stale_chart_cache',lambda f:f.stale_cache(),['R005'])
    changed=FIX/'changed_inputs';changed.mkdir(exist_ok=True)
    for src in (TASK/'data/input_files').glob('*.xlsx'):shutil.copyfile(src,changed/src.name)
    # Mutate the actual post-run source workbook, not a private evaluator copy.
    Fixture(changed/'ons_li01_january2024.xlsx').cell('LI01','E10',99).save(changed/'ons_li01_january2024.xlsx')
    add('source_mutated',loss=['R006'],input_dir=changed)
    add('output_missing',status='OUTPUT_MISSING')
    add('malformed_file',status='MALFORMED_OUTPUT')
    add('legitimate_uncached_formula',lambda f:f.cell('Authority panel','G2',None,formula='_xlfn.LET(x,D2-C2,x)',uncached=True),status='JUDGE_ERROR')
    # Schema validation fails closed before invoking any judge.
    for case in cases:
        if not isinstance(case['loss'],list) or not set(case['loss'])<=CRITERIA:raise ValueError('Invalid loss assertion')
        if case['expected_status']=='SCORED' and set(case['loss'])|set(case['unchanged'])!=CRITERIA:raise ValueError('Incomplete criterion assertions')
        if set(case['loss'])&set(case['unchanged']):raise ValueError('Contradictory assertions')
    (FIX/'manifest.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2))
    receipts=[];failed=[]
    for case in cases:
        if len(sys.argv)>1 and case['name'] not in sys.argv[1:]:continue
        result=evaluate(Path(case['path']),case['input_dir']);checks=[]
        checks.append(result['evaluation_status']==case['expected_status'])
        if case['expected_status']=='SCORED' and result['evaluation_status']=='SCORED':
            facts=result['criterion_scores'];checks.extend(facts[k]<1 for k in case['loss']);checks.extend(facts[k]==1 for k in case['unchanged'])
            if not case['loss']:checks.append(result['score_decimal']=='1.0')
            checks.append(all(p['criterion_scores']==facts for p in result['profiles'].values()))
        else:
            checks.append(result['normalized_score'] is None)
            checks.append(result['pass'] is (False if case['expected_status'] in ['OUTPUT_MISSING','MALFORMED_OUTPUT'] else None))
        good=all(checks);receipt={'fixture':case['name'],'assertions_passed':good,'expected':case,'result':result};receipts.append(receipt)
        print(case['name'],good,result.get('criterion_scores'),result['evaluation_status'],flush=True)
        if not good:failed.append(case['name'])
        (FIX/(case['name']+'.receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    all_receipts=[json.loads((FIX/(c['name']+'.receipt.json')).read_text()) for c in cases if (FIX/(c['name']+'.receipt.json')).exists()]
    failed=[r['fixture'] for r in all_receipts if not r['assertions_passed']]
    missing=[c['name'] for c in cases if not (FIX/(c['name']+'.receipt.json')).exists()]
    summary={'task_id':TASK.name,'status':'CALIBRATION_PASSED' if not failed and not missing else 'CALIBRATION_FAILED','fixture_count':len(cases),'failed':failed,'missing':missing,'agent_attempts':0,
      'profiles':'same candidate facts, fixed 3 profiles; only raw >= 0.70 is pass',
      'actual_checks':'one combined runner covering all declared semantic categories; after defects rerun affected cases only',
      'source_oracle':'Independent XML vs openpyxl, all eligible rates; independent grouped ranking verified before input/reference construction'}
    (TASK/'metadata/validation_receipt.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    if failed:raise SystemExit(1)
if __name__=='__main__':main()
