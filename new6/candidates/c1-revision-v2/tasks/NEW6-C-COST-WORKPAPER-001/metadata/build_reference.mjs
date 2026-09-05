import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=fileURLToPath(new URL('../',import.meta.url));
const facts=JSON.parse(await fs.readFile(root+'metadata/source_facts.json','utf8'));
const wb=Workbook.create();
for(const name of ['Summary','Elements','Provisional sums','Exclusions','Qualifications','Review decisions'])wb.worksheets.add(name);
function base(name,subtitle,headers){
 const sh=wb.worksheets.getItem(name);
 sh.getRange('A1').values=[['Falmouth Municipal Building - Cost estimate Revision A']];
 sh.getRange('A2').values=[['October 2024 | GBP | Job 3959 | Falmouth Town Council']];
 sh.getRange('A3').values=[[subtitle]];
 sh.getRange('A4').write([headers]);
 sh.getRange('A1:I35').format.font={name:'Arial',size:10};
 sh.getRange('A1:I3').format.rowHeight=20;
 sh.getRange('A4:I4').format={fill:'#334155',font:{name:'Arial',bold:true,color:'#FFFFFF'},rowHeight:32,wrapText:true};
 sh.getRange('A:A').format.columnWidth=53;
 sh.getRange('B:F').format.columnWidth=17;
 sh.getRange('G:G').format.columnWidth=43;
 sh.getRange('H:H').format.columnWidth=9;
 sh.getRange('I:I').format.columnWidth=55;
 return sh;
}
let sh=base('Elements','Elemental analysis, PDF page 5. Source dashes remain unpriced; working zero is a summation convention.',['Item','Printed amount','Printed rate','Working amount','Scope','Source','Page']);
sh.getRange('A5').write(facts.elements.map(r=>[r.label,r.amount??'-',r.rate,r.amount??0,r.scope||'Elemental cost',r.source,r.page]));
sh.getRange('B5:B19').setNumberFormat('#,##0');sh.getRange('C5:C19').setNumberFormat('0.00%');sh.getRange('D5:D19').setNumberFormat('#,##0');
sh.getRange('D5:D19').format.fill='#FFF3CD';sh.getRange('E:E').format.columnWidth=45;sh.getRange('F:F').format.columnWidth=45;sh.getRange('G:G').format.columnWidth=9;
sh=base('Summary','Working stages retain full precision. Difference = working minus printed; printed source values remain unchanged.',['Stage','Printed amount','Printed rate','Working rate','Working amount','Difference','Source','Page','Scope']);
sh.getRange('A5').write(facts.summary.map(r=>[r.label,r.amount,r.rate,r.rate,null,null,r.source,r.page,r.scope]));
sh.getRange('D11').values=[[0.12]];
const formulas={E5:"=SUM('Elements'!D5:D19)",E6:'=182800',E7:'=(E5+E6)*D7',E8:'=SUM(E5:E7)',E10:'=E8',E11:'=E10*D11',E14:'=SUM(E10:E11)',E15:'=E14*D15',E16:'=SUM(E14:E15)'};
for(const [c,f] of Object.entries(formulas))sh.getRange(c).formulas=[[f]];
for(const r of [5,6,7,8,10,11,14,15,16])sh.getRange('F'+r).formulas=[[`=E${r}-B${r}`]];
sh.getRange('B5:B16').setNumberFormat('#,##0');sh.getRange('C5:D16').setNumberFormat('0.00%');sh.getRange('E5:E16').setNumberFormat('#,##0');sh.getRange('F5:F16').setNumberFormat('0.000000');
for(const r of [7,11,15])sh.getRange('D'+r).format.fill='#FFF3CD';
sh.getRange('A19').values=[['Heating/ASHP replaces the included original package. Design risk is now 12%; other bases and rates are unchanged. Differences retain full precision, including source rounding.']];
sh.getRange('A20').values=[['The current heating quotation supersedes the earlier quotation. Asbestos remains an unapproved option outside the current cost limit. No consultant fees or VAT are added.']];
for(const [kind,name] of [['provisional','Provisional sums'],['exclusions','Exclusions'],['qualifications','Qualifications']]){
 sh=base(name,kind==='provisional'?'Basis of estimate, PDF page 4. These amounts are already within elemental costs.':kind==='exclusions'?'Explicit exclusions, PDF pages 3 and 4. No zero-priced offers are implied.':'Notes and qualifications, PDF page 3.',['Item','Printed amount','Scope','Source','Page']);
 sh.getRange('A5').write(facts[kind].map(r=>[r.label,r.amount,r.scope,r.source,r.page]));
 sh.getRange('A:A').format.columnWidth=63;sh.getRange('B:B').format.columnWidth=18;sh.getRange('C:C').format.columnWidth=85;sh.getRange('D:D').format.columnWidth=45;sh.getRange('E:E').format.columnWidth=9;
 sh.getRange('A5:E35').format.wrapText=true;sh.getRange('A5:E35').format.rowHeight=32;sh.getRange('B5:B35').setNumberFormat('#,##0');
}
sh=base('Review decisions','Project-authored review scenario. Prices share the estimate price date and exclude VAT and subsequent fee/allowance additions.',['Item','Printed amount','Working amount','Scope','Source']);
sh.getRange('A5').write([
 ['Current heating / ASHP quotation',null,458000,'Current same-scope replacement of the included original heating allowance; ventilation and all other works unchanged.','review_correspondence.md'],
 ['Earlier heating / ASHP quotation',472000,null,'Superseded by the current quotation; not an additional charge.','review_correspondence.md'],
 ['Asbestos removal option',null,18000,'Not approved; excluded from current cost limit. Option price is shown separately.','review_correspondence.md']
]);
sh.getRange('A:A').format.columnWidth=46;sh.getRange('B:C').format.columnWidth=20;sh.getRange('D:D').format.columnWidth=82;sh.getRange('E:E').format.columnWidth=40;
sh.getRange('A5:E7').format.wrapText=true;sh.getRange('A5:E7').format.rowHeight=54;
sh.getRange('B5:C7').setNumberFormat('#,##0');sh.getRange('C5').format.fill='#FFF3CD';sh.getRange('C7').format.fill='#FFF3CD';
sh=wb.worksheets.getItem('Elements');
for(let r=6;r<=19;r++)sh.getRange('D'+r).formulas=[[r===19?"=B19-'Provisional sums'!B15+'Review decisions'!C5":'=B'+r]];
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:30},maxChars:1500})).ndjson);
await fs.mkdir(root+'solution',{recursive:true});
await(await SpreadsheetFile.exportXlsx(wb)).save(root+'solution/reference.xlsx');
for(const name of ['Summary','Elements','Provisional sums','Exclusions','Qualifications','Review decisions']){
 const png=await wb.render({sheetName:name,range:name==='Summary'?'A4:F16':name==='Elements'?'A4:D19':name==='Review decisions'?'A4:E7':name==='Exclusions'?'A4:C28':name==='Qualifications'?'A4:C11':'A4:C17',scale:1.5,format:'png'});
 await fs.writeFile(root+'metadata/previews/'+name.toLowerCase().replaceAll(' ','_')+'_preview.png',new Uint8Array(await png.arrayBuffer()));
}
console.log('Reference authored; native Oracle parity is required before releasing a new build.');
