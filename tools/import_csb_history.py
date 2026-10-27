"""Import selected official CSB annual books as compact history."""
import hashlib
import json
from pathlib import Path

from extract_csb import extract
from import_csb import ROOT,parse_pages

BOOKS=[
    {'year':2025,'validFrom':'2025-01-01','file':'csb-2025.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/2025-yili-b-r-m-f-yatlari-200105_1007-20250120090000.pdf'},
    {'year':2024,'validFrom':'2024-01-01','file':'csb-2024.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/2024-bf-kitap-baskisi-20240119121027.pdf'},
]

def compact(records):
    result=[]
    for record in records:
        item={key:value for key,value in record.items() if key!='contexts'}
        item['contextCodes']=[context['code'] for context in record.get('contexts',[])]
        result.append(item)
    return result

def run():
    sources=json.loads((ROOT/'data/sources.json').read_text())
    for book in BOOKS:
        year=book['year'];source_id=f'csb-{year}'
        pdf=ROOT/'data'/book['file'];tables=ROOT/'data'/f'{source_id}-tables.json'
        if not pdf.exists():raise FileNotFoundError(f'Upload {book["file"]} before importing history')
        digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
        extract(pdf,tables)
        pages=json.loads(tables.read_text())
        records,report=parse_pages(pages,year,book['url'],source_id,book['validFrom'])
        if report:
            raise RuntimeError(f'{year}: {len(report)} table rows require review; import stopped')
        (ROOT/f'data/history-{year}.json').write_text(json.dumps(compact(records),ensure_ascii=False,separators=(',',':')))
        entry={'id':source_id,'institution':'ÇŞB','year':year,'period':f'{year} yıllık · 01.01.{year}',
            'validFrom':book['validFrom'],'url':book['url'],'status':'imported','sha256':digest,
            'note':f'{year} resmî ana kitabı: inşaat rayiç ve fiyatları ile mekanik ve elektrik fiyat/tarifleri. Montaj bedeli ayrı gösterilir.'}
        sources=[source for source in sources if source['id']!=source_id]
        sources.append(entry)
        print(f'{year}: {len(records)} records',flush=True)
    sources.sort(key=lambda source:(source['institution'],str(source['year'])),reverse=True)
    (ROOT/'data/sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
