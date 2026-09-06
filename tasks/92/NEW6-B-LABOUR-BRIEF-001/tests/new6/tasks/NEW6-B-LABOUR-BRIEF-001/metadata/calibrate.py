"""One fixed, bidirectional suite; wrong assertions/types fail the process."""
from pathlib import Path
import sys,json,argparse,re,copy,xml.etree.ElementTree as ET,shutil
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'tests'));sys.path.insert(0,str(TASK.parents[1]/'common'))
from fixture_xml import Fixture,NS,N
from evaluate import evaluate
from runtime import recalculate_xlsx
from decimal import Decimal

def build():
    ref=TASK/'solution/reference.xlsx';out=TASK/'fixtures';out.mkdir(exist_ok=True)
    cases=[]
    def save(name,f,lose=(),preserve=(),status='SCORED',native=False):
        f.save(out/(name+'.xlsx'))
        cases.append({'id':name,'file':'fixtures/'+name+'.xlsx','status':status,'lose':list(lose),'preserve':list(preserve),'native':native})
    allids=['R001','R002','R003','R004','R005']
    cases.append({'id':'reference','file':'solution/reference.xlsx','status':'SCORED','preserve':allids})
    f=Fixture(ref).layout()
    # Coherent legal view in reversed physical row order with relocated columns.
    # Cache-free chart references display the actual reordered table.
    for name,data in list(f.parts.items()):
        if re.search(r'/charts/.*\.xml$',name):
            root=ET.fromstring(data)
            for parent in root.iter():
                for child in list(parent):
                    if child.tag.split('}')[-1] in ['numCache','strCache']:parent.remove(child)
            f.parts[name]=ET.tostring(root)
    save('equivalent_layout',f,preserve=allids)
    save('equivalent_formula',Fixture(ref).cell('Current data','I2',3.9,formula='ROUND(D2-C2,1)',uncached=True),preserve=allids,native=True)
    # A static update can keep the old workbook as the actual retained artifact.
    f=Fixture(ref)
    for name in list(f.sheets):
        if name.startswith('Previous '):
            f.clear_sheet(name)
            root=f.root(name)
            for d in root.findall('m:drawing',NS):root.remove(d)
            f.update(name,root)
    # Remove unreferenced historical chart part so chart inventory stays semantic.
    for name in list(f.parts):
        if re.search(r'/charts/.*\.xml$',name) and b'Previous shortlist' in f.parts[name]:del f.parts[name]
    save('equivalent_retained_previous_file',f,preserve=allids)
    plan=json.loads((TASK/'metadata/reference_plan.json').read_text())
    movements=next(b['rows'] for b in plan['current'] if b['name']=='Shortlist changes')[1:]
    oracle=json.loads((TASK/'solution/oracle.json').read_text())
    f=Fixture(ref)
    f.cell('Shortlist changes','G1','Previous rank').cell('Shortlist changes','H1','Current rank')
    for i,row in enumerate(movements,2):
        code=row[0]
        f.cell('Shortlist changes',f'G{i}',oracle['previous_shortlist'].index(code)+1 if code in oracle['previous_shortlist'] else None)
        f.cell('Shortlist changes',f'H{i}',oracle['shortlist'].index(code)+1 if code in oracle['shortlist'] else None)
    save('equivalent_combined_ranks',f,preserve=allids)
    f=Fixture(ref).clear_sheet('Shortlist changes')
    for i,row in enumerate(movements,25):
        f.cell('Current briefing',f'A{i}',row[0]);f.cell('Current briefing',f'B{i}',f'{row[1]} {row[4].lower()} the shortlist. {row[5]}.')
    save('equivalent_narrative_movements',f,preserve=allids)
    retained_row=next(i+2 for i,row in enumerate(movements) if row[4]=='Retained')
    f=Fixture(ref).cell('Shortlist changes',f'E{retained_row}','Not retained').cell('Shortlist changes',f'F{retained_row}','Both comparisons did not deteriorate; not in the top five.')
    save('negated_movement_keywords',f,lose=['R004'],preserve=['R001','R002','R003','R005'])
    # Add a genuine visible second graph for ten source-correct context areas.
    f=Fixture(ref);chart_name=next(n for n,v in f.parts.items() if re.search(r'/charts/.*\.xml$',n) and b'Current shortlist' in v)
    root=ET.fromstring(f.parts[chart_name]);newchart='xl/charts/chartContext.xml'
    for text in root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}t'):text.text='Additional authority context'
    for formula in root.findall('.//c:f',NS):
        match=re.fullmatch(r"'Current shortlist'!\$?([A-Z]+)\$?(\d+)(?::\$?([A-Z]+)\$?(\d+))?",formula.text)
        if not match:raise ValueError('Unexpected chart fixture reference')
        oldcol=match[1];newcol={'C':'B','D':'I','E':'J','F':'K','G':'L'}[oldcol]
        formula.text=f"'Current data'!${newcol}$1" if match[2]=='1' else f"'Current data'!${newcol}$2:${newcol}$11"
    for parent in root.iter():
        for child in list(parent):
            if child.tag.split('}')[-1] in ['numCache','strCache']:parent.remove(child)
    f.parts[newchart]=ET.tostring(root)
    relns='http://schemas.openxmlformats.org/package/2006/relationships';rid='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    import posixpath
    attached=False
    for relname,raw in list(f.parts.items()):
        if not re.match(r'xl/drawings/_rels/.*\.rels$',relname):continue
        rr=ET.fromstring(raw)
        original=next((a for a in rr if (a.get('Target').lstrip('/') if a.get('Target').startswith('/') else posixpath.normpath('xl/drawings/'+a.get('Target')))==chart_name),None)
        if original is None:continue
        draw=relname.replace('/_rels/','/').removesuffix('.rels');dr=ET.fromstring(f.parts[draw]);anchor=next(a for a in dr if any(x.get(rid)==original.get('Id') for x in a.iter()))
        newanchor=copy.deepcopy(anchor)
        for x in newanchor.iter():
            if x.get(rid)==original.get('Id'):x.set(rid,'rIdContextChart')
            if x.tag.endswith('}row'):x.text=str(int(x.text)+30)
            if x.tag.endswith('}cNvPr'):x.set('id','900');x.set('name','Additional authority context')
        dr.append(newanchor);f.parts[draw]=ET.tostring(dr)
        ET.SubElement(rr,'{'+relns+'}Relationship',{'Id':'rIdContextChart','Type':original.get('Type'),'Target':'../charts/chartContext.xml'});f.parts[relname]=ET.tostring(rr);attached=True;break
    assert attached,'Context chart must actually be on a worksheet'
    types=ET.fromstring(f.parts['[Content_Types].xml']);ET.SubElement(types,'{http://schemas.openxmlformats.org/package/2006/content-types}Override',{'PartName':'/'+newchart,'ContentType':'application/vnd.openxmlformats-officedocument.drawingml.chart+xml'});f.parts['[Content_Types].xml']=ET.tostring(types)
    save('equivalent_context_chart',f,preserve=allids)
    save('wrong_cumulative',Fixture(ref).cell('Current shortlist','H2',2.0),lose=['R003'],preserve=['R001','R002','R004','R005'])
    save('wrong_second_interval',Fixture(ref).cell('Current shortlist','E2',6.7),lose=['R003','R004'],preserve=['R001','R002','R005'])
    save('duplicate_shortlist_row',Fixture(ref).duplicate_row('Current shortlist',2),lose=['R002'],preserve=['R001','R003','R004','R005'])
    save('omit_shortlist_row',Fixture(ref).remove_row('Current shortlist',6),lose=['R002','R004'],preserve=['R001','R003','R005'])
    save('stale_chart_cache',Fixture(ref).stale_cache(),lose=['R004'],preserve=['R001','R002','R003','R005'])
    save('overwritten_previous_data',Fixture(ref).cell('Previous data','C2',0),lose=['R005'],preserve=['R001','R002','R003','R004'])
    save('wrong_movement',Fixture(ref).cell('Shortlist changes','E2','Left'),lose=['R004'],preserve=['R001','R002','R003','R005'])
    plan=json.loads((TASK/'metadata/reference_plan.json').read_text())
    data=next(b['rows'] for b in plan['current'] if b['name']=='Current data')
    missing_row=next(i+1 for i,row in enumerate(data) if row[0]=='E06000053')
    save('missing_exclusion',Fixture(ref).remove_row('Current exclusions',2).cell('Current data',f'N{missing_row}','Not assessed'),lose=['R001'],preserve=['R002','R003','R004','R005'])
    f=Fixture(ref)
    for c,v in zip(['A','B','C','D','E','F','G','H'],['Current rank','Code','Authority','Employment change 2023–2024 (pp)','Employment change 2024–2025 (pp)','Unemployment change 2023–2024 (pp)','Unemployment change 2024–2025 (pp)','Cumulative unemployment change (pp)']):f.cell('Current shortlist',c+'30',v)
    for col,value in zip('ABCDEFGH',[1,'E07000148','Norwich',-7.6,-4.8,2.4,.1,2.5]):f.cell('Current shortlist',col+'31',value)
    save('mixed_final_shortlists',f,lose=['R002'],preserve=['R001','R003','R004','R005'])
    f=Fixture(ref)
    for name in list(f.sheets):
        if not name.startswith('Previous '):
            root=f.root(name);row=root.find('m:sheetData/m:row',NS)
            if row is not None:
                for cell in row:
                    for el in list(cell):cell.remove(el)
                    cell.set('t','inlineStr');ET.SubElement(ET.SubElement(cell,'{'+N+'}is'),'{'+N+'}t').text='Unfamiliar legal layout'
                f.update(name,root)
    save('unsupported_layout',f,status='JUDGE_ERROR')
    save('uncached_formula_direct',Fixture(ref).cell('Current data','I2',formula='_xlfn.UNSUPPORTED_NATIVE_FUNCTION()',uncached=True),status='JUDGE_ERROR')
    (out/'bad_file.xlsx').write_text('not an OOXML workbook')
    cases.extend([{'id':'bad_file','file':'fixtures/bad_file.xlsx','status':'MALFORMED_OUTPUT'}, {'id':'missing_output','file':'fixtures/absent.xlsx','status':'OUTPUT_MISSING'}])
    (TASK/'metadata/calibration_cases.json').write_text(json.dumps(cases,indent=2))
    return cases

