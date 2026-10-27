"""Download and import selected official CSB annual books as compact history."""
import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path

from extract_csb import extract
from import_csb import ROOT,parse_pages

BOOKS=[
    {'year':2025,'validFrom':'2025-01-01','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/2025-yili-b-r-m-f-yatlari-200105_1007-20250120090000.pdf'},
    {'year':2024,'validFrom':'2024-01-01','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/2024-bf-kitap-baskisi-20240119121027.pdf'},
]

def download(url,path):
    request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PozArama/1.0; official-source-import)'})
    with urllib.request.urlopen(request,timeout=90) as response:
        data=response.read()
    if not data.startswith(b'%PDF'):
        raise ValueError('Official source did not return a PDF')
    Path(path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()

def compact(records):
    result=[]
    for record in records:
        item={key:value for key,value in record.items() if key!='contexts'}
        item['contextCodes']=[context['code'] for context in record.get('contexts',[])]
        result.append(item)
    return result

def run():
    sources=json.loads((ROOT/'data/sources.json').read_text())
    with tempfile.TemporaryDirectory() as temp_dir:
        temp=Path(temp_dir)
        for book in BOOKS:
            year=book['year'];source_id=f'csb-{year}'
            pdf=temp/f'{source_id}.pdf';tables=temp/f'{source_id}-tables.json'
            print(f'Downloading CSB {year}',flush=True)
            digest=download(book['url'],pdf)
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
