"""Import official CSB annual and interim books as compact history."""
import hashlib
import json
from pathlib import Path

from extract_csb import extract
from import_csb import ROOT,parse_pages

BOOKS=[
    {'key':'2025','year':2025,'validFrom':'2025-01-01','period':'2025 yıllık · 01.01.2025','file':'csb-2025.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/2025-yili-b-r-m-f-yatlari-200105_1007-20250120090000.pdf'},
    {'key':'2024','year':2024,'validFrom':'2024-01-01','period':'2024 yıllık · 01.01.2024','file':'csb-2024.pdf','url':'https://webdosya.csb.gov.tr/v2/yfk/2024/06/1--2024-b-r-m-f-yatlar-20240603-1019-20240603093641.pdf'},
    {'key':'2023-2','year':'2023/2','validFrom':'2023-07-01','period':'2023 ikinci dönem · 01.07.2023','file':'csb-2023-2.pdf','url':'https://webdosya.csb.gov.tr/v2/yfk/2023/07/2023-2-birim-fiyatlar-170723-20230717105538.pdf'},
    {'key':'2023-1','year':'2023/1','validFrom':'2023-01-01','period':'2023 birinci dönem · 01.01.2023','file':'csb-2023-1.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/2023-b-r-m-f-yatlar--1-20230130125553-20250114083046.pdf'},
    {'key':'2022-3','year':'2022/3','validFrom':'2022-07-01','period':'2022 üçüncü dönem · 01.07.2022','file':'csb-2022-3.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/bf-2022-3-turkce-20220907143000.pdf'},
    {'key':'2022-2','year':'2022/2','validFrom':'2022-06-01','period':'2022 ikinci dönem · 01.06.2022','file':'csb-2022-2.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/bf-2022-2-turkce-20220907142858.pdf'},
    {'key':'2022-1','year':'2022/1','validFrom':'2022-01-01','period':'2022 birinci dönem · 01.01.2022','file':'csb-2022-1.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/bf-2022-1-turkce-20220907142750.pdf'},
    {'key':'2021','year':2021,'validFrom':'2021-01-01','period':'2021 yıllık · 01.01.2021','file':'csb-2021.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/bf-2021-turkce-20210809122111-20241015131501.pdf'},
    {'key':'2020','year':2020,'validFrom':'2020-01-01','period':'2020 yıllık · 01.01.2020','file':'csb-2020.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/-nsaat-b-r-m-f-yatlar--2020-turkce-20200207124629-20241015132829.pdf'},
    {'key':'2019','year':2019,'validFrom':'2019-01-01','period':'2019 yıllık · 01.01.2019','file':'csb-2019.pdf','url':'https://webdosya.csb.gov.tr/db/yfk/icerikler/-nsaat-b-r-m-f-yatlar--2019-turkce-20241015133030.pdf'},
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
        year=book['year'];key=book['key'];source_id=f'csb-{key}'
        pdf=ROOT/'data'/book['file'];tables=ROOT/'data'/f'{source_id}-tables.json'
        if not pdf.exists():raise FileNotFoundError(f'Upload {book["file"]} before importing history')
        digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
        if not tables.exists():
            extract(pdf,tables)
        pages=json.loads(tables.read_text())
        records,report=parse_pages(pages,year,book['url'],source_id,book['validFrom'],book['period'])
        if report:
            raise RuntimeError(f'{year}: {len(report)} table rows require review; import stopped')
        (ROOT/f'data/history-{key}.json').write_text(json.dumps(compact(records),ensure_ascii=False,separators=(',',':')))
        scope=book.get('scope','inşaat rayiç ve fiyatları ile mekanik ve elektrik fiyat/tarifleri')
        entry={'id':source_id,'institution':'ÇŞB','year':year,'period':book['period'],
            'validFrom':book['validFrom'],'url':book['url'],'status':'imported','sha256':digest,
            'note':f'{book["period"]} resmî kitabı: {scope}. Montaj bedeli bulunan tablolarda ayrı gösterilir.'}
        sources=[source for source in sources if source['id']!=source_id]
        sources.append(entry)
        print(f'{year}: {len(records)} records',flush=True)
    sources.sort(key=lambda source:(source['institution'],str(source['year'])),reverse=True)
    (ROOT/'data/sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
