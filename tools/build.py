"""Dependency-free static website build; SITE_URL enables canonical URLs/sitemap."""
import json
import os
import shutil
from html import escape as e
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
SITE=os.environ.get('SITE_URL','').rstrip('/')
records=json.loads((ROOT/'data/records.json').read_text())
for history_file in sorted((ROOT/'data').glob('history-*.json')):
    records.extend(json.loads(history_file.read_text()))
# Historical files keep only context codes to avoid repeating long group text.
record_lookup={(r['institution'],r['year'],r['code']):r for r in records}
for record in records:
    if 'contexts' not in record and record.get('contextCodes'):
        record['contexts']=[{
            'code':context['code'],'title':context['title'],'page':context['page'],'url':context['sourceUrl']
        } for code in record['contextCodes'] if (context:=record_lookup.get((record['institution'],record['year'],code)))]
sources=json.loads((ROOT/'data/sources.json').read_text())
record_groups={}
for record in records:
    record_groups.setdefault((record['institution'],record['code']),[]).append(record)
for versions in record_groups.values():
    versions.sort(key=lambda item:item.get('validFrom',''),reverse=True)
detail_ids={key:versions[0]['id'] for key,versions in record_groups.items()}
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(exist_ok=True)
for asset in ['style.css','app.js','neuvatech-logo.png']:
    shutil.copy(ROOT/'web'/asset,OUT/asset)
# The search index references shared group definitions by code instead of
# downloading the same long specification for each priced variant.
search_records=[]
search_fields={'id','code','title','unit','price','priceText','priceBasis','institution','year','period','recordType','installationPrice','tariff'}
for record in records:
    item={key:value for key,value in record.items() if key in search_fields}
    if item.get('tariff'):item['tariff']={'text':item['tariff']['text']}
    item['contextCodes']=[c['code'] for c in record.get('contexts',[])]
    item['detailId']=detail_ids[(record['institution'],record['code'])]
    search_records.append(item)
search_by_year={}
for item in search_records:
    search_by_year.setdefault(str(item['year']),[]).append(item)
search_manifest={}
for year,items in search_by_year.items():
    filename='records-'+year.replace('/','-')+'.json'
    (OUT/filename).write_text(json.dumps(items,ensure_ascii=False,separators=(',',':')))
    search_manifest[year]=filename
(OUT/'records-manifest.json').write_text(json.dumps({'years':search_manifest},ensure_ascii=False,separators=(',',':')))

