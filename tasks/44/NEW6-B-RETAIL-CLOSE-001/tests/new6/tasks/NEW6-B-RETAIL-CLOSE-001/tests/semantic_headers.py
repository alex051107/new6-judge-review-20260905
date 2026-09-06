"""Observed business header vocabulary and explicitly labelled period roles."""
import re

EXTRA={
 'metric':['kpi','measure','octoberinperiodclassification','octobersourcescopecontrol'],
 'value':['gbp','valuegbp','valuepounds','amountpounds'],
 'class':['type','treatment','scopeclass'],
 'amount':['signedlineamount','signedlineamountgbp','signedamountgbp','amountsigned','sourceamount','calculatedamount','calculatedamountgbp','linevalue','calculableamount','calculableamountgbp','amountcalculable','totalvalue','totalvaluegbp'],
 'count':['transactioncount','transactions','lines','numberoflines','occurrencecount'],
 'period':['periodcheck','period','month','reportingperiod'],
 'extract':['extract','sourcefile','periodfile'],
 'included':['included','includedanalysis','analysisincluded'],
 'scope':['periodscope','scope','scopedecision','scopestatus'],
 'missing_customer':['missingcustomeridissue','customeridmissing'],
 'reason':['reasons','exceptiontype'],
 'sale_amount':['sale','salesvalue','salevalue','salevaluegbp'],
 'credit_amount':['credit','signedcredits','signedcreditsgbp','creditssigned','creditsamount','creditvalue','creditvaluegbp'],
 'exception_amount':['exception','exceptionsvalue','exceptionvaluecalculable','exceptionamountgbp','exceptiongbp'],
 'sale_count':['salesrows','salerows'],
 'credit_count':['creditrows','creditsrows','creditslines'],
 'exception_count':['exceptionrows','exceptionsrows'],
 'component':['bridgecontribution','step','maincontributions','bridgestep','bridgeitem','maincontributions','contributiondriver'],
 'bridge_amount':['unroundedgbpvalue','unroundedgbp','contributiongbpunrounded','amountunrounded'],
 'q_sep':['septquantity','septsalesqty','septqty','sept_sales_qty','sepsalesqty','septembersalesqty'],
 'q_oct':['octsalesqty','octobersalesqty'],
 'v_sep':['septsalesvalue','septvalue','sepvaluegbp','sepsalesgbp','septembersalesgbp','septembersalesvaluegbp'],
 'v_oct':['octvaluegbp','octsalesgbp','octobersalesgbp','octobersalesvaluegbp'],
 'p_sep':['sepsalesweightedprice','septsalesweightedprice','sepsalesweightedunitprice','septweightedprice','septemberweightedprice','septemberweightedunitprice','sepprice','septwup'],
 'p_oct':['octsalesweightedprice','octsalesweightedunitprice','octoberweightedprice','octoberweightedunitprice','octprice','octwup'],
 'qty_effect':['quantitycontributiongbp','qtycontribution','qtycontributiongbp','qtycontributioncont'],
 'price_effect':['pricemixcontrib','pricemixcontribution','pricemixcontributiongbp','pricemixcontributioncont','pricetransactionmixcontribution','pricecontrib'],
 'entry_effect':['newskucontribution','newskucontrib','newcontrib','newcontribution','newskucontributiongbp'],
 'exit_effect':['exitedskucontribution','exitskucontrib','exitcontrib','exitedcontrib','exitedcontribution','exitedskucontributiongbp'],
 'sku_contribution':['skucontribution'],
}

_VOCABULARY={}
def headers(values,lookup,norm):
    vocabulary=_VOCABULARY.get(id(lookup))
    if vocabulary is None:
        vocabulary=dict(lookup)
        for key,names in EXTRA.items():
            for name in names:vocabulary[norm(name)]=key
        _VOCABULARY[id(lookup)]=vocabulary
    ns=[norm(v) for v in values];sku='stockcode' in ns or 'productcode' in ns
    period_wide=not sku and any(re.match(r'(?:oct|october)(?:sale|credit|exception)',n) for n in ns)
    result={}
    for i,n in enumerate(ns):
        if period_wide:
            if re.match(r'(?:sep|sept|september)(?:sale|credit|exception|net|signed)',n):continue
            n=re.sub(r'^(?:october|oct)(?=sale|credit|exception|net|signed)','',n)
        role=vocabulary.get(n)
        if role:
            if role in result and role not in ['value','bridge_amount']:
                # Repeated semantic roles require an explicit period or split region.
                result.setdefault('_duplicate_roles',[]).append(role)
            result[role]=i
        if re.fullmatch(r'(?:october|oct)(?:2011|gbp|2011gbp)?',n):result['oct_report']=i
        if re.fullmatch(r'(?:september|sept|sep)(?:2011|gbp|2011gbp)?',n):result['sep_report']=i
    if 'class' in result and 'value' in result and 'amount' not in result:result['amount']=result['value']
    return result

def month(v):
    text=str(v or '').lower()
    sep=bool(re.search(r'september|\bsept?\b|2011[-/]09',text))
    octo=bool(re.search(r'october|\boct\b|2011[-/]10',text))
    return 'sep' if sep and not octo else 'oct' if octo and not sep else None

def october_row(row,sheet):
    """Choose a labelled analysis period; never choose by expected values."""
    extract=str(row.get('extract') or '').lower()
    if 'september_extract' in extract:return False
    if 'retail_extract' in extract:return True
    selected=month(extract) or month(row.get('period')) or month(sheet)
    return selected!='sep'

def apply_scope(row,norm):
    scope=norm(row.get('scope'))
    if 'included' in row and (row['included'] is False or norm(row['included']) in ['false','no','0']):scope='outside'
    if scope in ['septembercontext','september','novembercontext','november']:scope='outside'
    if any(s in scope for s in ['outside','outofscope','outofperiod','excluded','beforeoctober','afteroctober']):
        row['_reported_business_class']=row.get('class');row['class']='outside_scope'
