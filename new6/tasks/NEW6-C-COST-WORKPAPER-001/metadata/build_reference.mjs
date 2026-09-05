import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=fileURLToPath(new URL('../',import.meta.url));
const facts=JSON.parse(await fs.readFile(root+'metadata/source_facts.json','utf8'));
const wb=Workbook.create();
for(const name of ['Summary','Elements','Provisional sums','Exclusions','Qualifications'])wb.worksheets.add(name);
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
const formulas={E5:"=SUM('Elements'!D5:D19)",E6:'=182800',E7:'=(E5+E6)*D7',E8:'=SUM(E5:E7)',E10:'=E8',E11:'=E10*D11',E14:'=SUM(E10:E11)',E15:'=E14*D15',E16:'=SUM(E14:E15)'};
for(const [c,f] of Object.entries(formulas))sh.getRange(c).formulas=[[f]];
for(const r of [5,6,7,8,10,11,14,15,16])sh.getRange('F'+r).formulas=[[`=E${r}-B${r}`]];
sh.getRange('B5:B16').setNumberFormat('#,##0');sh.getRange('C5:D16').setNumberFormat('0.00%');sh.getRange('E5:E16').setNumberFormat('#,##0');sh.getRange('F5:F16').setNumberFormat('0.000000');
for(const r of [7,11,15])sh.getRange('D'+r).format.fill='#FFF3CD';
sh.getRange('A19').values=[['Full precision gives GBP 1,971,277.8525, displayed as GBP 1,971,278. The printed stages reflect source rounding.']];
sh.getRange('A20').values=[['Included provisional sums are memorandum detail. No consultant fees or VAT are added. This is a reconstructed estimate, not an approved procurement price.']];
for(const [kind,name] of [['provisional','Provisional sums'],['exclusions','Exclusions'],['qualifications','Qualifications']]){
 sh=base(name,kind==='provisional'?'Basis of estimate, PDF page 4. These amounts are already within elemental costs.':kind==='exclusions'?'Explicit exclusions, PDF pages 3 and 4. No zero-priced offers are implied.':'Notes and qualifications, PDF page 3.',['Item','Printed amount','Scope','Source','Page']);
 sh.getRange('A5').write(facts[kind].map(r=>[r.label,r.amount,r.scope,r.source,r.page]));
 sh.getRange('A:A').format.columnWidth=63;sh.getRange('B:B').format.columnWidth=18;sh.getRange('C:C').format.columnWidth=85;sh.getRange('D:D').format.columnWidth=45;sh.getRange('E:E').format.columnWidth=9;
 sh.getRange('A5:E35').format.wrapText=true;sh.getRange('A5:E35').format.rowHeight=32;sh.getRange('B5:B35').setNumberFormat('#,##0');
}
await fs.mkdir(root+'solution',{recursive:true});
await(await SpreadsheetFile.exportXlsx(wb)).save(root+'solution/reference.xlsx');
for(const name of ['Summary','Elements']){
 const png=await wb.render({sheetName:name,range:name==='Summary'?'A4:F16':'A4:D19',scale:1.5,format:'png'});
 await fs.writeFile(root+'metadata/'+name.toLowerCase()+'_preview.png',new Uint8Array(await png.arrayBuffer()));
}
console.log('Reference authored from source facts; input release awaits native Oracle parity.');
