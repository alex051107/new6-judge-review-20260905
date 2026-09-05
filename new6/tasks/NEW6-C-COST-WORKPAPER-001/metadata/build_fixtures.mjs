import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';
const root=fileURLToPath(new URL('../',import.meta.url));
const facts=JSON.parse(await fs.readFile(root+'metadata/source_facts.json','utf8'));
const expected=JSON.parse(await fs.readFile(root+'metadata/oracle_expected.json','utf8'));
await fs.mkdir(root+'fixtures',{recursive:true});
const cases=[],all=['R001','R002','R003','R004','R005','R006'];
cases.push({name:'reference',file:'../solution/reference.xlsx',lose:[],preserve:all,status:'SCORED'});
async function make(name,fn,lose=[],preserve=all.filter(x=>!lose.includes(x)),status='SCORED'){
 const w=await SpreadsheetFile.importXlsx(await FileBlob.load(root+'solution/reference.xlsx'));
 await fn(w);await(await SpreadsheetFile.exportXlsx(w)).save(root+'fixtures/'+name+'.xlsx');
 cases.push({name,file:name+'.xlsx',lose,preserve,status});
}
await make('equivalent_formula',w=>{w.worksheets.getItem('Summary').getRange('E14').formulas=[['=E10*(1+D11)']];});
await make('equivalent_layout',w=>{
 const s=w.worksheets.getItem('Elements');s.getRange('A4:G19').values=Array.from({length:16},()=>Array(7).fill(null));
 s.getRange('C8').write([['Item','Printed amount','Printed rate','Working amount','Scope','Source','Page'],...facts.elements.map(r=>[r.label,r.amount??'-',r.rate,r.amount??0,r.scope||'Elemental cost',r.source,r.page])]);
 w.worksheets.getItem('Summary').getRange('E5').formulas=[["=SUM('Elements'!F9:F23)"]];
});
await make('equivalent_short_identity',w=>{for(const s of w.worksheets.items)s.getRange('A1').values=[['Falmouth Municipal Building cost review - Rev A']];});
await make('wrong_printed_element',w=>{w.worksheets.getItem('Elements').getRange('B6').values=[[419900]];},['R002']);
await make('wrong_risk_base',w=>{w.worksheets.getItem('Summary').getRange('E11').formulas=[['=E5*D11']];},['R004','R005']);
await make('excluded_is_zero',w=>{w.worksheets.getItem('Exclusions').getRange('B5').values=[[0]];},['R003']);
await make('double_count_provisional',w=>{w.worksheets.getItem('Summary').getRange('E5').formulas=[["=SUM('Elements'!D5:D19)+'Provisional sums'!B15"]];},['R004','R005']);
await make('mixed_final',w=>{const s=w.worksheets.getItem('Summary');s.getRange('A17').write([[facts.summary[11].label,1971278,null,null,null,null,facts.summary[11].source,2,'']]);s.getRange('E17').formulas=[['=E16+1000']];s.getRange('F17').formulas=[['=E17-B17']];},['R002','R004','R006']);
await make('duplicate_omission',w=>{w.worksheets.getItem('Elements').getRange('A19').values=[['Pitched Roof']];},['R002','R004','R005','R006']);
await make('static_current_answer',w=>{const s=w.worksheets.getItem('Summary');for(const [id,value] of Object.entries(expected.working)){const r=facts.summary.findIndex(x=>x.id===id)+5;s.getRange('E'+r).values=[[Number(value)]];}},['R005']);
await make('partial_parse',w=>{w.worksheets.getItem('Elements').getRange('A4:G4').values=[['Output type','Original','Fraction','Chosen','Meaning','Reference object','Location']];},[],[],'JUDGE_ERROR');
await make('legal_formula_limit',w=>{w.worksheets.getItem('Summary').getRange('E16').formulas=[['=_xlfn.LAMBDA(x,x)(SUM(E14:E15))']];},[],[],'JUDGE_ERROR');
await fs.writeFile(root+'fixtures/malformed.xlsx','not an XLSX');cases.push({name:'malformed',file:'malformed.xlsx',lose:[],preserve:[],status:'MALFORMED_OUTPUT'});
cases.push({name:'missing',file:'missing.xlsx',lose:[],preserve:[],status:'OUTPUT_MISSING'});
await fs.writeFile(root+'fixtures/manifest.json',JSON.stringify({task_version:'new6-c1-v1.0-falmouth',cases},null,2));
console.log('Built '+cases.length+' calibrated fixture definitions');
