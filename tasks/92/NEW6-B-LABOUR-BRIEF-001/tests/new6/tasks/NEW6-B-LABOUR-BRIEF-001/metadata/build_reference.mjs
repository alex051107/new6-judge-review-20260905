import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const task=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {releases,context}=JSON.parse(await fs.readFile(path.join(task,'metadata/source_records.json'),'utf8'));
const sourceManifest=JSON.parse(await fs.readFile(path.join(task,'metadata/source_manifest.json'),'utf8'));
const numeric=v=>v===null?null:Number(v);
const deci=v=>v===null?null:Math.round(Number(v)*10);
const delta=(a,b)=>a===null||b===null?null:(deci(b)-deci(a))/10;
const sources=Object.fromEntries(sourceManifest.sources.map(x=>[x.filename,x.final_url]));
const allCodes=years=>[...new Set(years.flatMap(y=>Object.keys(releases[y])))].sort();
const previousCodes=allCodes(['2023','2024']);
const rowsFor=years=>allCodes(years).map(code=>{
 const row={code,name:years.map(y=>releases[y][code]?.name).filter(Boolean).at(-1),missing:[]};
 for(const year of years)for(const metric of ['employment','unemployment']){
  const r=releases[year][code];row[metric+'_'+year]=r?.[metric]??null;
  if(row[metric+'_'+year]===null)row.missing.push(`${year} ${metric}: ${r?'unavailable/suppressed ('+r[metric+'_raw']+')':'geography not present'}`);
 }
 for(let i=1;i<years.length;i++)for(const m of ['employment','unemployment'])row[m+'_'+years[i-1]+'_'+years[i]]=delta(row[m+'_'+years[i-1]],row[m+'_'+years[i]]);
 row.cumulative=delta(row['unemployment_'+years[0]],row['unemployment_'+years.at(-1)]);
 row.eligible=row.missing.length===0&&years.slice(1).every((y,i)=>row['unemployment_'+years[i]+'_'+y]>0&&row['employment_'+years[i]+'_'+y]<0);
 return row;
});
const previous=rowsFor(['2023','2024']);const current=rowsFor(['2023','2024','2025']);
const select=rows=>rows.filter(r=>r.eligible).sort((a,b)=>b.cumulative-a.cumulative||a.code.localeCompare(b.code)).slice(0,5);
const previousTop=select(previous),currentTop=select(current);const previousSet=new Set(previousTop.map(r=>r.code)),currentSet=new Set(currentTop.map(r=>r.code));
const movements=[...new Set([...previousSet,...currentSet])].sort().map(code=>{
 const r=current.find(r=>r.code===code),movement=previousSet.has(code)&&currentSet.has(code)?'Retained':currentSet.has(code)?'Entered':'Left';
 const reasons=[];
 if(movement==='Left'){
  if(r.unemployment_2024_2025<=0)reasons.push(`Unemployment did not rise in the second comparison (${r.unemployment_2024_2025.toFixed(1)} pp)`);
  if(r.employment_2024_2025>=0)reasons.push(`Employment did not fall in the second comparison (${r.employment_2024_2025.toFixed(1)} pp)`);
 }else reasons.push(`Both consecutive comparisons deteriorated; cumulative unemployment increase ${r.cumulative.toFixed(1)} pp ranks within the current five`);
 return [code,r.name,previousSet.has(code)?'Yes':'No',currentSet.has(code)?'Yes':'No',movement,reasons.join('; ')];
});
// Builder uses integer tenths from raw source records; the separate Decimal
// Oracle is read only for validation after both answer sets have been computed.
const oracle=JSON.parse(await fs.readFile(path.join(task,'solution/oracle.json'),'utf8'));
if(JSON.stringify(previousTop.map(r=>r.code))!==JSON.stringify(oracle.previous_shortlist)||JSON.stringify(currentTop.map(r=>r.code))!==JSON.stringify(oracle.shortlist))throw Error('Independent shortlist mismatch');
for(const r of current){const o=oracle.panel.find(x=>x.code===r.code);for(const m of ['employment','unemployment'])for(const [a,b] of [['2023','2024'],['2024','2025']])if(r[m+'_'+a+'_'+b]!==numeric(o[m+'_change_'+a.slice(2)+'_'+b.slice(2)]))throw Error('Independent delta mismatch');}
const limits='Descriptive changes in APS employment rates (ages 16–64) and model-based unemployment rates (16+ economically active). Sampling variability remains; these comparisons do not establish statistical significance or causality.';
const sourceRows=years=>years.map(y=>[y==='2023'?'2023 corrected release':`January ${y}`,context[y].employment_header.replaceAll('\n','; '),sourceManifest.sources.find(x=>x.filename.includes(y)).final_url]);
const oldBrief=[['Previous briefing','January 2024 update'],['Purpose','Project-reconstructed working paper using the first two supplied releases.'],['Observation periods','Oct 2021–Sep 2022 compared with Oct 2022–Sep 2023.'],['Previous policy','Unemployment rose and employment fell in this single comparison; rank by unemployment increase, then geography code; select up to five.'],['Qualifying authorities',previous.filter(x=>x.eligible).length],['Previous selected count',previousTop.length],['Previous selected codes',previousTop.map(r=>r.code).join(', ')],['Limits',limits],['2023 revision','Official corrected replacement published 14 February 2023, provided under the January 2023 dataset; correction note retained.'],['Units','Displayed rates rounded to one decimal; changes are percentage points.'],...sourceRows(['2023','2024']).map(([a,b,c])=>[a,`${b} ${c}`])];
const oldData=[['Code','Authority','Employment 2023','Employment 2024','Unemployment 2023','Unemployment 2024','Employment change 2023–2024 (pp)','Unemployment change 2023–2024 (pp)','Previous eligibility'],...previous.map(r=>[r.code,r.name,...['employment_2023','employment_2024','unemployment_2023','unemployment_2024'].map(k=>numeric(r[k])),r.employment_2023_2024,r.unemployment_2023_2024,r.missing.length?'Unavailable':r.eligible?'Yes':'No'])];
const oldTop=[['Previous rank','Code','Authority','Employment change 2023–2024 (pp)','Unemployment change 2023–2024 (pp)'],...previousTop.map((r,i)=>[i+1,r.code,r.name,r.employment_2023_2024,r.unemployment_2023_2024])];
const oldEx=[['Code','Authority','Reason'],...previous.filter(r=>r.missing.length).map(r=>[r.code,r.name,r.missing.join('; ')])];
const currentBrief=[['Current briefing','January 2025 update'],['Purpose','Continued deterioration across both consecutive comparisons.'],['Observation periods','Oct 2021–Sep 2022; Oct 2022–Sep 2023; Oct 2023–Sep 2024.'],['Published definitions',limits],['In-scope union',current.length],['Three-period comparable count',current.filter(r=>r.missing.length===0).length],['Qualifying authorities',current.filter(r=>r.eligible).length],['Current selected count',currentTop.length],['Current selected codes',currentTop.map(r=>r.code).join(', ')],['Retained from previous count',movements.filter(r=>r[4]==='Retained').length],['Entered count',movements.filter(r=>r[4]==='Entered').length],['Left count',movements.filter(r=>r[4]==='Left').length],['Changes from previous shortlist',movements.map(r=>`${r[0]} ${r[4].toLowerCase()}`).join('; ')],['Comparability limits','Authorities absent from a release or with unavailable/suppressed rates cannot be assessed across all three periods. Reasons are retained in Current exclusions; no values are imputed.'],['Previous analysis','Previous briefing, Previous data, Previous shortlist and Previous exclusions remain available; previous_briefing.xlsx is also retained.'],['Units','Changes are percentage points using rates displayed to one decimal place.'],...sourceRows(['2023','2024','2025']).map(([a,b,c])=>[a,`${b} ${c}`])];
const currentData=[['Code','Authority','Employment 2023','Employment 2024','Employment 2025','Unemployment 2023','Unemployment 2024','Unemployment 2025','Employment change 2023–2024 (pp)','Employment change 2024–2025 (pp)','Unemployment change 2023–2024 (pp)','Unemployment change 2024–2025 (pp)','Cumulative unemployment change (pp)','Current eligibility'],...current.map(r=>[r.code,r.name,...['employment_2023','employment_2024','employment_2025','unemployment_2023','unemployment_2024','unemployment_2025'].map(k=>numeric(r[k])),r.employment_2023_2024,r.employment_2024_2025,r.unemployment_2023_2024,r.unemployment_2024_2025,r.cumulative,r.missing.length?'Unavailable':r.eligible?'Yes':'No'])];
const currentTopRows=[['Current rank','Code','Authority','Employment change 2023–2024 (pp)','Employment change 2024–2025 (pp)','Unemployment change 2023–2024 (pp)','Unemployment change 2024–2025 (pp)','Cumulative unemployment change (pp)'],...currentTop.map((r,i)=>[i+1,r.code,r.name,r.employment_2023_2024,r.employment_2024_2025,r.unemployment_2023_2024,r.unemployment_2024_2025,r.cumulative])];
const oldBlocks=[{name:'Previous briefing',rows:oldBrief,brief:true},{name:'Previous data',rows:oldData},{name:'Previous shortlist',rows:oldTop,chart:{cat:2,values:[3,4],title:'Previous shortlist changes (pp)'}},{name:'Previous exclusions',rows:oldEx}];
const newBlocks=[{name:'Current briefing',rows:currentBrief,brief:true},{name:'Current data',rows:currentData},{name:'Current shortlist',rows:currentTopRows,chart:{cat:2,values:[3,4,5,6],title:'Changes across both comparisons (pp)'}},{name:'Shortlist changes',rows:[['Code','Authority','Previously selected','Currently selected','Movement','Reason'],...movements]},{name:'Current exclusions',rows:[['Code','Authority','Reason'],...current.filter(r=>r.missing.length).map(r=>[r.code,r.name,r.missing.join('; ')])]}];
const letter=n=>{let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
async function build(blocks,destination,renderBlocks){
 const wb=Workbook.create();
 for(const b of blocks){
  const s=wb.worksheets.add(b.name),height=b.rows.length,width=b.rows[0].length;s.showGridLines=false;
  s.getRangeByIndexes(0,0,height,width).values=b.rows;
  s.getRangeByIndexes(0,0,height,width).format.font={name:'Arial',size:11};
  s.getRangeByIndexes(0,0,1,width).format={fill:'#243D52',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:44};
  s.getRangeByIndexes(0,0,height,width).format.columnWidth=18;s.getRange('A:A').format.columnWidth=18;
  if(width>1)s.getRange('B:B').format.columnWidth=b.brief?100:30;
  if(b.brief){s.getRange('A:A').format.columnWidth=30;s.getRangeByIndexes(1,0,height-1,width).format.wrapText=true;s.getRangeByIndexes(1,0,height-1,width).format.rowHeight=52;}
  else{if(height>20)s.freezePanes.freezeRows(1);for(let c=0;c<width;c++)if(/employment|change/i.test(String(b.rows[0][c])))s.getRangeByIndexes(1,c,height-1,1).setNumberFormat('0.0');}
  if(b.name.includes('exclusions')){s.getRange('C:C').format.columnWidth=100;s.getRangeByIndexes(1,2,height-1,1).format.wrapText=true;s.getRangeByIndexes(1,0,height-1,width).format.rowHeight=42;}
  if(b.name==='Shortlist changes'){s.getRange('F:F').format.columnWidth=90;s.getRangeByIndexes(1,5,height-1,1).format.wrapText=true;s.getRangeByIndexes(1,0,height-1,width).format.rowHeight=44;}
  if(b.chart){const chart=s.charts.add('bar',[b.chart.cat,...b.chart.values].map(c=>s.getRangeByIndexes(0,c,height,1)));chart.title=b.chart.title;chart.setPosition(`A${height+3}`,`N${height+21}`);chart.titleTextStyle.fontSize=13;chart.titleTextStyle.typeface='Arial';chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};chart.yAxis={numberFormatCode:'0.0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};}
 }
 const inspect=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},maxChars:1000});
 await fs.writeFile(path.join(task,'metadata',path.basename(destination)+'.inspection.ndjson'),inspect.ndjson);
 await (await SpreadsheetFile.exportXlsx(wb)).save(destination);
 for(const b of renderBlocks){const range=b.chart?`A1:N${b.rows.length+22}`:`A1:${letter(Math.min(b.rows[0].length-1,6))}${Math.min(b.rows.length,9)}`;const blob=await wb.render({sheetName:b.name,range,scale:1,format:'png'});await fs.writeFile(path.join(task,'metadata',`preview_${b.name.replaceAll(' ','_')}.png`),new Uint8Array(await blob.arrayBuffer()));}
 return {file:path.relative(task,destination),sheets:blocks.map(x=>x.name)};
}
await fs.writeFile(path.join(task,'metadata/reference_plan.json'),JSON.stringify({previous:oldBlocks,current:newBlocks},null,2));
const referenceOnly=process.argv.includes('--reference-only');
const previousOutput=referenceOnly?{file:'data/input_files/previous_briefing.xlsx',sheets:oldBlocks.map(x=>x.name)}:await build(oldBlocks,path.join(task,'data/input_files/previous_briefing.xlsx'),oldBlocks);
const referenceOutput=await build([...newBlocks,...oldBlocks],path.join(task,'solution/reference.xlsx'),referenceOnly?newBlocks.filter(x=>x.name==='Shortlist changes'):newBlocks);
await fs.writeFile(path.join(task,'metadata/reference_build_receipt.json'),JSON.stringify({status:'BUILT_PENDING_EVALUATOR_CALIBRATION',previousOutput,referenceOutput,independent_shortlist_parity:true,independent_all_delta_parity:true,old_contains_only_first_two_releases:true},null,2));
console.log(JSON.stringify({previousOutput,referenceOutput,currentSelected:currentTop.map(r=>r.code),previousSelected:previousTop.map(r=>r.code)}));
