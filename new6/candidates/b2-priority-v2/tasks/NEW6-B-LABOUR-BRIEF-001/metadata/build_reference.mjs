import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const task=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const plan=JSON.parse(await fs.readFile(path.join(task,'metadata/reference_plan.json'),'utf8'));
const source=JSON.parse(await fs.readFile(path.join(task,'solution/oracle.json'),'utf8'));
const scenarios=[['baseline',10],['relaxed',5],['strict',20]];
const register=new Map(source.panel.map(r=>[r[0],{code:r[0],name:r[1]}]));
const lists=[];const selected={};
for(const [scenario,threshold] of scenarios){
 const eligible=source.panel.filter(r=>r[6]!==null&&r[7]!==null&&Math.round(Number(r[6])*10)<=-threshold&&Math.round(Number(r[7])*10)>=threshold);
 eligible.sort((a,b)=>Math.round(Number(b[7])*10)-Math.round(Number(a[7])*10)||Math.round(Number(a[6])*10)-Math.round(Number(b[6])*10)||a[0].localeCompare(b[0]));
 const top=eligible.slice(0,5);selected[scenario]=new Set(top.map(r=>r[0]));
 for(const r of source.panel){const x=register.get(r[0]);x[scenario+'_eligible']=r[6]===null||r[7]===null?'unavailable':eligible.some(v=>v[0]===r[0])?'yes':'no';x[scenario+'_selected']=selected[scenario].has(r[0])?'yes':'no';}
 top.forEach((r,i)=>lists.push([scenario,i+1,r[0],r[1],Number(r[6]),Number(r[7])]));
}
const fields=['baseline_eligible','baseline_selected','relaxed_eligible','relaxed_selected','strict_eligible','strict_selected'];
plan.sheets.push({name:'Screening',rows:[['Geography code','Geography',...fields.map(f=>f.replaceAll('_',' '))],...Array.from(register.values()).map(r=>[r.code,r.name,...fields.map(f=>r[f])])]});
plan.sheets.push({name:'Review shortlists',rows:[['Scenario','Review order','Geography code','Geography','Employment change pp','Unemployment change pp'],...lists]});
const movement=[];for(const [s] of scenarios)if(s!=='baseline'){for(const code of selected[s])if(!selected.baseline.has(code))movement.push([s,code,'entered']);for(const code of selected.baseline)if(!selected[s].has(code))movement.push([s,code,'left']);}
plan.sheets.push({name:'Membership changes',rows:[['Scenario','Geography code','Movement'],...movement]});
plan.sheets[0].rows.push(['Review policy','Both indicators comparable; unemployment rise and employment fall each at least threshold. Baseline 1.0 pp; relaxed 0.5 pp; strict 2.0 pp. Inclusive boundaries. Five places: unemployment descending, employment ascending, code ascending.'],['Review interpretation','This shortlist is a descriptive follow-up policy, not a statistical significance or causal finding. Eligibility differs from selection when there are more eligible areas than five places.'],...scenarios.map(([s])=>[s+' selected count',selected[s].size]));
await fs.writeFile(path.join(task,'metadata/priority_reference_plan.json'),JSON.stringify(plan));

