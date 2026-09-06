"""Unit cases use SYNTHETIC rates; not published USPS accuracy checks."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from tariff_oracle import quote
class Bands(unittest.TestCase):
    def test_upper_bounds(self):
        rates=[{'service':'ground','zone':1,'upper_oz':4,'usd':'1.00'}, {'service':'ground','zone':1,'upper_oz':8,'usd':'2.00'},{'service':'ground','zone':1,'upper_oz':16,'usd':'3.00'},{'service':'ground','zone':1,'upper_oz':32,'usd':'4.00'}]
        for v,u,x in [('4','oz','1.00'),('4.01','oz','2.00'),('8','oz','2.00'),('1','lb','3.00'),('1.01','lb','4.00')]:
            self.assertEqual(str(quote(rates,'ground',v,u,1)),x)
    def test_outside(self):
        with self.assertRaises(ValueError):quote([],'ground',0,'oz',1)
if __name__=='__main__':unittest.main()
