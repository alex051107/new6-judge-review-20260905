"""Task-specific Decimal Oracle for the author's September 2018 Amazon model.
Raw inputs only. No candidate cells and no cached source forecasts are consumed.
The circular lease/synthetic-rating relation is solved by enumerating the finite
published rating bands and requiring a self-consistent band, not by fitting gold.
"""
from decimal import Decimal, getcontext, ROUND_HALF_UP
from pathlib import Path
import json, openpyxl
getcontext().prec=40
D=lambda v: Decimal(str(v))
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source/AmazonSept18.xlsx'

def raw_inputs():
 w=openpyxl.load_workbook(SOURCE,data_only=False)
 s=w['Input sheet'];l=w['Operating lease converter'];rd=w['R& D converter'];syn=w['Synthetic rating']
 p={k:D(s[c].value) for k,c in dict(revenue='B8',ebit='B9',interest='B10',equity_book='B11',debt='B12',cash='B15',nonoperating='B16',minority='B17',shares='B18',price='B19',marginal_tax='B21',growth='B23',margin='B24',convergence='B25',riskfree='B28',discount='B29',terminal_discount='B40',terminal_roc='B43').items()}
 p['tax']=D(769)/D(3806) # the source input is the printed formula =769/3806
 p['lease_expense']=D(l['E4'].value);p['leases']=[D(l.cell(r,2).value) for r in range(7,13)]
 p['rd_current']=D(rd['F7'].value);p['rd_years']=int(rd['F6'].value);p['rd_history']=[D(rd.cell(r,2).value) for r in range(11,11+p['rd_years'])]
 p['bands']=[(D(syn.cell(r,1).value),D(syn.cell(r,4).value)) for r in range(19,34)]
 assert s['B13'].value==s['B14'].value=='Yes' and s['B31'].value=='No'
 assert s['B42'].value==s['B39'].value=='Yes'
 assert all(s[c].value=='No' for c in ['B45','B50','B52','B55','B58'])
 return p

def compute(growth_delta=0,margin_delta=0,discount_delta=0,review=False):
 p=raw_inputs();p['growth']+=D(growth_delta);p['margin']+=D(margin_delta)-(D('.02') if review else 0);p['discount']+=D(discount_delta)
 l=p['leases'];n=int((l[5]/(sum(l[:5])/5)).quantize(D(1),rounding=ROUND_HALF_UP));valid=[]
 for lower,spread in p['bands']:
  r=p['riskfree']+spread
  debt=sum(v/(1+r)**(i+1) for i,v in enumerate(l[:5]))+(l[5]/n)*(1-(1+r)**(-n))/r/(1+r)**5
  ebit_adjust=p['lease_expense']-debt/D(5+n)
  coverage=(p['ebit']+ebit_adjust)/(p['interest']+debt*r)
  selected=max(b for b in p['bands'] if b[0]<=coverage)
  if selected==(lower,spread):valid.append((r,debt,ebit_adjust,coverage))
 assert len(valid)==1, 'Synthetic rating/lease circular relation is not uniquely solved'
 rate,lease_debt,lease_adjust,coverage=valid[0]
 rd_adjust=p['rd_current']-sum(p['rd_history'])/p['rd_years']
 base_ebit=p['ebit']+lease_adjust+rd_adjust;base_margin=base_ebit/p['revenue']
 sales_capital=p['revenue']/(p['equity_book']+p['debt']-p['cash'])
 rev=p['revenue'];df=D(1);rows=[]
 for t in range(1,12):
  g=p['growth'] if t<=5 else p['growth']-(p['growth']-p['riskfree'])*D(t-5)/5 if t<=10 else p['riskfree']
  margin=base_margin+(p['margin']-base_margin)*min(D(t)/p['convergence'],D(1))
  tax=p['tax'] if t<=5 else p['tax']+(p['marginal_tax']-p['tax'])*D(min(t-5,5))/5
  newrev=rev*(1+g);ebit=newrev*margin;nopat=ebit*(1-tax)
  reinvest=(newrev-rev)/sales_capital if t<=10 else p['riskfree']/p['terminal_roc']*nopat
  discount=p['discount'] if t<=5 else p['discount']-(p['discount']-p['terminal_discount'])*D(min(t-5,5))/5
  if t<=10:df/=1+discount
  rows.append(dict(year=t,growth=g,revenue=newrev,margin=margin,ebit=ebit,tax=tax,nopat=nopat,reinvestment=reinvest,fcff=nopat-reinvest,discount=discount,discount_factor=df,pv=(nopat-reinvest)*df))
  rev=newrev
 terminal=rows[-1]['fcff']/(p['terminal_discount']-p['riskfree']);terminal_pv=terminal*df;forecast_pv=sum(x['pv'] for x in rows[:10]);operating=terminal_pv+forecast_pv;debt=p['debt']+lease_debt;equity=operating-debt-p['minority']+p['cash']+p['nonoperating']
 return dict(rows=rows,bridge=dict(terminal_cashflow=rows[-1]['fcff'],terminal_discount=p['terminal_discount'],terminal_value=terminal,terminal_pv=terminal_pv,forecast_pv=forecast_pv,total_pv=operating,operating_assets=operating,debt=debt,minority=p['minority'],cash=p['cash'],nonoperating=p['nonoperating'],equity=equity,options=D(0),common_equity=equity,shares=p['shares'],value_per_share=equity/p['shares'],price=p['price'],price_ratio=p['price']/(equity/p['shares'])),source_adjustments=dict(lease_debt=lease_debt,lease_rate=rate,lease_coverage=coverage,lease_ebit_adjustment=lease_adjust,rd_ebit_adjustment=rd_adjust,adjusted_base_ebit=base_ebit,sales_to_capital=sales_capital))

def jsonable(x):
 if isinstance(x,Decimal):return str(x)
 if isinstance(x,dict):return {k:jsonable(v) for k,v in x.items()}
 if isinstance(x,list):return [jsonable(v) for v in x]
 return x
if __name__=='__main__':print(json.dumps(jsonable({'base':compute(),'review':compute(review=True)}),indent=2))
