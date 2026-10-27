# Poz Arama

Türkçe poz numarası ve anahtar kelime araması; ölçü birimi, fiyat, kaynak PDF sayfası. Bağımsız statik web uygulaması. Sunucu, hesap veya ücretli servis gerekmez.

## Mevcut kapsam

ÇŞB/YFK 2019–2026 ana kitapları, 2022'nin üç ve 2023'ün iki ayrı dönemi ile KGM ve DSİ 2026 yıllık kitapları aktarılır. ÇŞB: inşaat rayiçleri ve birim fiyatları, mekanik ve elektrik pozları, ana kitaptaki kodlu grup tarifleri. Montaj bedeli, montajlı fiyatın içindeki ayrı bir bileşendir; fiyata eklenmez. Poz gruplarının açıklamaları yalnızca kod hiyerarşisi eşleştiğinde alt pozlarla ilişkilendirilir.

**ÇŞB'nin ayrı analiz ciltleri, sonraki düzeltmeler ve aylık güncellemeler henüz aktarılmadı.** İnşaat tablo tanımı tam analiz tarifi olarak sunulmaz. DSİ pozlarının bir bölümünde resmî R03 tarif yayınıyla doğrudan poz kodu eşleştirmesi yapılır; ayrı kaynak ve sürüm gösterilir. Diğer kurumlar `data/sources.json` içindedir. Tüm kurumların güncel verilerini kapsadığı iddia edilmez.

Fiyatlar kaynak sütununun niteliğiyle birlikte sunulur; farklı kurumların fiyatları eşdeğer kabul edilmez. Kaynak PDF'lerin SHA-256 doğrulama özetleri `data/sources.json` içindedir. Büyük tarihsel PDF ve ara tablo dosyaları depoya eklenmez; yeniden aktarım için resmî kaynaklardan edinilir. Kaynak belgelerin hakları ilgili kurumlara aittir.

## Çalıştırma

Python 3.12+:

```sh
python -m unittest discover -s tests
SITE_URL=https://emeklituran.github.io/birim-fiyat python tools/build.py
python -m http.server 8000 --directory dist
```

`http://localhost:8000` adresini açın. `file://` üzerinden açmayın; arama JSON dosyasını HTTP üzerinden yükler.

Her poz için ayrı HTML sayfası, sayfalanmış bağlantılı dizin, canonical URL, robots.txt ve sitemap.xml üretilir. Google'ın indeksleme kararı garanti edilemez. Alan adı değişirse `SITE_URL` değerini değiştirip yeniden derleyin.

Arayüz yıl/dönem filtresini veri dosyalarından otomatik oluşturur. `data/history-YYYY.json` dosyaları aynı pozun diğer yıllardaki fiyatlarını detay sayfasında birbirine bağlar; ara dönemler `history-YYYY-N.json` biçiminde saklanır.

## GitHub Pages

Dosyaları herkese açık `birim-fiyat` deposunun `main` dalına yükleyin. GitHub **Settings → Pages → Source → GitHub Actions** seçin. `.github/workflows/pages.yml` doğrulama, derleme ve yayınlamayı yapar. İlk yayın için Pages'in depo ayarlarında etkin olması gerekir. Actions kullanımı hesap kotalarına tabidir.

## Veriyi yeniden çıkarma

```sh
python -m pip install -r requirements.txt
python tools/import_data.py
python tools/import_tariffs.py
python tools/extract_csb.py
python tools/import_csb.py
python tools/import_csb_history.py
python -m unittest discover -s tests
python tools/build.py
```

İçe aktarma çevrimdışı kayıtlı resmî PDF dosyalarını okur; kendiliğinden güncel yayın indirmez. Yeni dönem için resmî dosyayı edinip kaynak manifestine ayrı dönem olarak ekleyin. `data/import-report.json` ayrıştırılamayan veya yinelenen satırları içerir; rapor gözden geçirilmeden tam kapsam varsayılmamalıdır. Kaynak SHA-256 özetleri manifestte tutulur.

Tarif aktarımı için sistemde `pdftotext` (Ubuntu: `poppler-utils`) bulunmalıdır. Gruplu pozlar ve sonraki sayfaya taşan tarifler otomatik eşleştirilmez; tam kapsam değildir.

ÇŞB tablosunun özgün hücreleri `data/csb-tables.json`, kaynak PDF özeti `data/sources.json`, inceleme gerektiren satırlar `data/csb-import-report.json` içinde tutulur. Çıkarım 741 sayfanın tablo geometrisini okuduğu için birkaç dakika sürebilir; günlük site derlemesi hazır JSON verisini kullanır ve PDF çıkarımını tekrarlamaz.
