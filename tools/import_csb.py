"""Import CSB 2026 annual tables, including explicitly coded group definitions.

Installation is a component of the installed price, never added to it. Context
is inherited only from unpriced group codes with a matching numeric prefix.
"""
import hashlib
import json
import re
from pathlib import Path
from import_data import clean,money

ROOT=Path(__file__).resolve().parents[1]
URL='https://webdosya.csb.gov.tr/v2/yfk/2026/01/1-BF-202619011535-20260119155143.pdf'
CODE=re.compile(r'(?<!\d)(?:10|15|19|25|35)\.\d{3}\.\d{4}(?!\d)')

def unit_from(text):
    matches=re.findall(r'Ölçü\s*[:;]\s*([^\n)]{1,65})',text,re.I)
    if not matches:return None
    # Measurement clauses can be full sentences or refer to another BFT code.
    # Use only an explicit leading unit, never a truncated narrative as a unit.
    for value in reversed(matches):
        token=re.match(r'\s*[\(\[]?\s*((?:\d+\s*)?(?:Adet|Ad|metre|mt|m[²³23]?|kg|ton|takım|Tk|saat|sa|lt|l|%))(?=[\s.,;:)\]]|$)',value,re.I)
        if token:return token.group(1).strip()
    return None

def parse_pages(pages,year,url,source_id,valid_from):
    records=[];report=[];groups={};seen=set();last=None;mode=None
    for page in pages:
        number=page['page']
        for table in page['tables']:
            for cells in table:
                row=[clean(x) for x in cells]
                if not row:continue
                header=' '.join(row)
                if 'Poz No' in header and ('Tanımı' in header or 'Yapılacak İşin Cinsi' in header):
                    mode='installed' if 'Montaj' in header else 'standard'
                    continue
                codes=CODE.findall(row[0])
                if not codes:
                    # Continuation of a group tariff over a PDF page boundary.
                    if len(row)>=2 and row[1] and not any(money(x) for x in row[2:]) and last and last['recordType']=='group' and row[0] in ('','o','N','No'):
                        last['title']+=' '+row[1]
                        last['endPage']=number
                        if '_group' in last:last['_group']['title']=last['title']
                    continue
                if len(codes)!=1 or len(row) not in (3,4,5) or not row[1]:
                    report.append({'page':number,'reason':'ambiguous table cells','row':row});continue
                code=codes[0];title=row[1]
                if code in seen:
                    report.append({'page':number,'reason':'duplicate code','row':row});continue
                installed=mode=='installed' and code.startswith(('25.','35.'))
                price_text='';delivery=''
                if installed:
                    if len(row)!=4:
                        report.append({'page':number,'reason':'unexpected installed columns','row':row});continue
                    price=money(row[2]);installation=money(row[3]);unit=None
                    price_raw=row[2]
                    if price_raw in (':','li','k','n','ı') and not row[3]:
                        if price_raw!=':':title+=price_raw
                        price_raw=''
                    elif re.fullmatch(r'%\s*\d+(?:,\d+)?',price_raw):
                        price_text=price_raw
                    elif price is None and re.fullmatch(r'\d[\d.]*,\d{2}\s+[a-zA-Zıİ]+',price_raw):
                        price=money(price_raw.split()[0])
                else:
                    price=money(row[-1]);installation=None;price_raw=row[-1]
                    unit=row[2] if len(row)>=4 else None
                    if len(row)==5:delivery=row[3]
                    if not price_raw and re.search(r'\bF\s*=',title):price_text='Formüle göre hesaplanır; poz tanımındaki formüle bakınız.'
                # Numeric-looking but malformed price cells must not become a
                # group definition or a silently altered amount.
                if price_raw and price is None and not price_text:
                    report.append({'page':number,'reason':'non-numeric price; manual review','row':row});continue
                if installed and row[3] and installation is None:
                    report.append({'page':number,'reason':'invalid installation amount','row':row});continue
                prefix,tail=code.rsplit('.',1)
                contexts=[]
                for key,g in groups.items():
                    gp,gt=key.rsplit('.',1)
                    stem=gt.rstrip('0')
                    if gp==prefix and key!=code and (not stem or tail.startswith(stem)):
                        contexts.append(g)
                contexts.sort(key=lambda g:len(g['code'].rsplit('.',1)[1].rstrip('0')))
                if not unit:
                    for txt in [title]+[g['title'] for g in reversed(contexts)]:
                        unit=unit_from(txt)
                        if unit:break
                unit=unit or 'Kaynak tarife bakınız'
                record_type='priced' if price is not None else ('formula' if price_text else 'group')
                if record_type=='group' and not installed:
                    report.append({'page':number,'reason':'unpriced construction row','row':row});continue
                basis=('Montajlı birim fiyat (TL); montaj bedeli bu tutara ayrıca eklenmez' if installed else ('Rayiç fiyatı (TL)' if code.startswith('10.') else 'Birim fiyat (TL)'))
                if delivery:basis+=' · Teslim yeri: '+delivery
                record={'id':source_id+'-'+code.replace('.','-'),'code':code,'title':title,'unit':unit,
                    'price':price,'priceText':price_text or ('Grup tarifi; bu kod için ayrı fiyat yayımlanmamış.' if price is None else ''),
                    'delivery':delivery,
                    'installationPrice':installation,'priceBasis':basis,'institution':'ÇŞB','year':year,
                    'period':f'{year} yıllık · {valid_from[8:10]}.{valid_from[5:7]}.{year}','validFrom':valid_from,'source':source_id,
                    'sourceUrl':url+'#page='+str(number),'page':number,'recordType':record_type,
                    'discipline':{'10':'İnşaat rayiç','15':'İnşaat','19':'İnşaat','25':'Mekanik','35':'Elektrik'}[code[:2]],
                    'descriptionStatus':('Kitaptaki poz tanımı ve eşleşen üst grup tarifleri aşağıdadır.' if installed else 'Ana kitaptaki tablo tanımı. Ayrı inşaat analiz kitabının ayrıntılı tarif metni henüz aktarılmadı.'),
                    'contexts':contexts.copy() if installed else []}
                if record_type=='group':
                    # Store the group itself by reference until all continuation
                    # rows have been collected; inherited contexts use it later.
                    group={'code':code,'title':title,'page':number,'url':record['sourceUrl']}
                    groups[code]=group
                    record['_group']=group
                records.append(record);seen.add(code);last=record
                if record_type=='group':last=record
                # Continuation edits must update both the record and group.
    for record in records:
        if '_group' in record:
            record['_group']['title']=record['title']
            del record['_group']
    return records,report

