from pathlib import Path
import json
TASK=Path(__file__).resolve().parents[1]
o=json.loads((TASK/'solution/oracle.json').read_text())
def numbers(row,idx):return [float(x) if i in idx and x is not None else x for i,x in enumerate(row)]
report=[['Metric','Value'],['Earlier edition','January 2024'],['Later edition','January 2025'],
 ['Earlier observation window','Oct 2022 to Sep 2023'],['Later observation window','October 2023 to September 2024'],
 ['Employment denominator','Population age 16 to 64'],['Unemployment denominator','Age 16+ economically active population'],
 ['Change units','percentage points'],['Precision','Published display rates, one decimal place'],
 ['Eligible authority codes',296],['Employment comparable pairs',294],['Unemployment comparable pairs',294],
 ['Interpretation','Descriptive cross-period differences. No causal or statistical-significance claim; survey sampling variability applies.'],
 ['Source','ONS LI01 January 2024 and January 2025. Annual Population Survey and model-based local unemployment.'],
 ['Source URL','https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/li01regionallabourmarketlocalindicatorsforcountieslocalandunitaryauthorities']]
plan={'title':'English local labour-market comparison','sheets':[
 {'name':'Briefing','rows':report},
 {'name':'Top five','rows':[['Rank','Geography code','Geography','Unemployment change pp','Employment change pp']]+[numbers(r,{0,3,4}) for r in o['top5']],
  'chart':{'category':2,'values':[3,4],'title':'Rate changes, percentage points'}},
 {'name':'Authority panel','rows':[['Geography code','Geography','Employment rate earlier','Employment rate later','Unemployment rate earlier','Unemployment rate later','Employment change pp','Unemployment change pp','Comparison status']]+[numbers(r,{2,3,4,5,6,7}) for r in o['panel']]},
 {'name':'Exclusions','rows':[['Geography code','Geography','Metric','Reason']]+o['exclusions']},
 {'name':'Source trace','rows':[['Geography code','Edition','Metric','Raw value','Published value','Source location']]+[numbers(r,{3,4}) if r[4] is not None else r for r in o['provenance']]}]}
(TASK/'metadata/reference_plan.json').write_text(json.dumps(plan,ensure_ascii=False))
receipts=json.loads((TASK.parents[1]/'sources/downloads_b/download_receipt.json').read_text())
sources=[{'filename':Path(r['path']).name,**{k:r[k] for k in ['source_id','resolved_url','final_url','size','sha256','content_type']},'terms':'Open Government Licence v3.0 except noted material; ONS landing saved locally; no additional workbook restriction found.'} for r in receipts if r['source_id'].startswith('ons_')]
manifest={'task_id':TASK.name,'sources':sources,'source_type':'official_statistics_reconstructed_request','not_a_real_client_commission':True,
 'observations':{'January2024':'Oct 2022 to Sep 2023','January2025':'October 2023 to September 2024'},
 'population_definitions':{'employment':'age 16 to 64','unemployment':'age 16+ economically active'},
 'precision':'Source raw numeric values retained; visible project convention uses published 1dp display for changes/ranking',
 'compatibility':'Both APS employment and model-based unemployment definitions align; 2025 LFS reweighting note explicitly says APS not reweighted to that LFS population. Descriptive period comparison only.',
 'transformation':'Original input workbooks copied byte-for-byte; no geographic prescreening or source table changes.',
 'source_gate':'PASSED','oracle_gate':'PASSED independent OOXML and Decimal source check',
 'source_notes':{'earlier':o['earlier_source_context'],'later':o['later_source_context']}}
(TASK/'metadata/source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(TASK/'data/input_files/source_context.md').write_text('# ONS source context\n\nThe supplied workbooks are the original January 2024 and January 2025 LI01 editions from the Office for National Statistics. Read each original Cover_sheet, Notes and LI01 header before comparing rates. Employment is from the Annual Population Survey; local unemployment is model-based. Source suppression codes and sample warnings remain in the originals.\n\nSource: '+sources[0]['resolved_url']+'\n\nLater edition: '+sources[1]['resolved_url']+'\n\nContains public sector information licensed under the Open Government Licence v3.0, except where otherwise stated: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/\n\nThis task is a project-authored statistics reconstruction, not an actual client engagement. No source geographies were preselected in the input files.\n')
print('Labour source manifest and reference plan ready')
