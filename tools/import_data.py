"""Import official PDF table cells, preserving source page and price basis.

No inferred prices or generated descriptions. Unparsed rows go to a report.
"""
import hashlib
import json
import re
from pathlib import Path
from decimal import Decimal
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]

def clean(value):
    return re.sub(r'\s+', ' ', value or '').strip()

def money(value):
    value = clean(value).replace(' ', '')
    if not re.fullmatch(r'\d[\d.]*,\d{2}', value):
        return None
    return str(Decimal(value.replace('.', '').replace(',', '.')))

def run():
    existing_path=ROOT/'data/records.json'
    existing=json.loads(existing_path.read_text()) if existing_path.exists() else []
    records=[r for r in existing if r['institution']=='ÇŞB']
    report, seen = [], set()
    sources = json.loads((ROOT / 'data/sources.json').read_text())
    for source in sources:
        if source['status'] != 'imported' or source['institution']=='ÇŞB':
            continue
        file = ROOT / 'data' / source['file']
        source['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
        with pdfplumber.open(file) as pdf:
            for number, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ''
                # Initial approval letters contain duplicate preliminary prices.
                if source['institution'] == 'KGM' and number < 4:
                    continue
                basis = 'Kitaptaki birim fiyat (TL)'
                if source['institution'] == 'KGM':
                    basis = 'Kârsız birim fiyat (TL)' if 'KARSIZ' in text else 'Kitaptaki birim fiyat (TL); sütun başlığı için kaynağa bakınız'
                    if 'KARLI' in text and 'KARSIZ' not in text:
                        basis = 'Kârlı birim fiyat (TL)'
                for table in page.extract_tables():
                    for cells in table:
                        row = [clean(c) for c in cells]
                        if not row or not re.match(r'^(?:KGM/?|\d{2}\.)', row[0]):
                            continue
                        formula = len(row) == 4 and money(row[3]) is None and any(x in row[3] for x in ['Formül', 'Tarif', 'Analiz', 'Hesap'])
                        if len(row) != 4 or not row[1] or not row[2] or ' ' in row[0] or (money(row[3]) is None and not formula):
                            report.append({'source': source['id'], 'page': number, 'row': row})
                            continue
                        code, title, unit, price = row
                        key = (source['id'], code, basis)
                        if key in seen:
                            report.append({'source': source['id'], 'page': number, 'duplicate': code})
                            continue
                        seen.add(key)
                        slug = source['id'] + '-' + re.sub(r'[^a-z0-9]+', '-', code.lower()).strip('-')
                        # Include basis in identity if an institution repeats a code.
                        slug += '-' + hashlib.sha256(basis.encode()).hexdigest()[:6]
                        records.append({'id': slug, 'code': code, 'title': title, 'unit': unit,
                            'price': money(price), 'priceText': price if formula else '', 'priceBasis': basis, 'institution': source['institution'],
                            'year': source['year'], 'period': source['period'], 'source': source['id'],
                            'sourceUrl': source['url'] + '#page=' + str(number), 'page': number,
                            'descriptionStatus': 'Kitaptaki tablo tanımı. Ayrıntılı analiz/tarif henüz aktarılmadı.'})
    assert records, 'No records extracted'
    (ROOT / 'data/records.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
    (ROOT / 'data/import-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (ROOT / 'data/sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2))
    print(f'{len(records)} records; {len(report)} rows require review')

if __name__ == '__main__':
    run()
