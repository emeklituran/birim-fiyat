# Poz Arama

Türkçe poz numarası ve anahtar kelime araması; ölçü birimi, fiyat, kaynak PDF sayfası. Bağımsız statik web uygulaması. Sunucu, hesap veya ücretli servis gerekmez.

## Mevcut kapsam

KGM ve DSİ 2026 yıllık kitaplarının ayrıştırılabilen fiyat tabloları. **ÇŞB aktarımı, aylık güncellemeler ve ayrıntılı analiz/tarif kapsamı henüz tamamlanmadı. DSİ pozlarının bir bölümünde resmî R03 tarif yayınıyla doğrudan poz kodu eşleştirmesi yapılır; ayrı kaynak ve sürüm gösterilir.** Tablo tanımı tam tarif olarak sunulmaz. Diğer kurumlar için kaynak listesi `data/sources.json` içindedir. Tüm kurumların güncel verilerini kapsadığı iddia edilmez.

Fiyatlar kaynak sütununun niteliğiyle birlikte sunulur; farklı kurumların fiyatları eşdeğer kabul edilmez. Kaynak PDF'ler doğrulama ve yeniden aktarım için `data/` içindedir. Kaynak belgelerin hakları ilgili kurumlara aittir.

## Çalıştırma

Python 3.12+:

```sh
python -m unittest discover -s tests
SITE_URL=https://emeklituran.github.io/birim-fiyat python tools/build.py
python -m http.server 8000 --directory dist
```

`http://localhost:8000` adresini açın. `file://` üzerinden açmayın; arama JSON dosyasını HTTP üzerinden yükler.

Her poz için ayrı HTML sayfası, sayfalanmış bağlantılı dizin, canonical URL, robots.txt ve sitemap.xml üretilir. Google'ın indeksleme kararı garanti edilemez. Alan adı değişirse `SITE_URL` değerini değiştirip yeniden derleyin.

## GitHub Pages

Dosyaları herkese açık `birim-fiyat` deposunun `main` dalına yükleyin. GitHub **Settings → Pages → Source → GitHub Actions** seçin. `.github/workflows/pages.yml` doğrulama, derleme ve yayınlamayı yapar. İlk yayın için Pages'in depo ayarlarında etkin olması gerekir. Actions kullanımı hesap kotalarına tabidir.

## Veriyi yeniden çıkarma

```sh
python -m pip install -r requirements.txt
python tools/import_data.py
python tools/import_tariffs.py
python -m unittest discover -s tests
python tools/build.py
```

İçe aktarma çevrimdışı kayıtlı resmî PDF dosyalarını okur; kendiliğinden güncel yayın indirmez. Yeni dönem için resmî dosyayı edinip kaynak manifestine ayrı dönem olarak ekleyin. `data/import-report.json` ayrıştırılamayan veya yinelenen satırları içerir; rapor gözden geçirilmeden tam kapsam varsayılmamalıdır. Kaynak SHA-256 özetleri manifestte tutulur.

Tarif aktarımı için sistemde `pdftotext` (Ubuntu: `poppler-utils`) bulunmalıdır. Gruplu pozlar ve sonraki sayfaya taşan tarifler otomatik eşleştirilmez; tam kapsam değildir.
