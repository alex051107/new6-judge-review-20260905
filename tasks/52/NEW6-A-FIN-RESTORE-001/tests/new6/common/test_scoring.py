import unittest, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from score_facts import score
from harbor_verifier import validate_result
class Scores(unittest.TestCase):
    def setUp(self):self.r={'profiles':{'capability_first':{'X':100}}}
    def test_threshold(self):
        for x,p in [('0.699999999',False),('0.70',True),('1',True),('0',False)]:
            self.assertEqual(score(self.r,{'X':x})['pass'],p)
    def test_missing(self):
        with self.assertRaises(ValueError):score(self.r,{})
    def test_unknown(self):self.assertIsNone(score(self.r,{},status='JUDGE_ERROR')['normalized_score'])
    def test_delivery_failures_are_zero(self):
        for status in ['OUTPUT_MISSING','MALFORMED_OUTPUT']:
            s=score(self.r,{},status=status)
            self.assertFalse(s['pass']); self.assertEqual(s['score_decimal'],'0')
            self.assertEqual(s['normalized_score'],0); self.assertTrue(s['sample_countable'])
            self.assertNotIn('criterion_scores',s)
            self.assertEqual(validate_result(s)['normalized_score'],0)
    def test_old_delivery_receipts_normalized_including_profiles(self):
        s={'evaluation_status':'OUTPUT_MISSING','normalized_score':None,
           'profiles':{'capability_first':{'evaluation_status':'OUTPUT_MISSING','normalized_score':None}}}
        result=validate_result(s)
        self.assertEqual(result['normalized_score'],0)
        self.assertEqual(result['profiles']['capability_first']['normalized_score'],0)
    def test_unavailable_not_zero(self):
        for status in ['JUDGE_ERROR','TASK_INVALID','NATIVE_RECALC_REQUIRED','INFRA_ERROR']:
            result=validate_result(score(self.r,{},status=status))
            self.assertIsNone(result['normalized_score']);self.assertIsNone(result['pass'])
            self.assertFalse(result['sample_countable'])
            with self.assertRaises(ValueError):
                validate_result({'evaluation_status':status,'normalized_score':0})
    def test_invalid_transport_states_fail(self):
        for value in [0.1,True,'0',float('nan')]:
            with self.assertRaises(ValueError):
                validate_result({'evaluation_status':'OUTPUT_MISSING','normalized_score':value})
        with self.assertRaises(ValueError):
            validate_result({'evaluation_status':'OUTPUT_MISSING','normalized_score':0},1)
        with self.assertRaises(ValueError):
            validate_result({'evaluation_status':'UNKNOWN','normalized_score':None})
    def test_profiles(self):
        root=Path(__file__).parents[1]
        paths=list((root/'tasks').glob('*/rubric.json'))
        self.assertEqual(len(paths),6)
        for p in paths:
            r=json.loads(p.read_text()); facts={c['id']:1 for c in r['criteria']}
            for name in r['profiles']:
                s=score(r,facts,name);self.assertEqual(s['normalized_score'],1);self.assertTrue(s['pass'])
if __name__=='__main__':unittest.main()