def shell(title, body, path='', base='./', description='Resmî kurumların birim fiyat kitaplarında poz numarası veya açıklamayla arama yapın. Poz tanımı, birimi, fiyatı ve kaynak belgesini inceleyin.'):
    canonical=f'<link rel="canonical" href="{e(SITE+"/"+path)}">' if SITE else ''
    return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><base href="{base}"><title>{e(title)} | Neuvatech Poz</title><meta name="description" content="{e(description)}"><meta name="theme-color" content="#c60000">{canonical}<link rel="stylesheet" href="style.css"></head><body><header><nav class="wrap" aria-label="Ana menü"><a class="brand" href="./" aria-label="Neuvatech Poz ana sayfa"><img src="neuvatech-logo.png" alt="Neuvatech – Engineering Design Technology"></a><div class="links"><a href="./">Poz ara</a><a href="kaynaklar/">Veri kaynakları</a></div></nav></header><main class="wrap">{body}</main><footer><div class="wrap">Neuvatech Poz · Bağımsız arama uygulaması · Resmî kurum sitesi değildir.<br>Fiyatın dönemini ve kapsamını kaynak belgeden kontrol edin. Kapsam ve eksikler: <a href="kaynaklar/">Veri kaynakları</a></div></footer><script src="app.js" defer></script></body></html>'''

def write(path,content):
    dest=OUT/path
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(content)

institutions=sorted(set(r['institution'] for r in records))
options=''.join(f'<option value="{e(x)}">{e(x)}</option>' for x in institutions)
years=sorted({str(r['year']) for r in records},reverse=True)
year_options=''.join(f'<option value="{e(x)}">{e(x)}</option>' for x in years)
csb_years=sorted({int(str(r['year'])[:4]) for r in records if r['institution']=='ÇŞB'})
csb_year_label=f'{csb_years[0]}–{csb_years[-1]}' if len(csb_years)>1 else str(csb_years[0])
body=f'''<section class="hero"><div class="eyebrow">Kamu birim fiyat kütüphanesi · yıllara göre</div><h1>Aradığınız poz,<br>tek bir yerde.</h1><p>Poz numarasını veya işin adını yazın. Birim fiyatı, kitapta yer alan tanımı ve resmî kaynağı birlikte bulun.</p></section><form id="search" role="search"><div class="searchbox"><label class="sr-only" for="q">Poz numarası veya anahtar kelimeler</label><input id="q" name="q" type="search" placeholder="Poz numarası veya anahtar kelime…" autocomplete="off"><button class="primary" type="submit">Ara →</button></div><div class="filters"><label for="institution">Kurum</label><select id="institution"><option value="">Tüm aktarılan kurumlar</option>{options}</select><label for="year">Yıl</label><select id="year"><option value="">Tüm yıllar</option>{year_options}</select><span class="muted">Türkçe karakter olmadan da arayabilirsiniz.</span></div></form><aside class="notice">ÇŞB {e(csb_year_label)} yıllık ve ara dönem yayınları ile KGM ve DSİ 2026 yayınları. Dönem ve kapsam ayrıntıları kaynak sayfasında gösterilir. Ayrı ÇŞB analiz ciltleri ve aylık güncellemeler henüz aktarılmadı. <a href="kaynaklar/">Kapsamı incele →</a></aside><div class="bar"><strong id="count" role="status" aria-live="polite">Pozlar yükleniyor…</strong><span class="muted">Fiyatlar Türk lirası</span></div><section id="results" class="results" aria-label="Arama sonuçları"></section><div class="paging"><button id="prev" disabled>← Önceki</button><span id="page">1 / 1</span><button id="next" disabled>Sonraki →</button></div><noscript><p>Canlı arama için JavaScript gereklidir. <a href="dizin/">Poz dizinini</a> JavaScript olmadan inceleyebilirsiniz.</p></noscript><a class="muted" href="dizin/">Tüm pozlar dizini →</a>'''
write('index.html',shell('Birim fiyat ve poz arama',body))
paths=['','kaynaklar/','dizin/']
detail_records=[]
for key,versions in sorted(record_groups.items()):
    r=versions[0]
    detail_records.append(r)
    path='poz/'+r['id']+'/'
    paths.append(path)
    price=(f"{float(r['price']):,.2f}".translate(str.maketrans(',.','.,'))+" ₺") if r['price'] is not None else ('Grup tarifi' if r.get('recordType')=='group' else "Tarife bağlı")
    body=f'''<article class="detail"><a class="muted" href="./">← Poz aramaya dön</a><p class="eyebrow">{e(r['institution'])} · {r['year']} · {e(r['code'])}</p><h1>{e(r['title'])}</h1><section class="detail-panel"><dl class="facts"><div><dt>Poz numarası</dt><dd>{e(r['code'])}</dd></div><div><dt>Birim</dt><dd>{e(r['unit'])}</dd></div><div><dt>Fiyat</dt><dd>{price}</dd></div><div><dt>Dönem</dt><dd>{e(r['period'])}</dd></div></dl><p class="muted">{e(r['priceBasis'])}</p><p>{e(r.get('priceText',''))}</p></section><section class="prose"><h2>Kitaptaki tanım</h2><p>{e(r['title'])}</p><aside class="notice">{e(r['descriptionStatus'])}</aside><h2>Resmî kaynak</h2><p><a href="{e(r['sourceUrl'])}" target="_blank" rel="noopener noreferrer">{e(r['institution'])} {r['year']} birim fiyat kitabı · PDF sayfa {r['page']} ↗</a></p><p>Gösterilen fiyat kitabın ilgili sütunundan alınmıştır. KDV, kâr ve diğer uygulama koşulları için resmî belgenin genel hükümlerini inceleyin.</p></section></article>'''
    if len(versions)>1:
        items=''
        for x in versions:
            amount=(f"{float(x['price']):,.2f}".translate(str.maketrans(',.','.,'))+' ₺ / '+e(x['unit'])) if x.get('price') is not None else e(x.get('priceText') or 'Tarife bağlı')
            items+=f'<li><strong>{e(str(x["year"]))}</strong>: {amount} · <a href="{e(x["sourceUrl"])}" target="_blank" rel="noopener noreferrer">PDF sayfa {x["page"]} ↗</a></li>'
        unique_titles=[]
        for x in versions:
            if x['title'] not in unique_titles:unique_titles.append(x['title'])
        descriptions=''.join('<p>'+e(title)+'</p>' for title in unique_titles)
        body=body.replace('</article>',f'<section class="prose"><h2>Yıllara göre fiyatlar</h2><ul>{items}</ul><h2>Kitaplarda geçen tanımlar</h2>{descriptions}</section></article>')
    if r.get('installationPrice') is not None:
        installation=f"{float(r['installationPrice']):,.2f}".translate(str.maketrans(',.','.,'))
        body=body.replace('</dl>',f'<div><dt>Montaj bedeli (fiyatın içindedir)</dt><dd>{installation} ₺</dd></div></dl>',1)
    if r.get('contexts'):
        context_section='<section class="prose"><h2>Üst grup tarifleri</h2><p>Tarifin tamamını açmak için grup kodunu seçin.</p><ul>'
        for context in r['contexts']:
            group_id=detail_ids.get((r['institution'],context['code']))
            if group_id:
                context_section+='<li><a href="poz/'+e(group_id)+'/">'+e(context['code'])+' · '+e(context['title'][:180])+'</a></li>'
        context_section+='</ul></section>'
        body=body.replace('</article>',context_section+'</article>')
    if r.get('tariff'):
        t=r['tariff']
        section='<section class="prose"><h2>Kaynak tarif metni</h2><p class="muted">'+e(t['version'])+'</p><div style="white-space:pre-wrap">'+e(t['text'])+'</div><p><a href="'+e(t['url'])+'" target="_blank" rel="noopener noreferrer">Tarif PDF · sayfa '+str(t['page'])+' ↗</a></p></section>'
        body=body.replace('</article>',section+'</article>')
    write(path+'index.html',shell(r['code']+' '+r['title'][:100],body,path,'../../',r['title'][:155]))
body='<section class="hero"><div class="eyebrow">Şeffaf veri kapsamı</div><h1>Kaynaklar ve güncellik.</h1><p>Yalnızca aktarılan resmî veriler arama sonuçlarında görünür. Son veri derleme tarihi: 27 Ekim 2026. Bu tarih, fiyatların o tarihte yürürlükteki en son fiyatlar olduğunu ifade etmez.</p></section><div class="source-list">'
for s in sources:
    count=sum(r['source']==s['id'] for r in records)
    body+=f'<article><h2>{e(s["institution"])} · {e(s["period"])}</h2><strong>{str(count)+" poz aktarıldı" if count else "Aktarım bekliyor"}</strong><p class="prose">{e(s["note"])}</p><a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">Resmî kaynağı aç ↗</a></article>'
body+='</div><p class="prose">PDF tablo tanımları ile ayrıntılı birim fiyat tarifleri ayrı içeriklerdir. Ayrıntılı tarif aktarılmadığında tablo tanımı, tam tarif olarak etiketlenmez. Aktarım raporu kaynak kodunda data/import-report.json dosyasındadır.</p>'
write('kaynaklar/index.html',shell('Veri kaynakları ve kapsam',body,'kaynaklar/','../'))
# Crawlable paginated directory: no client-side-only SEO dependency.
groups=[detail_records[i:i+200] for i in range(0,len(detail_records),200)]
for n,group in enumerate(groups):
    path='dizin/' if n==0 else f'dizin/{n+1}/'
    if n:paths.append(path)
    links=''.join(f'<li><a href="poz/{e(r["id"])}/">{e(r["institution"])} · {e(r["code"])}</a></li>' for r in group)
    pages=' · '.join(f'<a href="dizin/{str(i+1)+"/" if i else ""}">{i+1}</a>' for i in range(len(groups)))
    write(path+'index.html',shell('Poz dizini · '+str(n+1),f'<section class="hero"><h1>Poz dizini</h1><p>{pages}</p></section><ul class="all-links">{links}</ul>',path,'../' if n==0 else '../../'))
write('404.html',shell('Sayfa bulunamadı','<section class="hero"><h1>Bu sayfa bulunamadı.</h1><p><a href="./">Poz aramaya dön →</a></p></section>',base=(SITE+'/' if SITE else './')))
write('.nojekyll','')
if SITE:
    write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(SITE+'/'+p)+'</loc></url>' for p in paths)+'</urlset>')
    write('robots.txt','User-agent: *\nAllow: /\nSitemap: '+SITE+'/sitemap.xml\n')
else:
    write('robots.txt','User-agent: *\nAllow: /\n')
print(f'Built {len(records)} searchable records in {len(detail_records)} detail pages. Canonical base: {SITE or "not configured"}')
