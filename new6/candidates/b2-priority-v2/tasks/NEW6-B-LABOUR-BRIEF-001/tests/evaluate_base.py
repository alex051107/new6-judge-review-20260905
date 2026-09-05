"""Conservative NEW6 B labour evaluator. Same facts feed all frozen profiles."""
from pathlib import Path
import sys,json,hashlib,argparse,re
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'common'))
from runtime import score_profiles,output_status
from read_candidate import tables,charts,ParsePending,norm,num,eq,population,consensus_rows,mean
TASK=Path(__file__).resolve().parents[1]
SPECS={'panel':{'code','employment_old','employment_new','unemployment_old','unemployment_new','employment_change','unemployment_change'},
 'exclusions':{'code','reason'},'top':{'rank','code','employment_change','unemployment_change'},
 'sources':{'code','edition','metric','raw','source'}, 'report':{'metric','value'}}

def evaluate(path,input_dir=None):
    evidence={'candidate':str(path),'reader':'semantic headers and physical identifiers; OOXML chart references/caches','dynamic_tests':'not applicable; static fully accepted'}
    status=output_status(path)
    if status:return score_profiles(TASK/'rubric.json',status=status,evidence=evidence)
    if input_dir is None:
        evidence['reason']='Run input directory is required to observe source preservation.'
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    try:
        ts,text=tables(path,SPECS);chart_evidence=charts(path)
    except ParsePending as exc:
        evidence['reason']=str(exc);return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    except Exception as exc:
        evidence['reason']=type(exc).__name__+': '+str(exc);return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    if not any(ts.values()):
        evidence['reason']='Populated workbook cannot be semantically bound by this reader; manual/agentic parse required.'
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    if not ts['panel'] and any(x.startswith('__UNBOUND__') and re.search(r'\bE0[6789]\d{6}\b',x) for x in text):
        evidence['reason']='Authority results may be present but required metric columns cannot be semantically bound; manual/agentic parse required.'
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    truth=json.loads((TASK/'solution/oracle.json').read_text());manifest=json.loads((TASK/'metadata/source_manifest.json').read_text())
    expected={r[0]:r for r in truth['panel']}
    comparable={code:r for code,r in expected.items() if r[6] is not None and r[7] is not None}
    rows,by=consensus_rows(ts['panel'],'code')
    exrows=[r for t in ts['exclusions'] for r in t['rows'] if r.get('code')]
    exby={}
    for r in exrows:exby.setdefault(str(r['code']),[]).append(r)
    reps=[r for region in ts['report'] for r in region['rows'] if r.get('metric')]
    report={}
    for r in reps:report.setdefault(norm(r['metric']),[]).append(r['value'])
    def report_text(key,pred):
        explicit=report.get(norm(key))
        if explicit:return all(pred(str(x)) for x in explicit)
        return any(pred(str(x)) for x in text)
    context=[
      report_text('earlier edition',lambda x:'2024' in x and 'january' in x.lower()),
      report_text('later edition',lambda x:'2025' in x and 'january' in x.lower()),
      report_text('earlier observation window',lambda x:'2022' in x and '2023' in x and 'oct' in x.lower() and 'sep' in x.lower()),
      report_text('later observation window',lambda x:'2023' in x and '2024' in x and 'oct' in x.lower() and 'sep' in x.lower()),
      report_text('employment denominator',lambda x:'16' in x and '64' in x and ('age' in x.lower() or 'population' in x.lower())),
      report_text('unemployment denominator',lambda x:'16' in x and 'economically active' in x.lower()),
      report_text('change units',lambda x:'percentage point' in x.lower() or bool(re.search(r'\b(?:change|threshold)[^\n]*\bpp\b',x,re.I))),
      not any(re.search(r'\b(caused by|causal effect|statistically significant|significant increase)\b',x,re.I) and not re.search(r'\b(no|not|without|cannot)\b',x,re.I) for x in text)]
    identity=mean([bool(by.get(code) or exby.get(code)) and all(norm(r.get('name'))==norm(ex[1]) for r in by.get(code,[])+exby.get(code,[])) for code,ex in expected.items()])
    r1=mean([mean(context),identity])
    # Each final panel representation is checked separately, so duplicating or
    # contradicting an existing panel cannot be hidden by overwriting a dict.
    def is_comparison(r):
        code=str(r.get('code'))
        return code in comparable or num(r.get('employment_change')) is not None or num(r.get('unemployment_change')) is not None
    panel_pop=population([str(r.get('code')) for r in rows if is_comparison(r)],comparable)
    exkeys=[];expanded=[]
    for r in exrows:
        code=str(r['code'])
        if code not in expected:continue # transparent out-of-scope appendix is permitted
        label=norm(r.get('metric'));reason=str(r.get('reason') or '')
        metrics=[label] if label in ['employment','unemployment'] else []
        if not metrics:
            if re.search(r'\bunemployment\b',reason,re.I):metrics.append('unemployment')
            if re.search(r'(?<!un)\bemployment\b',reason,re.I):metrics.append('employment')
            if re.search(r'\bboth (?:rates|indicators)\b',reason,re.I):metrics=['employment','unemployment']
        for metric in metrics:exkeys.append((code,metric));expanded.append((code,metric,r))
    expected_ex=[(r[0],r[2]) for r in truth['exclusions']]
    reasons=[]
    for code,metric in expected_ex:
        matches=[r for c,m,r in expanded if c==code and m==metric]
        reasons.append(bool(matches) and all(any(t in str(r.get('reason','')).lower() for t in ['suppress','unavail','missing','[x]','[c]']) for r in matches))
    r2=mean([panel_pop,population(exkeys,expected_ex),mean(reasons)])
    source_scores=[];delta_scores=[];candidate_consistency=[];mismatches=[]
    fields=['employment_old','employment_new','unemployment_old','unemployment_new','employment_change','unemployment_change']
    for code,ex in comparable.items():
        for j,key in enumerate(fields,2):
            ok=bool(by.get(code)) and all(eq(r.get(key),ex[j]) for r in by[code])
            (source_scores if j<6 else delta_scores).append(ok)
            if not ok and len(mismatches)<30:mismatches.append({'code':code,'field':key,'expected':ex[j],'candidate':[r.get(key) for r in by.get(code,[])]})
        for r in by.get(code,[]):
            for p in ['employment','unemployment']:
                a,b=num(r.get(p+'_old')),num(r.get(p+'_new'))
                candidate_consistency.append(eq(r.get(p+'_change'),None if a is None or b is None else b-a))
    optional_source_ok=all(eq(r.get(key),ex[j]) for code,ex in expected.items() if code not in comparable for r in by.get(code,[]) for j,key in enumerate(fields,2))
    r3=mean([mean(source_scores+[optional_source_ok]),mean(delta_scores)])
    tops=[r for t in ts['top'] for r in t['rows'] if r.get('code')]
    top_facts=[]
    for rank,code,name,un,em in truth['top5']:
        cand=[r for r in tops if eq(r.get('rank'),rank)]
        for key,value in [('code',code),('unemployment_change',un),('employment_change',em)]:
            top_facts.append(bool(cand) and all(str(r.get(key))==value if key=='code' else eq(r.get(key),value) for r in cand))
    top_population=mean([population([str(r.get('code')) for r in t['rows'] if r.get('code')],[r[1] for r in truth['top5']]) for t in ts['top']])
    top_consistency=[]
    for rank,code,name,un,em in truth['top5']:
        top_matches=[r for r in tops if str(r.get('code'))==code]
        detail_matches=by.get(code,[])
        for metric in ['employment_change','unemployment_change']:
            top_consistency.append(bool(top_matches) and bool(detail_matches) and all(eq(a.get(metric),b.get(metric)) for a in top_matches for b in detail_matches))
    r4=mean([mean(top_facts),top_population,mean(top_consistency)])
    chart_facts=[];chart_self=[];all_metrics_seen=set()
    accepted_names={r[1]:r[2] for r in truth['top5']}
    for chart in chart_evidence:
        series=chart['series'];metrics_seen=set()
        for ser in series:
            categories=[str(x) for x in ser['categories']]
            codes=[next((c for c,name in accepted_names.items() if norm(x) in [norm(c),norm(name)]),x) for x in categories]
            label=norm(ser.get('name'))
            if 'unemployment' in label:metric='unemployment'
            elif 'employment' in label:metric='employment'
            else:
                evidence['reason']='Chart series metric cannot be identified from its label.'
                return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
            metrics_seen.add(metric);idx=3 if metric=='unemployment' else 4
            expected_values={r[1]:r[idx] for r in truth['top5']}
            chart_facts.append(population(codes,accepted_names))
            bound=list(zip(codes,ser['values']))
            for code,value in expected_values.items():
                actual=[v for c,v in bound if c==code]
                chart_facts.append(len(actual)==1 and eq(actual[0],value))
            for label in ['categories','values']:
                cache=ser[label+'_cache']
                good=not cache or (len(cache)==len(ser[label]) and all(eq(a,b) if label=='values' else str(a)==str(b) for a,b in zip(cache,ser[label])))
                chart_facts.append(good);chart_self.append(good)
        all_metrics_seen.update(metrics_seen)
    # The visible task requests the selected areas' employment comparison.
    # Additional unemployment series may share a chart or be separate.
    chart_facts.append('employment' in all_metrics_seen)
    r5=mean(chart_facts)
    sources=[r for t in ts['sources'] for r in t['rows'] if r.get('code')]
    source_units=[]
    joined='\n'.join(text).lower()
    filename_sources=all(src['filename'].lower() in joined for src in manifest['sources'])
    named_releases=('ons' in joined and 'li01' in joined and
                    all(re.search(r'\bjanuary\s+'+year+r'\b',joined) for year in ['2024','2025']))
    declared_sources=(filename_sources or named_releases) and 'li01' in joined
    indirect_trace=[]
    for code,edition,metric,raw,pub,loc in truth['provenance']:
        matches=[r for r in sources if str(r.get('code'))==code and norm(r.get('edition'))==norm(edition) and norm(r.get('metric'))==metric]
        if matches:
            source_units.append(all((eq(r.get('raw'),raw) if num(raw) is not None else str(r.get('raw'))==raw) and loc.split('#')[0].lower() in str(r.get('source','')).lower() and 'li01' in str(r.get('source','')).lower() for r in matches))
        else:
            linked=declared_sources and bool(by.get(code) or exby.get(code))
            source_units.append(linked)
            if linked:indirect_trace.append({'code':code,'edition':edition,'metric':metric,'method':'declared source filename + LI01 + delivered geography code; raw numbers retained in preserved source input'})
    protection=[];protection_evidence=[]
    from source_protection import compare_source
    for src in manifest['sources']:
        p=Path(input_dir)/src['filename'];match=p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==src['sha256']
        detail={'state':'IDENTICAL_SOURCE_BYTES'}
        if not match:
            match,detail=compare_source(TASK/'data/input_files'/src['filename'],p)
            if match is None:
                evidence.update(reason=detail['reason'],source_protection_pending=detail)
                return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
        protection.append(match);protection_evidence.append(detail)
    r6=mean([mean(source_units),mean(protection)])
    facts=dict(zip(['R001','R002','R003','R004','R005','R006'],[r1,r2,r3,r4,r5,r6]))
    evidence.update(candidate_tables={k:[{'sheet':t['sheet'],'header_row':t['header_row'],'row_count':len(t['rows'])} for t in v] for k,v in ts.items()},
      context_facts=dict(zip(['earlier_edition','later_edition','earlier_observation_window','later_observation_window','employment_denominator','unemployment_economically_active_denominator','percentage_point_units','no_unsupported_affirmative_causal_or_significance_claim'],context)),
      exclusion_pair_facts=[{'code':c,'metric':m,'reason_evidenced':bool(v)} for (c,m),v in zip(expected_ex,reasons)],
      source_value_mismatches=mismatches,candidate_delta_self_consistency=mean(candidate_consistency),candidate_top5_self_consistency=mean(top_consistency),source_protection=protection,source_protection_evidence=protection_evidence,
      chart_cache_self_consistency=chart_self,chart_evidence=chart_evidence,
      indirect_source_trace_count=len(indirect_trace),
      denominators={'eligible_codes':296,'comparable_codes':294,'source_rate_units':1176,'optional_displayed_source_consistency_units':1,'delta_units':588,'exclusion_pairs':4,'top5_numeric_identity_units':15,'source_trace_units':1184},
      external_acceptance_gaps=['No external negative-item/agentic parser acceptance claimed','Natural Agent attempt not included in calibration'])
    return score_profiles(TASK/'rubric.json',facts,evidence=evidence)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('answer',nargs='?',default='/app/output/answer.xlsx');p.add_argument('--input-dir');p.add_argument('--result');a=p.parse_args()
    result=evaluate(Path(a.answer),a.input_dir);out=json.dumps(result,ensure_ascii=False,indent=2)
    if a.result:Path(a.result).write_text(out)
    print(out)
