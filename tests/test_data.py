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

    def test_csb_price_columns_and_context(self):
        records=json.loads((ROOT/'data/records.json').read_text())
        csb={r['code']:r for r in records if r['institution']=='ÇŞB'}
        self.assertGreater(len(csb),5000)
        self.assertEqual(Decimal(csb['15.100.1001']['price']),Decimal('256.25'))
        self.assertEqual(Decimal(csb['10.100.1062']['price']),Decimal('205.00'))
        mechanical=csb['25.170.1101']
        self.assertEqual(Decimal(mechanical['price']),Decimal('1159.35'))
        self.assertEqual(Decimal(mechanical['installationPrice']),Decimal('481.88'))
        self.assertEqual(mechanical['unit'],'m')
        self.assertTrue(any('KOLLEKTÖR' in c['title'] for c in mechanical['contexts']))
        electrical=csb['35.172.1226']
        self.assertEqual(Decimal(electrical['price']),Decimal('9099.21'))
        self.assertEqual(Decimal(electrical['installationPrice']),Decimal('474.21'))
        self.assertEqual(csb['25.615.1200']['unit'],'Adet')
        self.assertIsNone(csb['25.300.2100']['price'])
        self.assertEqual(csb['25.300.2100']['priceText'],'% 30')
        self.assertIn('Depoda',csb['10.130.1001']['priceBasis'])
        for r in csb.values():
            self.assertTrue(r['code'].startswith(('10.','15.','19.','25.','35.')))
            if r['recordType']=='group':self.assertIsNone(r['price'])

if __name__=='__main__':unittest.main()