def main():
    p=argparse.ArgumentParser();p.add_argument('--case',action='append');p.add_argument('--out',type=Path,required=True);p.add_argument('--build',action='store_true');a=p.parse_args()
    cases=build() if a.build else json.loads((TASK/'metadata/calibration_cases.json').read_text())
    if a.case:cases=[c for c in cases if c['id'] in a.case]
    if not cases:raise ValueError('No cases')
    a.out.mkdir(parents=True,exist_ok=False);checks=[]
    for case in cases:
        path=TASK/case['file'];native=None
        if case.get('native'):path,native=recalculate_xlsx(path,a.out/case['id']/ 'native',120)
        result=evaluate(path,TASK/'data/input_files');(a.out/(case['id']+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
        try:
            assert result['evaluation_status']==case['status'],(result['evaluation_status'],result.get('evidence',{}).get('reason'))
            if case['status']=='SCORED':
                facts=result['criterion_scores']
                for k in case.get('lose',[]):assert isinstance(facts[k],(float,int)) and facts[k]<1,(k,'must lose',facts[k])
                for k in case.get('preserve',[]):assert facts[k]==1,(k,'must preserve',facts[k])
                assert set(result['profiles'])=={'capability_first','balanced','ongoing_use'}
                for profile in result['profiles'].values():
                    assert profile['criterion_scores']==facts
                    assert profile['pass']==(Decimal(profile['score_decimal'])>=Decimal('.70'))
            elif case['status'] in ['MALFORMED_OUTPUT','OUTPUT_MISSING']:
                assert result['normalized_score']==0 and result['pass'] is False
            else:assert result['normalized_score'] is None and result['pass'] is None
            checks.append({'case':case['id'],'passed':True,'status':result['evaluation_status'],'score':result.get('score_decimal'),'native':native})
        except AssertionError as exc:checks.append({'case':case['id'],'passed':False,'error':str(exc),'facts':result.get('criterion_scores')})
        print(json.dumps(checks[-1]),flush=True)
    receipt={'passed':all(x['passed'] for x in checks),'checks':checks,'api_calls':0}
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2));return 0 if receipt['passed'] else 1
if __name__=='__main__':sys.exit(main())
