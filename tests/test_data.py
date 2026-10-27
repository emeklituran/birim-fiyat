import json
import unittest
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]

class DataTests(unittest.TestCase):
    def test_integrity(self):
        records=json.loads((ROOT/'data/records.json').read_text())
        self.assertGreater(len(records),100)
        self.assertEqual(len({r['id'] for r in records}),len(records))
        for r in records:
            if r['price'] is not None:
                self.assertGreaterEqual(Decimal(r['price']),0)
            else:
                self.assertTrue(r['priceText'])
            self.assertTrue(r['title'])
            self.assertTrue(r['unit'])
            self.assertTrue(r['sourceUrl'].endswith('#page='+str(r['page'])))

    def test_official_reference_values(self):
        records=json.loads((ROOT/'data/records.json').read_text())
        for institution,code,expected in [('DSİ','50.205.1001','117.00'),('KGM','KGM/1901','838.69')]:
            record=next(r for r in records if r['institution']==institution and r['code']==code)
            self.assertEqual(Decimal(record['price']),Decimal(expected))

if __name__=='__main__':unittest.main()
