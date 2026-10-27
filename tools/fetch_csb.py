"""Download public CSB publications and retain their official URLs."""
import concurrent.futures
import json
import re
import urllib.request
from html import unescape
from pathlib import Path
from urllib.parse import urljoin,urlparse

OUT=Path('csb-downloads')
OUT.mkdir(exist_ok=True)
INDEX='https://yfk.csb.gov.tr/birim-fiyatlar-100468'
MONTHLY='https://yfk.csb.gov.tr/aylik-guncel-rayic-ve-birim-fiyat-listeleri-113351'
SEEDS=[
 'https://webdosya.csb.gov.tr/v2/yfk/2026/01/1-BF-202619011535-20260119155143.pdf',
 'https://webdosya.csb.gov.tr/v2/yfk/2026/01/in-aat-analiz-1-20260115162935-20260120125449.pdf',
]

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PozArama/1.0; official-source-import)'})
    with urllib.request.urlopen(req,timeout=45) as response:return response.read()

def run():
    manifest=[];found=set(SEEDS)
    for name,url in [('index',INDEX),('monthly',MONTHLY)]:
        try:
            raw=get(url);(OUT/(name+'.html')).write_bytes(raw)
            html=raw.decode('utf-8',errors='replace')
            links=[urljoin(url,unescape(x)) for x in re.findall(r'href=[\"\']([^\"\']+)[\"\']',html,re.I)]
            (OUT/(name+'-links.json')).write_text(json.dumps(links,ensure_ascii=False,indent=2))
            for link in links:
                if urlparse(link).hostname=='webdosya.csb.gov.tr' and '/2026/' in link and link.lower().endswith('.pdf'):found.add(link)
        except Exception as error:
            manifest.append({'url':url,'error':str(error)})
    # Annual index includes only the current year. Monthly lists can be acquired
    # separately once their selected period is inspected.
    def fetch(url):
        name=Path(urlparse(url).path).name
        try:
            raw=get(url)
            if not raw.startswith(b'%PDF'):raise ValueError('Not a PDF response')
            (OUT/name).write_bytes(raw)
            return {'url':url,'file':name,'bytes':len(raw)}
        except Exception as error:return {'url':url,'error':str(error)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for item in pool.map(fetch,sorted(found)):
            manifest.append(item);print(json.dumps(item,ensure_ascii=False),flush=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