plan.sheets.push({name:'Live controls',rows:[['Setting','Input value'],['Unemployment threshold pp',1],['Employment decline threshold pp',1],['Review places',5],['Current selected count',5]]});
plan.sheets.push({name:'Live screening',rows:[['Geography code','Geography','Employment change pp','Unemployment change pp','Current eligible','Current selected','Selection order'],...source.panel.map(r=>[r[0],r[1],r[6]===null?'unavailable':Number(r[6]),r[7]===null?'unavailable':Number(r[7]),'-','-',0])]});
plan.sheets.push({name:'Live shortlist',rows:[['Current order','Geography code','Employment change pp','Unemployment change pp'],...Array.from({length:10},(_,i)=>[i+1,'-','-','-'])]});
const wb=Workbook.create();
const letter=n=>{let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
for(const block of plan.sheets){
 const s=wb.worksheets.add(block.name);const rows=block.rows;const width=rows[0].length;
 s.showGridLines=false;
 for(let start=0;start<rows.length;start+=5000){
  const chunk=rows.slice(start,start+5000);
  s.getRangeByIndexes(start,0,chunk.length,width).values=chunk;
 }
 s.getRange(`A1:${letter(width-1)}1`).format={fill:'#263F57',font:{bold:true,color:'#FFFFFF',name:'Arial',size:11},wrapText:true,rowHeight:34};
 s.getRange(`A1:${letter(width-1)}${Math.min(rows.length,60)}`).format.columnWidth=23;
 if(width>1)s.getRange('B:B').format.columnWidth=30;
 if(block.name==='Live controls'){s.getRange('A:A').format.columnWidth=45;s.getRange('B:B').format.columnWidth=20;}
 if(block.name.includes('report')||block.name==='Briefing'){
  s.getRange('A:A').format.columnWidth=32;s.getRange('B:B').format.columnWidth=100;
  s.getRange(`A2:B${rows.length}`).format.wrapText=true;s.getRange(`A2:B${rows.length}`).format.rowHeight=32;
 } else if(rows.length>20){s.freezePanes.freezeRows(1);}
 for(let c=0;c<width;c++){
  const h=String(rows[0][c]).toLowerCase();
  if(/rate|change|published/.test(h))s.getRange(`${letter(c)}2:${letter(c)}${rows.length}`).setNumberFormat('0.0');
  else if(/amount|unitprice/.test(h))s.getRange(`${letter(c)}2:${letter(c)}${rows.length}`).setNumberFormat('#,##0.00;[Red](#,##0.00)');
  if(/reason|source location|description/.test(h)){
   s.getRange(`${letter(c)}:${letter(c)}`).format.columnWidth=h.includes('source')?70:55;
   s.getRange(`${letter(c)}2:${letter(c)}${rows.length}`).format.wrapText=true;
   s.getRange(`A2:${letter(width-1)}${rows.length}`).format.rowHeight=32;
  }
 }
 if(block.chart){
  const b=block.chart;const ranges=[b.category,...b.values].map(c=>s.getRange(`${letter(c)}1:${letter(c)}${rows.length}`));
  const ch=s.charts.add('bar',ranges);ch.title=b.title;ch.setPosition(`${letter(width+1)}2`,`${letter(width+11)}19`);
  ch.titleTextStyle.fontSize=13;ch.titleTextStyle.typeface='Arial';
  ch.yAxis={numberFormatCode:b.title.includes('GBP')?'#,##0':'0.0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:11}};
  ch.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:11}};
 }
 console.log('AUTHORED',block.name,rows.length-1,'rows');
}
const live=wb.worksheets.getItem('Live screening');
for(let r=2;r<=source.panel.length+1;r++){
 live.getRange(`E${r}`).formulas=[[`=IF(AND(ISNUMBER(C${r}),ISNUMBER(D${r})),IF(AND(D${r}>='Live controls'!$B$2,C${r}<=-'Live controls'!$B$3),"yes","no"),"unavailable")`]];
 live.getRange(`G${r}`).formulas=[[`=IF(E${r}="yes",COUNTIFS($E$2:$E$297,"yes",$D$2:$D$297,">"&D${r})+COUNTIFS($E$2:$E$297,"yes",$D$2:$D$297,D${r},$C$2:$C$297,"<"&C${r})+COUNTIFS($E$2:$E$297,"yes",$D$2:$D$297,D${r},$C$2:$C$297,C${r},$A$2:$A$297,"<"&A${r})+1,0)`]];
 live.getRange(`F${r}`).formulas=[[`=IF(AND(G${r}>0,G${r}<='Live controls'!$B$4),"yes","no")`]];
}
const ls=wb.worksheets.getItem('Live shortlist');
for(let r=2;r<=11;r++)for(const [out,col] of [['B','A'],['C','C'],['D','D']])ls.getRange(`${out}${r}`).formulas=[[`=IF(A${r}>'Live controls'!$B$4,"-",IFERROR(INDEX('Live screening'!$${col}$2:$${col}$297,MATCH(A${r},'Live screening'!$G$2:$G$297,0)),"-"))`]];
wb.worksheets.getItem('Live controls').getRange('B5').formulas=[[`=COUNTIF('Live screening'!F2:F297,"yes")`]];

await fs.mkdir(path.join(task,'solution'),{recursive:true});
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(task,'solution/reference.xlsx'));
console.log('EXPORTED reference.xlsx');
const inspected=await wb.inspect({kind:'table',range:`'${plan.sheets[0].name}'!A1:B16`,include:'values,formulas',tableMaxRows:16,tableMaxCols:2,maxChars:2000});
await fs.writeFile(path.join(task,'metadata/artifact_inspect.ndjson'),inspected.ndjson);
for(const block of plan.sheets){
 const right=letter(Math.min(block.rows[0].length-1,6));
 const range=block.chart?`A1:${letter(block.rows[0].length+11)}20`:`A1:${right}${Math.min(block.rows.length,9)}`;
 try{
  const png=await wb.render({sheetName:block.name,range,scale:1,format:'png'});
  await fs.writeFile(path.join(task,'metadata',`preview_${block.name.replaceAll(' ','_')}.png`),new Uint8Array(await png.arrayBuffer()));
 }catch(e){await fs.writeFile(path.join(task,'metadata',`render_${block.name.replaceAll(' ','_')}_error.txt`),String(e));}
}
