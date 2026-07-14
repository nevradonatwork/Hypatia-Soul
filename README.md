# Trigger tracker

ETL mantığıyla kurulmuş, tetikleyici olayları extract -> transform -> filter -> load
adımlarından geçiren, sonucu "system" (avukat/mahkeme/kayıt) veya "archive" (eski duygu)
olarak etiketleyen basit bir uygulama. EN/TR dil desteği var.

## Kurulum (local SQL Server'a bağlanma)

1. SQL Server'da `schema.sql` dosyasını çalıştır (SQL Server Management Studio ile açıp
   execute edebilirsin, ya da sqlcmd ile).
2. `.env.example` dosyasını `.env` olarak kopyala ve gerçek bilgilerini gir:

```
cp .env.example .env
```

Varsayılan ayar Windows Authentication (`TT_DB_AUTH=windows`) ile SSMS'te gördüğün
`NevraDonat\SQLEXPRESS` sunucusuna bağlanacak şekildedir — SSMS'e Windows hesabınla
(`NEVRADONAT\nevra`) nasıl giriyorsan, uygulama da aynı Windows kimliğiyle bağlanır,
ayrı bir SQL login oluşturmana gerek yok. Ayrı bir SQL login kullanmak istersen
`.env` içinde `TT_DB_AUTH=sql` yapıp `TT_DB_USER`/`TT_DB_PASSWORD` gir.

`.env` dosyası `.gitignore`'da, yani GitHub'a asla gitmiyor. `db.py` bu dosyayı
otomatik okuyor (python-dotenv ile).

3. Bağımlılıkları kur:

```
pip install -r requirements.txt
```

`pyodbc` için Windows'ta ayrıca "ODBC Driver 17 for SQL Server" kurulu olmalı
(genelde SQL Server Management Studio ile birlikte gelir, yoksa Microsoft'un
sitesinden indirilebilir).

4. Uygulamayı çalıştır:

```
python app.py
```

Tarayıcıda `http://localhost:5050` adresine git. Sağ üstten EN/TR arasında geçiş
yapabilirsin.

## Testler

```
pytest tests/ -v
```

Testler gerçek SQL Server'a ihtiyaç duymaz, sahte (fake) bir connection kullanır.
Bu yüzden `pyodbc` kurulu olmasa bile testler çalışır.

## Yapı

- `schema.sql` — SQL Server şeması (events tablosu + count view'ları)
- `translations.py` — EN/TR metinler
- `logic.py` — hedef (system/archive) önerisi ve validasyon
- `db.py` — SQL Server bağlantısı ve insert/select fonksiyonları
- `app.py` — Flask arayüzü
- `templates/` — form ve counts sayfaları
- `tests/` — veri katmanı, iş mantığı, arka yüz testleri

## Sonraki adımlar (istersen)

- Google Cloud'a taşırken `db.py`'deki connection string'i Cloud SQL için güncellemek yeterli,
  geri kalan mantık aynı kalır.
- Şu an her event tek satırda kaydediliyor; istersen event_questions_log gibi ayrı bir tabloya
  geçip her soruyu ayrı satır olarak tutabiliriz (daha esnek ama daha karmaşık).
- Manuel destination_tag override'ı şu an dropdown'da "(auto)" seçeneğiyle boş bırakılabiliyor,
  form.html'de select'e default olarak boş değer atanmalı (küçük bir iyileştirme).
