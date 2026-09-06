"""Development arithmetic check from published summary + explicit task precision rule.
Not a full source extraction oracle; verify source labels visually before release.
"""
from decimal import Decimal, ROUND_HALF_UP
import json
D=Decimal
b=D('1430225');p=D('182800');oh=(b+p)*D('.10');base=b+p+oh
risk=base*D('.10');pre=base+risk;infl=pre*D('.01');final=pre+infl
out={k:{'unrounded':str(v),'display_gbp':str(v.quantize(D('1'),rounding=ROUND_HALF_UP))}
 for k,v in [('building',b),('preliminaries',p),('overheads_profit',oh),('base',base),('risk',risk),('pre_inflation',pre),('inflation',infl),('final',final)]}
assert final==D('1971277.8525')
print(json.dumps(out,indent=2))
