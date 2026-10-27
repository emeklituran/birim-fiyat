"""Conservative exact-code matching for the official DSİ R03 tariff PDF.

Only self-contained page blocks with an explicit analysis heading and TARİF
marker are imported. Ranges and continuation pages are left for review.
Requires pdftotext (poppler-utils).
"""
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
URL='https://cdniys.tarimorman.gov.tr/api/File/GetGaleriFile/425/DosyaGaleri/595/dsi_birim_fiyat_kitabi_analiz_ve_tarifleri_r03.pdf'

def run():
    text=subprocess.check_output(['pdftotext','-layout',str(ROOT/'data/dsi-analiz-tarif-r03.pdf'),'-']).decode()
    tariffs={}
    for number,page in enumerate(text.split('\f'),1):
        for block in re.split(r'Poz No\.:\s+Analizin Adı:',page)[1:]:
            code=re.search(r'^\s*(\d{2}\.\d{3}\.\d{4})\s',block,re.M)
            tariff=re.search(r'TARİF\s*:',block)
            if not code or not tariff:
                continue
            # Do not merge repeated blocks or infer matches for grouped codes.
            code=code.group(1)
            content=block[tariff.start():].strip()
            content=re.sub(r'\n\s*\d+\s*$','',content).strip()
            content=re.sub(r'[ \t]+',' ',content)
            content=re.sub(r'\n{3,}','\n\n',content)
            if code not in tariffs:
                tariffs[code]={'text':content,'page':number,'url':URL+'#page='+str(number),'version':'DSİ Analiz ve Tarifler R03 (resmî sitede ayrı yayın)'}
    records=json.loads((ROOT/'data/records.json').read_text())
    count=0
    for r in records:
        if r['institution']=='DSİ' and r['code'] in tariffs:
            r['tariff']=tariffs[r['code']]
            r['descriptionStatus']='Kitaptaki tablo tanımı ve ayrı R03 yayınındaki poz tarifi. Tarifin kaynağı aşağıda belirtilmiştir.'
            count+=1
    (ROOT/'data/records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    print(f'{count} records matched to explicit DSİ R03 tariff blocks')

if __name__=='__main__':run()
