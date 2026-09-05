"""Three-release briefing update: source-correct and coherent handover facts.

No formula requirement, hidden hurdle, score cap, or answer-dependent selection
of candidate regions. See metadata/scoring_contract.md for fixed obligations.
"""
from pathlib import Path
import sys,json,argparse,re,hashlib
from decimal import Decimal,ROUND_HALF_UP
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'common'))
from runtime import output_status,score_profiles
from read_candidate import read,read_charts,ParsePending,norm,num,eq,population,mean,field,historic
TASK=Path(__file__).resolve().parents[1]

def published_equal(value,expected):
    """Compare numerical claims at the visible one-decimal reporting precision."""
    if expected is None:return num(value) is None
    actual=num(value);target=num(expected)
    return actual is not None and target is not None and actual.quantize(Decimal('.1'),rounding=ROUND_HALF_UP)==target.quantize(Decimal('.1'),rounding=ROUND_HALF_UP)

def evaluate(path,input_dir=None):
    evidence={'task_version':'new6-b2-three-release-v3','judge_version':'new6-b2-three-release-v3.1-actual-equivalence','candidate':str(path),'dynamic_tests':'Not required; correct static and formula implementations equally accepted.'}
    status=output_status(path)
    if status:return score_profiles(TASK/'rubric.json',status=status,evidence=evidence)
    if input_dir is None:return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'reason':'Post-run input directory required to observe preservation.'})
    try:
        regions,lines,unbound=read(path);chart_evidence=read_charts(path)
    except Exception as exc:
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'reason':str(exc),'exception':type(exc).__name__})
    if unbound or not regions:
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'reason':'Potential authority results cannot be bound safely; supported-reader limit, not business failure.','unbound':unbound[:8]})
    truth=json.loads((TASK/'solution/oracle.json').read_text());expected={x['code']:x for x in truth['panel']}
    current=[t for t in regions if t['role']!='previous'];rows=[x for t in current for x in t['rows']]
    tops=[t for t in current if t['role']=='shortlist' or (t['role']=='movement' and 'rank' in t['columns'])]
    by={}
    for row in rows:by.setdefault(row['code'],[]).append(row)
    current_lines=[x for x in lines if not x['historical']];joined='\n'.join(x['text'] for x in current_lines).lower()
    alltext='\n'.join(x['text'] for x in lines).lower()
    mismatches=[]
    def observe(code,key):
        values=[]
        for row in by.get(code,[]):
            if key in row:values.append({'value':row[key],'location':row['_loc'],'method':'explicit displayed result'})
            elif '_change_' in key:
                metric,pair=key.split('_change_');a,b=pair.split('_')
                left,right=num(row.get(metric+'_20'+a)),num(row.get(metric+'_20'+b))
                if left is not None and right is not None:values.append({'value':str(right-left),'location':row['_loc'],'method':'difference of candidate displayed published rates'})
        return values
    def checked(code,key):
        obs=observe(code,key);ok=bool(obs) and all(published_equal(x['value'],expected[code][key]) for x in obs)
        if not ok:mismatches.append({'code':code,'field':key,'expected':expected[code][key],'candidate':obs})
        return ok
    # R001: fixed context buckets and all genuinely unassessable authorities.
    periods=[bool(re.search(r'oct[^\n]*'+a+r'[^\n]*sep[^\n]*'+b,joined)) for a,b in [('2021','2022'),('2022','2023'),('2023','2024')]]
    definitions=[bool(re.search(r'16\s*[–—-]\s*64',joined)),bool(re.search(r'16\+|16\s*(?:and|or)\s*(?:over|above)',joined)) and 'economically active' in joined]
    source_ids=[('li01' in joined or 'ons.gov.uk' in joined) and (f'january {y}' in joined or f'ons_li01_january{y}' in joined or (y=='2023' and '2023 corrected' in joined)) for y in ['2023','2024','2025']]
    units='percentage point' in joined or bool(re.search(r'\bpp\b',joined))
    exclusions=[]
    for code,x in expected.items():
        if not x['missing']:continue
        reasons=[str(row.get('reason') or row.get('_text','')).lower() for row in by.get(code,[]) if row.get('reason') or row.get('eligible') in ['Unavailable','Not comparable','Excluded']]
        reason_ok=bool(reasons) and any(any(w in t for w in ['absent','not present','unavailable','suppress','missing','not available','reorgan','boundary']) for t in reasons)
        not_imputed=all(num(row.get(m['metric']+'_'+m['year'])) is None for row in by.get(code,[]) for m in x['missing'] if m['metric']+'_'+m['year'] in row)
        exclusions.append({'code':code,'reason':reason_ok,'not_imputed':not_imputed,'candidate_reasons':reasons})
    scope_ok=bool(rows) and all(str(row['code']).startswith(('E06','E07','E08','E09')) for row in rows)
    limits=any(x in joined for x in ['sampling','uncertain','variability','confidence interval','not statistically','do not establish statistical'])
    r1=mean([mean(periods),mean(definitions),mean(source_ids),units,scope_ok,limits,mean([x['reason'] and x['not_imputed'] for x in exclusions])])
    # R002: separate multisets and ranks for every explicit current shortlist.
    chosen=truth['shortlist'];selection=[]
    for region in tops:
        actual=[x for x in region['rows'] if region['role']!='movement' or num(x.get('rank')) is not None];codes=[x['code'] for x in actual]
        order=[]
        for rank,code in enumerate(chosen,1):
            matches=[x for i,x in enumerate(actual,1) if eq(x.get('rank',i),rank)]
            order.append(len(matches)==1 and matches[0]['code']==code)
        selection.append({'sheet':region['sheet'],'codes':codes,'population':population(codes,chosen),'order':order})
    r2=mean([mean([x['population'] for x in selection]),mean([mean(x['order']) for x in selection])])
    # R003: 25 current supporting deltas, 8 second-interval deltas explaining
    # the four departures; all other displayed source/delta claims must agree.
    keys=['employment_change_23_24','employment_change_24_25','unemployment_change_23_24','unemployment_change_24_25','unemployment_change_23_25']
    obligations=[(code,k) for code in chosen for k in keys]
    departed=[code for code in truth['previous_shortlist'] if code not in chosen]
    obligations.extend((code,k) for code in departed for k in ['employment_change_24_25','unemployment_change_24_25'])
    support=[checked(code,k) for code,k in obligations]
    optional=[];optional_errors=[]
    for row in rows:
        if row['code'] not in expected:continue
        for key,value in row.items():
            if key in expected[row['code']] and (key.startswith('employment_') or key.startswith('unemployment_')):
                ok=published_equal(value,expected[row['code']][key]);optional.append(ok)
                if not ok:optional_errors.append({'location':row['_loc'],'code':row['code'],'field':key,'value':value,'expected':expected[row['code']][key]})
    r3=mean(support)*.8+(bool(optional) and all(optional))*.2
    # R004: current charts, actual explanation of movement, and coherent brief.
    chart_checks=[];current_chart_count=0;covered=set();chart_integrity=[]
    names={norm(c):c for c in expected}
    for c,x in expected.items():
        for name in [x['name'],*x.get('name_aliases',[])]:names[norm(name)]=c
    for chart in chart_evidence:
        if chart['historical']:continue
        current_chart_count+=1
        for ser in chart['series']:
            key=field(ser['name'])
            if key is None or not key.startswith(('employment_','unemployment_')):
                return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'reason':'Current chart metric/period label cannot be bound.','series_name':ser['name']})
            codes=[names.get(norm(x),str(x)) for x in ser['categories']]
            vals=ser['values'];unit=[]
            # Every displayed point is checked against its stated metric. A
            # correct context graph need not repeat the shortlist's five codes.
            for code,value in zip(codes,vals):
                correct=code in expected and key in expected[code] and published_equal(value,expected[code][key])
                unit.append(correct)
                if correct and code in chosen:covered.add(code)
            caption=(chart['title']+' '+chart['sheet']).lower()
            if any(x in caption for x in ['previous and current','old and new','shortlist comparison']):
                unit.append(population(codes,set(truth['previous_shortlist'])|set(chosen))==1)
            elif any(x in caption for x in ['all qualifying','all eligible']):unit.append(population(codes,truth['eligible_codes'])==1)
            elif 'shortlist' in caption and 'context' not in caption:unit.append(population(codes,chosen)==1)
            for kind in ['categories','values']:
                cache=ser[kind+'_cache']
                unit.append(not cache or (len(cache)==len(ser[kind]) and all(eq(a,b) if kind=='values' else str(a)==str(b) for a,b in zip(cache,ser[kind]))))
            chart_checks.append({'chart':chart['chart'],'metric':key,'facts':unit});chart_integrity.extend(unit)
    chart_score=(mean([c in covered for c in chosen])*.5+bool(chart_integrity and all(chart_integrity))*.5) if current_chart_count else 0
    movement_checks=[]
    oldset=set(truth['previous_shortlist']);newset=set(chosen)
    exclusion_locations={x['_loc'] for t in current if t['role']=='exclusions' for x in t['rows']}
    def mentions(text,code):
        identifiers=re.findall(r'\bE\d{8}\b',text)
        if identifiers:return code in identifiers
        return bool(re.search(r'(?<!\w)'+re.escape(expected[code]['name'])+r'(?!\w)',text,re.I))
    for code in sorted(oldset|newset):
        want='retained' if code in oldset&newset else 'entered' if code in newset else 'left'
        candidates=[x for x in by.get(code,[]) if x.get('movement') is not None]
        candidates.extend({**x,'movement':'Excluded','from_exclusion':True} for x in by.get(code,[]) if x['_loc'] in exclusion_locations and x.get('reason'))
        # Explicit authority-linked prose is an equally valid business brief.
        for line in current_lines:
            t=line['text'];body=t.lower()
            if len(re.findall(r'E\d{8}',t))>1:
                segments=[part for part in t.split(';') if mentions(part,code)]
                body='; '.join(segments).lower()
            if mentions(t,code) and len(t)>45 and re.search(r'\b(retain|retained|remains?|stay|stayed|entered|new entrant|added|left|exited|removed|dropped)\b',body) and not any(x['_loc']==f"{line['sheet']}!{line['row']}" for x in candidates):
                candidates.append({'movement':body,'reason':body,'_loc':f"{line['sheet']}!{line['row']}",'_text':t,'from_prose':True})
        synonyms={'retained':['retained','remain','unchanged','stayed'],'entered':['entered','new','added'],'left':['left','exit','removed','drop','excluded']}
        def positive_word(text,word):
            for m in re.finditer(r'\b'+word+r'\w*\b',text):
                if not re.search(r'\b(?:no|not|never|without)\s+(?:\w+\s+){0,2}$',text[max(0,m.start()-32):m.start()]):return True
            return False
        labels=bool(candidates) and all(any(positive_word(str(x['movement']).lower(),w) for w in synonyms[want]) for x in candidates)
        if not candidates:
            possible=[x for x in current_lines if mentions(x['text'],code) and re.search(r'\b(because|shortlist|comparison|review)\b',x['text'],re.I) and len(x['text'])>60]
            if possible:
                return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'reason':'Authority-linked explanation may be present but its meaning is not safely bound.','authority':code,'candidate_prose':possible})
        reason_text=[str(x.get('reason') or '').lower() for x in candidates]
        reason=False
        if want=='left':
            for text in reason_text:
                unemployment=expected[code]['unemployment_change_24_25'];employment=expected[code]['employment_change_24_25']
                reason |= (num(unemployment)<=0 and 'unemployment' in text and bool(re.search(r'not rise|didn.t rise|fell|fall|declin|decreas|negative|improv',text))) or (num(employment)>=0 and 'employment' in text and bool(re.search(r'not fall|didn.t fall|rose|risen|increas|positive|improv',text)))
        else:reason=any(('both' in x or 'consecutive' in x or 'two' in x) and any(positive_word(x,w) for w in ['deteriorat','qualif','rose','increase']) and any(positive_word(x,w) for w in ['rank','five','top','largest']) and not re.search(r'not\s+(?:in|among|within)\s+(?:the\s+)?(?:top|five)|did\s+not\s+deteriorat',x) for x in reason_text)
        movement_checks.append({'code':code,'expected':want,'label':labels,'reason':bool(reason),'candidate':candidates})
    brief_lines=[x['text'] for x in current_lines if re.search(r'brief|summary|report|overview',x['sheet'],re.I)]
    count_claims=[]
    wanted_counts={'current selected count':5,'retained from previous count':1,'entered count':4,'left count':4,'qualifying authorities':truth['counts']['eligible'],'three-period comparable count':truth['counts']['three_period_comparable'],'in-scope union':truth['counts']['union']}
    for line in brief_lines:
        for label,value in wanted_counts.items():
            if line.lower().startswith(label+' ||'):
                count_claims.append(eq(line.split('||')[-1].strip(),value))
        if line.lower().startswith('current selected codes ||'):
            count_claims.append(population(re.findall(r'E\d{8}',line),chosen)==1)
    brief_ok=bool(brief_lines) and (not count_claims or all(count_claims))
    r4=chart_score*.45+mean([mean([x['label'],x['reason']]) for x in movement_checks])*.4+brief_ok*.15
    # R005: previous analysis is a preserved artifact, not a required layout.
    manifest=json.loads((TASK/'metadata/source_manifest.json').read_text())
    protection=[]
    for source in manifest['sources']:
        p=Path(input_dir)/source['filename']
        protection.append(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256'])
    previous=Path(input_dir)/'previous_briefing.xlsx';reference_previous=TASK/'data/input_files/previous_briefing.xlsx'
    external_available=previous.is_file() and previous.read_bytes()==reference_previous.read_bytes() and 'previous_briefing.xlsx' in alltext
    oldregions=[t for t in regions if t['role']=='previous'];oldrows=[x for t in oldregions for x in t['rows']]
    old_claims=[]
    for row in oldrows:
        if row['code'] not in expected:continue
        for key,value in row.items():
            if key in expected[row['code']] and key.startswith(('employment_','unemployment_')) and not key.endswith('25'):
                old_claims.append(published_equal(value,expected[row['code']][key]))
    oldtops=[t for t in oldregions if 'old_rank' in t['columns'] or 'rank' in t['columns'] or re.search(r'shortlist',t['context'],re.I)]
    old_top_ok=bool(oldtops) and all(population([x['code'] for x in t['rows']],truth['previous_shortlist'])==1 and all(eq(x.get('old_rank',x.get('rank',i+1)),truth['previous_shortlist'].index(x['code'])+1) for i,x in enumerate(t['rows']) if x['code'] in truth['previous_shortlist']) for t in oldtops)
    old_chart=any(x['historical'] for x in chart_evidence)
    old_chart_checks=[]
    for chart in chart_evidence:
        if not chart['historical']:continue
        for ser in chart['series']:
            key=field(ser['name']);codes=[names.get(norm(x),str(x)) for x in ser['categories']]
            if key is None:
                return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'reason':'Historical chart metric cannot be bound.'})
            good=population(codes,truth['previous_shortlist'])==1 and all(c in expected and key in expected[c] and eq(v,expected[c][key]) for c,v in zip(codes,ser['values']))
            for kind in ['categories','values']:
                cache=ser[kind+'_cache']
                good &= not cache or (len(cache)==len(ser[kind]) and all(eq(a,b) if kind=='values' else str(a)==str(b) for a,b in zip(cache,ser[kind])))
            old_chart_checks.append(good)
    old_data=any({'employment_2023','employment_2024','unemployment_2023','unemployment_2024'}<=set(t['columns']) and bool(t['rows']) for t in oldregions)
    old_exclusions=any('reason' in t['columns'] and bool(t['rows']) for t in oldregions)
    old_brief=any(x['historical'] and 'brief' in x['sheet'].lower() for x in lines)
    historical_components={'data':old_data,'shortlist':old_top_ok,'brief':old_brief,'exclusions':old_exclusions,'chart':old_chart}
    embedded_available=mean(historical_components.values())
    previous_available=1 if external_available else embedded_available
    old_consistent=(not old_claims or all(old_claims)) and (not oldtops or old_top_ok) and (not old_chart_checks or all(old_chart_checks))
    r5=mean([previous_available,previous_available*old_consistent,mean(protection)])
    facts=dict(zip(['R001','R002','R003','R004','R005'],[r1,r2,r3,r4,r5]))
    evidence.update(regions=[{k:t[k] for k in ['sheet','header_row','role','columns']} for t in regions],
      context={'periods':periods,'definitions':definitions,'sources':source_ids,'units':units,'scope':scope_ok,'sampling_limits':limits},
      exclusion_facts=exclusions,selection_facts=selection,support_obligations=[{'code':c,'field':k,'correct':v} for (c,k),v in zip(obligations,support)],
      source_value_mismatches=mismatches,optional_displayed_errors=optional_errors,chart_facts=chart_checks,chart_evidence=chart_evidence,
      movement_facts=movement_checks,brief_facts={'exists':bool(brief_lines),'claims':count_claims},
      preservation={'external_available':external_available,'embedded_available':embedded_available,'historical_components':historical_components,'embedded_consistent':old_consistent,'sources_unchanged':protection},
      denominators={'current_selected':5,'required_support':len(obligations),'movement_authorities':len(oldset|newset),'unassessable_authorities':len(exclusions),'context_buckets':7},
      external_acceptance_gaps=['Formal difficulty validation pending','External negative-item and agentic parser acceptance not asserted'])
    return score_profiles(TASK/'rubric.json',facts,evidence=evidence)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('answer',nargs='?',default='/app/output/answer.xlsx');p.add_argument('--input-dir');p.add_argument('--result');a=p.parse_args()
    result=evaluate(Path(a.answer),a.input_dir);s=json.dumps(result,ensure_ascii=False,indent=2)
    if a.result:Path(a.result).write_text(s)
    print(s)
