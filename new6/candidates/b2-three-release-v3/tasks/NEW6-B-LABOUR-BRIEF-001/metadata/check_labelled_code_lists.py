"""One focused v3.2 compatibility set; no Agent calls or native recalculation.

Validates code-only list recognition, fact-level contradiction treatment and
the boundary between membership labels and actual reasons. Outputs are new.
"""
from pathlib import Path
import sys,json,argparse,zipfile,posixpath,xml.etree.ElementTree as ET
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'tests'))
from fixture_xml import Fixture
from evaluate import evaluate
from read_candidate import labelled_code_list

ALL=['R001','R002','R003','R004','R005']
REF=TASK/'solution/reference.xlsx'

def run(out,category='lists',image_workbook=None):
    out.mkdir(parents=True,exist_ok=False)
    truth=json.loads((TASK/'solution/oracle.json').read_text())
    old=set(truth['previous_shortlist']);new=set(truth['shortlist'])
    def lists(f):
        for ri,(label,codes) in enumerate([
          ('Previous shortlist codes',truth['previous_shortlist']),
          ('• Authorities retained:',sorted(old&new)),
          ('Authorities entered',sorted(new-old)),
          ('Authorities left',sorted(old-new))],30):
            f.cell('Current briefing',f'A{ri}',label).cell('Current briefing',f'B{ri}',', '.join(codes))
        return f
    cases=[{'id':'reference','path':REF,'preserve':ALL}]
    def add(name,f,**kwargs):
        p=out/'fixtures'/(name+'.xlsx');f.save(p);cases.append({'id':name,'path':p,**kwargs})
    add('additional_correct_lists',lists(Fixture(REF)),preserve=ALL)
    f=lists(Fixture(REF).clear_sheet('Shortlist changes').cell('Current briefing','B13','Membership labels only; reasons not supplied.'))
    add('labels_without_reasons',f,preserve=[k for k in ALL if k!='R004'],lose=['R004'],r4=.8,reasons=False,labels=True)
    f=lists(Fixture(REF)).cell('Current briefing','B31',', '.join(sorted(old&new)+[sorted(old-new)[0]]))
    add('contradictory_retained_list',f,preserve=[k for k in ALL if k!='R004'],lose=['R004'],contradiction=sorted(old-new)[0])
    f=Fixture(REF).cell('Current briefing','A30','Unknown numeric result').cell('Current briefing','B30',sorted(new)[0]).cell('Current briefing','C30',123)
    add('unknown_numeric_row',f,status='JUDGE_ERROR')
    f=Fixture(REF).cell('Current briefing','A30','Authorities retained').cell('Current briefing','B30',sorted(old&new)[0]).cell('Current briefing','C30',123)
    add('list_label_with_extra_number',f,status='JUDGE_ERROR')
    if category=='images':cases=cases[:1]
    if category in ('images','all'):
        if image_workbook is None:raise ValueError('--image-workbook must supply the real static-chart artifact for image checks')
        with zipfile.ZipFile(image_workbook) as z:
            image=z.read('xl/media/image1.png')
            drawing=ET.fromstring(z.read('xl/drawings/drawing1.xml'))
        rid='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
        nsrel='http://schemas.openxmlformats.org/package/2006/relationships'
        nsmedia='http://schemas.openxmlformats.org/drawingml/2006/main'
        nscontent='http://schemas.openxmlformats.org/package/2006/content-types'
        for blip in drawing.findall('.//{'+nsmedia+'}blip'):blip.set(rid+'embed','rId1')
        f=Fixture(REF)
        media='xl/media/v32-static-chart.png';dp='xl/drawings/drawingV32Image.xml'
        f.parts[media]=image;f.parts[dp]=ET.tostring(drawing)
        dr=ET.Element('{'+nsrel+'}Relationships')
        ET.SubElement(dr,'{'+nsrel+'}Relationship',{'Id':'rId1','Type':rid[1:-1]+'/image','Target':'../media/v32-static-chart.png'})
        f.parts['xl/drawings/_rels/drawingV32Image.xml.rels']=ET.tostring(dr)
        sp=f.sheets['Current briefing'];rp=posixpath.dirname(sp)+'/_rels/'+posixpath.basename(sp)+'.rels'
        sr=ET.fromstring(f.parts[rp]) if rp in f.parts else ET.Element('{'+nsrel+'}Relationships')
        ET.SubElement(sr,'{'+nsrel+'}Relationship',{'Id':'rIdV32Image','Type':rid[1:-1]+'/drawing','Target':'../drawings/drawingV32Image.xml'})
        f.parts[rp]=ET.tostring(sr)
        root=f.root('Current briefing')
        ET.SubElement(root,'{http://schemas.openxmlformats.org/spreadsheetml/2006/main}drawing',{rid+'id':'rIdV32Image'})
        f.update('Current briefing',root)
        ct=ET.fromstring(f.parts['[Content_Types].xml'])
        ET.SubElement(ct,'{'+nscontent+'}Override',{'PartName':'/'+dp,'ContentType':'application/vnd.openxmlformats-officedocument.drawing+xml'})
        if not any(x.get('Extension')=='png' for x in ct):ET.SubElement(ct,'{'+nscontent+'}Default',{'Extension':'png','ContentType':'image/png'})
        f.parts['[Content_Types].xml']=ET.tostring(ct)
        add('attached_static_chart_image',f,status='JUDGE_ERROR',image_pending=True)
        f=Fixture(REF);f.parts[media]=image
        add('unattached_media_is_not_chart_evidence',f,preserve=ALL)
    checks=[]
    # Strict recognizer must not swallow arbitrary code lines or prose reasons.
    assert labelled_code_list(['Other figures','E07000148']) is None
    assert labelled_code_list(['Authorities retained','E07000148 because both comparisons deteriorated']) is None
    assert labelled_code_list(['Authorities retained','E07000148',2.5]) is None
    for c in cases:
        result=evaluate(c['path'],TASK/'data/input_files')
        (out/(c['id']+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
        try:
            assert result['evaluation_status']==c.get('status','SCORED'),result['evidence'].get('reason')
            if c.get('image_pending'):
                images=result['evidence'].get('embedded_chart_candidates',[])
                assert images and images[0]['sheet']=='Current briefing',images
                assert images[0]['media']=='xl/media/v32-static-chart.png',images
                assert result['score_decimal'] is None
            if result['evaluation_status']=='SCORED':
                facts=result['criterion_scores']
                for k in c.get('preserve',[]):assert facts[k]==1,(k,'preserve',facts[k])
                for k in c.get('lose',[]):assert facts[k]<1,(k,'lose',facts[k])
                if 'r4' in c:assert abs(facts['R004']-c['r4'])<1e-12,facts['R004']
                moves=result['evidence']['movement_facts']
                if 'reasons' in c:assert all(x['reason']==c['reasons'] for x in moves),moves
                if 'labels' in c:assert all(x['label']==c['labels'] for x in moves),moves
                if 'contradiction' in c:assert not next(x for x in moves if x['code']==c['contradiction'])['label']
                assert result['evidence']['denominators']['movement_authorities']==9
                assert result['evidence']['denominators']['required_support']==33
            checks.append({'id':c['id'],'passed':True,'status':result['evaluation_status'],'score':result['score_decimal']})
        except AssertionError as exc:checks.append({'id':c['id'],'passed':False,'error':str(exc)})
    receipt={'passed':all(c['passed'] for c in checks),'judge_version':'new6-b2-three-release-v3.2-labelled-code-lists','category':category,'checks':checks,'api_calls':0,'native_recalculations':0,'validation_budget':{'focused_suite_invocations':1,'cases':len(cases),'independent_reviews':0,'new_input_hashes':0},'unchanged':'task instruction, sources, reference, weights, fixed fact denominators'}
    (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print(json.dumps(receipt,ensure_ascii=False))
    return receipt['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--category',choices=['lists','images','all'],default='lists');p.add_argument('--image-workbook',type=Path);a=p.parse_args()
    sys.exit(0 if run(a.out,a.category,a.image_workbook) else 1)