def run():
    pages=json.loads((ROOT/'data/csb-tables.json').read_text())
    records,report=parse_pages(pages,2026,URL,'csb-2026','2026-01-01')
    old=json.loads((ROOT/'data/records.json').read_text())
    old=[r for r in old if r['institution']!='ÇŞB']
    (ROOT/'data/records.json').write_text(json.dumps(old+records,ensure_ascii=False,indent=2))
    (ROOT/'data/csb-import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    sources=json.loads((ROOT/'data/sources.json').read_text())
    for source in sources:
        if source['id']=='csb-2026':
            source.update({'status':'imported','file':'csb-2026.pdf','url':URL,'period':'2026 yıllık · 01.01.2026',
                'validFrom':'2026-01-01','sha256':hashlib.sha256((ROOT/'data/csb-2026.pdf').read_bytes()).hexdigest(),
                'note':'Kullanıcının sağladığı 19.01.2026 sürümü: inşaat rayiç ve fiyatları, mekanik ve elektrik fiyatları ile ana kitaptaki poz ve üst grup tarifleri. Montaj bedeli ayrı gösterilir; montajlı fiyata eklenmez. Ayrı analiz ciltleri ve sonraki düzeltmeler henüz aktarılmadı.'})
    (ROOT/'data/sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2))
    print(f'CSB: {len(records)} entries; {sum(r["price"] is not None for r in records)} numeric prices; {len(report)} rows for review')

if __name__=='__main__':run()
