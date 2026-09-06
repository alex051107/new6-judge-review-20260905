import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const task=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const plan=JSON.parse(await fs.readFile(path.join(task,'metadata/reference_plan.json'),'utf8'));
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
 if(block.name.includes('report')||block.name==='Briefing'||block.name==='Monthly bridge'){
  s.getRange('A:A').format.columnWidth=32;s.getRange('B:B').format.columnWidth=100;
  s.getRange(`A2:B${rows.length}`).format.wrapText=true;s.getRange(`A2:B${rows.length}`).format.rowHeight=32;
  if(block.name==='Monthly bridge'){s.getRange('A:A').format.columnWidth=48;s.getRange('B:B').format.columnWidth=85;s.getRange('B2:B10').setNumberFormat('#,##0.00;[Red](#,##0.00)');}
 } else if(rows.length>20){s.freezePanes.freezeRows(1);}
 for(let c=0;c<width;c++){
  const h=String(rows[0][c]).toLowerCase();
  if(/rate|change|published/.test(h))s.getRange(`${letter(c)}2:${letter(c)}${rows.length}`).setNumberFormat('0.0');
  else if(/amount|unitprice|value|effect|unit price/.test(h))s.getRange(`${letter(c)}2:${letter(c)}${rows.length}`).setNumberFormat('#,##0.00;[Red](#,##0.00)');
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
await fs.mkdir(path.join(task,'solution'),{recursive:true});
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(task,'solution/reference.xlsx'));
console.log('EXPORTED reference.xlsx');
const inspected=await wb.inspect({kind:'table',range:`'${plan.sheets[0].name}'!A1:B16`,include:'values,formulas',tableMaxRows:16,tableMaxCols:2,maxChars:2000});
await fs.writeFile(path.join(task,'metadata/artifact_inspect.ndjson'),inspected.ndjson);
for(const block of plan.sheets){
 if(!['Monthly bridge','SKU comparison','Trading report'].includes(block.name))continue;
 const right=letter(Math.min(block.rows[0].length-1,6));
 const range=block.chart?`A1:${letter(block.rows[0].length+11)}20`:`A1:${right}${Math.min(block.rows.length,9)}`;
 try{
  const png=await wb.render({sheetName:block.name,range,scale:1,format:'png'});
  await fs.writeFile(path.join(task,'metadata',`preview_${block.name.replaceAll(' ','_')}.png`),new Uint8Array(await png.arrayBuffer()));
 }catch(e){await fs.writeFile(path.join(task,'metadata',`render_${block.name.replaceAll(' ','_')}_error.txt`),String(e));}
}
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'v2 formula error scan',maxChars:1000});
await fs.writeFile(path.join(task,'metadata/v2_preparation/formula_error_scan.ndjson'),errors.ndjson);
