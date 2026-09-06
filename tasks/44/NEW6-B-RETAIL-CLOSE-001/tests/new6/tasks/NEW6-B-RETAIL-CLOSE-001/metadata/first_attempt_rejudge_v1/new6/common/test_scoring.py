import unittest, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from score_facts import score
class Scores(unittest.TestCase):
    def setUp(self):self.r={'profiles':{'capability_first':{'X':100}}}
    def test_threshold(self):
        for x,p in [('0.699999999',False),('0.70',True),('1',True),('0',False)]:
            self.assertEqual(score(self.r,{'X':x})['pass'],p)
    def test_missing(self):
        with self.assertRaises(ValueError):score(self.r,{})
    def test_unknown(self):self.assertIsNone(score(self.r,{},status='JUDGE_ERROR')['normalized_score'])
    def test_output_missing(self):self.assertFalse(score(self.r,{},status='OUTPUT_MISSING')['pass'])
    def test_profiles(self):
        root=Path(__file__).parents[1]
        paths=list((root/'tasks').glob('*/rubric.json'))
        self.assertEqual(len(paths),6)
        for p in paths:
            r=json.loads(p.read_text()); facts={c['id']:1 for c in r['criteria']}
            for name in r['profiles']:
                s=score(r,facts,name);self.assertEqual(s['normalized_score'],1);self.assertTrue(s['pass'])
if __name__=='__main__':unittest.main()
