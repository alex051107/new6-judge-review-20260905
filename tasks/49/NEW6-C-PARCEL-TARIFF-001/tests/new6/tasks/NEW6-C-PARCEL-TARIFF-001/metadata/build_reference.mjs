import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const rates=JSON.parse(await fs.readFile(path.join(root,'metadata/rates.json'),'utf8'));
const expected=JSON.parse(await fs.readFile(path.join(root,'metadata/oracle_expected.json'),'utf8'));
const requestLines=(await fs.readFile(path.join(root,'data/input_files/quote_requests.csv'),'utf8')).trim().split(/\r?\n/).slice(1);
const requests=requestLines.map(l=>{const [id,weight,unit,zone]=l.split(',');return {id,weight:+weight,unit,zone:+zone};});
const variants=['reference','equivalent_layout','equivalent_formula','zone_shift','floor_weight','constant_quotes','contradictory_total','duplicate_rate','omitted_quote','mixed_final','unsupported_formula','dynamic_unsupported','constant_offset','wrong_page','equivalent_date','wide_rates_long_quotes','empty_rate_table','unresolved_rate_delivery','shared_source','missing_source'];
const col=n=>{let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
await fs.mkdir(path.join(root,'fixtures'),{recursive:true});await fs.mkdir(path.join(root,'solution'),{recursive:true});
for(const variant of variants.filter(v=>process.argv.length<3||process.argv.slice(2).includes(v))){
 const wb=Workbook.create();const shifted=variant==='equivalent_layout';
 const q=wb.worksheets.add(shifted?'Shipment comparison':'Quotes');
 const r=wb.worksheets.add(shifted?'Published tariffs':'Rates');
 const rh=shifted?['usd','zone','source_page','weight_unit','upper_bound','service','effective_date','upper_oz']:['service','upper_bound','weight_unit','upper_oz','zone','usd','effective_date','source_page'];
 const qh=shifted?['selected_usd','selected','ground_usd','priority_usd','zone','weight_unit','weight','request_id','weight_oz','priority_band_lb','ground_band','ground_unit']:['request_id','weight','weight_unit','zone','weight_oz','priority_band_lb','ground_band','ground_unit','priority_usd','ground_usd','selected','selected_usd'];
 const rr=shifted?7:5, qr=shifted?8:5;
 const R=(f,row)=>`${col(rh.indexOf(f))}${row}`;
 const Q=(f,row)=>`${col(qh.indexOf(f))}${row}`;
 const sr=`'${r.name}'!`;const sq=`'${q.name}'!`;
 let rateRows=[...rates];if(shifted)rateRows.reverse();if(variant==='duplicate_rate')rateRows.push({...rateRows[0]});
 r.getRange('A1').values=[['USPS retail parcel rates']];
 r.getRange('A2').values=[['Notice 123 effective 2026-07-12. USD. Weight not over means inclusive upper bound.']];
 r.getRange('A3').values=[['Source: USPS_Notice123_20260712_pages1_5_7.pdf. Printed pages 5 and 7. https://pe.usps.com/PriceChange/Index']];
 r.getRangeByIndexes(rr-1,0,1,rh.length).values=[rh];
 const rateMatrix=rateRows.map(x=>rh.map(k=>variant==='wrong_page'&&k==='source_page'&&x.service==='priority'?15:variant==='equivalent_date'&&k==='effective_date'?new Date('2026-07-12T00:00:00Z'):['upper_bound','upper_oz','zone','usd','source_page'].includes(k)?Number(x[k]):x[k]));
 r.getRangeByIndexes(rr,0,rateMatrix.length,rh.length).values=rateMatrix;
 q.getRange('A1').values=[['Parcel quote comparison']];
 q.getRange('A2').values=[['Own ordinary cartons; declared ordinary-parcel conditions only. Outside scope: report out_of_scope. USD prices, not delivery-time recommendations.']];
 q.getRange('A3').values=[['Requests: quote_requests.csv, project-authored test requests. Weight and zone are editable; original request IDs are retained.']];
 q.getRangeByIndexes(qr-1,0,1,qh.length).values=[qh];
 const usedRequests=variant==='omitted_quote'?requests.slice(0,-1):shifted?[...requests].reverse():requests;
 const rateRange=f=>`${sr}$${col(rh.indexOf(f))}$${rr+1}:$${col(rh.indexOf(f))}$${rr+rateRows.length}`;
 for(let i=0;i<usedRequests.length;i++){
  const request=usedRequests[i],row=qr+i+1;
  const vals={request_id:request.id,weight:request.weight,weight_unit:request.unit,zone:request.zone};
  q.getRangeByIndexes(row-1,0,1,qh.length).values=[qh.map(k=>vals[k]??null)];
  const oz=Q('weight_oz',row),zone=Q('zone',row),unit=Q('weight_unit',row),weight=Q('weight',row);
  const scope=`AND(ISNUMBER(${weight}),${weight}>0,OR(${unit}="oz",${unit}="lb"),${oz}<=160,${zone}>=1,${zone}<=8,${zone}=INT(${zone}))`;
  const fs={weight_oz:`=${weight}*IF(${unit}="lb",16,1)`,priority_band_lb:`=${variant==='floor_weight'?'MAX(1,INT('+oz+'/16))':'ROUNDUP('+oz+'/16,0)'}`,ground_band:`=IF(${oz}<=4,4,IF(${oz}<=8,8,IF(${oz}<=12,12,IF(${oz}<=15.999,15.999,${Q('priority_band_lb',row)}))))`,ground_unit:`=IF(${oz}<=15.999,"oz","lb")`};
  for(const service of ['priority','ground']){
   const band=Q(service==='priority'?'priority_band_lb':'ground_band',row);
   const bu=service==='priority'?'"lb"':Q('ground_unit',row);
   const zz=variant==='zone_shift'&&request.id==='Q12'?`${zone}-1`:zone;
   let lookup=variant==='equivalent_formula'?`SUMPRODUCT((${rateRange('service')}="${service}")*(${rateRange('upper_bound')}=${band})*(${rateRange('weight_unit')}=${bu})*(${rateRange('zone')}=${zz})*${rateRange('usd')})`:`SUMIFS(${rateRange('usd')},${rateRange('service')},"${service}",${rateRange('upper_bound')},${band},${rateRange('weight_unit')},${bu},${rateRange('zone')},${zz})`;
   fs[service+'_usd']=`=IF(${scope},${lookup}${variant==='constant_offset'?'+1':''},"out_of_scope")`;
   if(variant==='dynamic_unsupported'&&service==='priority'&&request.id==='Q01')fs[service+'_usd']=`=IF(${oz}<=4,${lookup},VALUE(_xlfn.REGEXREPLACE(TEXT(${lookup},"0.00"),"^","")))`;
  }
  fs.selected=`=IF(${scope},IF(${Q('ground_usd',row)}<=${Q('priority_usd',row)},"ground","priority"),"out_of_scope")`;
  fs.selected_usd=`=IF(${scope},MIN(${Q('priority_usd',row)},${Q('ground_usd',row)}),"out_of_scope")`;
  for(const [k,f]of Object.entries(fs))q.getRange(Q(k,row)).formulas=[[f]];
  if(variant==='constant_quotes'){
   const exp=expected.quotes.find(x=>x.request_id===request.id);
   for(const k of ['priority_usd','ground_usd','selected','selected_usd'])q.getRange(Q(k,row)).values=[[k==='selected'?exp.selected:Number(k==='selected_usd'?exp.selected_usd:exp[k.replace('_usd','')])]];
  }
  if(variant==='mixed_final'&&request.id==='Q04')q.getRange(Q('ground_usd',row)).values=[[99]];
  if(variant==='unsupported_formula'&&request.id==='Q01')q.getRange(Q('priority_usd',row)).formulas=[['=_xlfn.PY("11.0",0)']];
 }
 const totalRow=qr+usedRequests.length+3;
 q.getRange(`A${totalRow}`).values=[['Batch total USD']];
 q.getRange(`B${totalRow}`).formulas=[[`=SUM(${Q('selected_usd',qr+1)}:${Q('selected_usd',qr+usedRequests.length)})`]];
 if(variant==='contradictory_total')q.getRange(`B${totalRow}`).values=[[9999]];
 if(variant==='mixed_final'){
  q.getRange(`A${totalRow+2}`).values=[['Batch total USD']];q.getRange(`B${totalRow+2}`).values=[[164.55]];
 }
 if(variant==='wide_rates_long_quotes'){
  r.getRange('A4:L210').clear({applyTo:'contents'});
  const wideHeaders=['weight_not_over','weight_unit',...Array.from({length:8},(_,i)=>`Zone ${i+1}`),'source_page','effective_date'];
  for(const [svc,titleRow,headerRow,startRow] of [['priority',4,5,6],['ground',18,19,20]]){
   r.getRange(`A${titleRow}`).values=[[svc==='priority'?'Priority Mail Retail':'USPS Ground Advantage Retail']];
   r.getRange(`A${headerRow}:L${headerRow}`).values=[wideHeaders];
   const bands=[...new Map(rates.filter(x=>x.service===svc).map(x=>[`${x.upper_bound}/${x.weight_unit}`,x])).values()];
   const rows=bands.map(b=>[+b.upper_bound,b.weight_unit,...Array.from({length:8},(_,i)=>+rates.find(x=>x.service===svc&&x.upper_bound===b.upper_bound&&x.weight_unit===b.weight_unit&&x.zone===i+1).usd),b.source_page,b.effective_date]);
   r.getRangeByIndexes(startRow-1,0,rows.length,12).values=rows;
  }
  for(let i=0;i<usedRequests.length;i++){
   const row=qr+i+1;const zone=Q('zone',row),weight=Q('weight',row),unit=Q('weight_unit',row),oz=Q('weight_oz',row);
   const scope=`AND(ISNUMBER(${weight}),${weight}>0,OR(${unit}="oz",${unit}="lb"),${oz}<=160,${zone}>=1,${zone}<=8,${zone}=INT(${zone}))`;
   q.getRange(Q('priority_usd',row)).formulas=[[`=IF(${scope},INDEX('Rates'!$C$6:$J$15,${Q('priority_band_lb',row)},${zone}),"out_of_scope")`]];
   const groundRow=`IF(${Q('ground_unit',row)}="oz",MATCH(${Q('ground_band',row)},'Rates'!$A$20:$A$23,0),4+${Q('priority_band_lb',row)})`;
   q.getRange(Q('ground_usd',row)).formulas=[[`=IF(${scope},INDEX('Rates'!$C$20:$J$33,${groundRow},${zone}),"out_of_scope")`]];
  }
 }
 if(['shared_source','missing_source'].includes(variant)){
  r.getRange(`G${rr}:H${rr+rateRows.length}`).clear({applyTo:'contents'});
  r.getRange('A2').values=[['Notice 123 — Effective date']];r.getRange('B2').values=[['07/12/2026']];
  r.getRange('A3').values=[[variant==='shared_source'?'Source: Notice 123 — Priority Mail Retail, printed page 5; Source: Notice 123 — USPS Ground Advantage Retail weight-by-zone price table':null]];
 }
 if(variant==='empty_rate_table')r.getRange(`A${rr+1}:H${rr+rateRows.length}`).clear({applyTo:'contents'});
 if(variant==='unresolved_rate_delivery')r.getRange('A1:H210').clear({applyTo:'contents'});
 for(const [sheet,hrow,width] of [[q,qr,12],[r,rr,8]]){
  sheet.showGridLines=false;sheet.getUsedRange().format.font={name:'Arial',size:11};
  sheet.getRangeByIndexes(hrow-1,0,1,width).format={fill:'#263B50',font:{name:'Arial',color:'#FFFFFF',bold:true,size:11},wrapText:true,rowHeight:34};
  sheet.getUsedRange().format.columnWidth=17;sheet.getRange('A1').format.font={name:'Arial',size:16,bold:true};
  sheet.getRange(`A2:${col(width-1)}3`).format.rowHeight=28;
  sheet.freezePanes.freezeRows(hrow);
 }
 q.getRange(`${Q('weight',qr+1)}:${Q('weight',qr+usedRequests.length)}`).format.fill='#FFF2CC';
 q.getRange(`${Q('zone',qr+1)}:${Q('zone',qr+usedRequests.length)}`).format.fill='#FFF2CC';
 for(const f of ['priority_usd','ground_usd','selected_usd'])q.getRange(`${Q(f,qr+1)}:${Q(f,qr+usedRequests.length)}`).setNumberFormat('0.00');
 q.getRange(`B${totalRow}`).setNumberFormat('0.00');r.getRange(`${R('usd',rr+1)}:${R('usd',rr+rateRows.length)}`).setNumberFormat('0.00');
 const out=path.join(root,variant==='reference'?'solution/reference.xlsx':`fixtures/${variant}.xlsx`);
 await (await SpreadsheetFile.exportXlsx(wb)).save(out);
 if(variant==='reference'){
  const checks=await wb.inspect({kind:'table',range:`${q.name}!A${qr}:L${qr+3}`,include:'values,formulas',tableMaxRows:4,tableMaxCols:12});
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:20},summary:'Reference formula scan'});
  await fs.writeFile(path.join(root,'metadata/artifact_inspection.json'),JSON.stringify({table:checks.ndjson,errors:errors.ndjson},null,2));
  for(const sheet of [q,r]){
   const blob=await wb.render({sheetName:sheet.name,range:sheet===q?'A1:L21':'A1:H16',scale:1,format:'png'});
   await fs.writeFile(path.join(root,`metadata/preview_${sheet.name}.png`),new Uint8Array(await blob.arrayBuffer()));
  }
 }
 console.log(out);
}
await fs.writeFile(path.join(root,'fixtures/malformed.xlsx'),'not an xlsx');
