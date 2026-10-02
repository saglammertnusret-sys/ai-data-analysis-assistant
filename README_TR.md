# AI Veri Analizi Asistanı

**Hazırlayan: Mert Nusret Sağlam**

CSV/Excel dosyalarını inceleyen, doğal dil sorusundan sınırlı bir analiz planı üreten ve hesaplamayı yerel Pandas motoruyla yapan bir portföy uygulaması. Streamlit arayüzü sonuç tablosu, Matplotlib grafiği ve indirilebilir HTML raporu sunar. LLM planlama akışı LangChain ve OpenAI entegrasyonu kullanır.

## 1. Windows'ta ilk kurulum

ZIP içindeki `ai_data_assistant` klasörünü `C:\Users\elcsa\Desktop\projects` altına çıkar. Proje kökünde `app.py` görünmeli. Python 3.11 veya üzeri gerekir; 3.12/3.13 uygun seçeneklerdir.

PowerShell'de aşağıdaki komutları sırayla çalıştır:

```powershell
Set-Location "C:\Users\elcsa\Desktop\projects\ai_data_assistant"
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe smoke_test.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Sanal ortamı ayrıca aktive etmek gerekmez. Kurulum sırasında internet gerekir. `py` bulunamazsa Python kurulumunu kontrol et; `python --version` çalışıyorsa sanal ortam komutunu `python -m venv .venv` olarak kullanabilirsin.

Smoke test **SMOKE TEST PASSED** yazmalı. Tarayıcı açılmazsa `http://localhost:8501` adresine git. Terminal açık kalmalı; uygulamayı kapatmak için Ctrl+C. 8501 portu doluysa başlatma komutuna `--server.port 8502` ekle ve 8502 adresini kullan.

## 2. API olmadan ilk analiz

Sol menüde **Demo (API gerektirmez)** ve **Örnek satış verisini kullan** seçili olsun. Hazır soru listesinden bir soru seç:

1. Veri kalitesini özetle.
2. Toplam gelir ne kadar?
3. Bölgelere göre toplam geliri grafikle göster.
4. Ürünlere göre ortalama geliri göster.
5. Geliri 1000 üzerindeki kayıtları göster.
6. Günlere göre toplam geliri çizgi grafikle göster.

**Planı hazırla** düğmesine bas, sütun ve işlemi incele, ardından **Analizi çalıştır** düğmesine bas. Örnek veri tamamen yapaydır: 12 satır, toplam gelir **20.800**, Istanbul **8.000**, Ankara **6.500**, Izmir **6.300**. `gelir > 1000` filtresi beş kayıt döndürür. `sample_data/sales.xlsx` aynı verinin Excel sürümüdür.

Demo bu altı soruyu önceden tanımlanmış planlara eşler; dil modeli çalıştırmaz ve serbest soruları anlayabildiği iddiası taşımaz. Kendi dosyanda farklı sütunlar varsa satış soruları geçersiz olur; veri kalitesi özeti her uygun dosyada çalışır.

## 3. Gerçek LLM modunu aç

İlk demoyu tamamladıktan sonra proje kökünde:

```powershell
Copy-Item .env.example .env
notepad .env
```

Bu komut `.env` yokken kullanılmalı; mevcut anahtar dosyan varsa onu düzenle. Dosyaya kendi OpenAI API anahtarını yerel olarak yaz:

```dotenv
OPENAI_API_KEY=buraya_kendi_anahtarin
OPENAI_MODEL=gpt-4.1-mini
```

Anahtar oluşturma sayfası: https://platform.openai.com/api-keys
Model dokümanı: https://developers.openai.com/api/docs/models/gpt-4.1-mini

Anahtar, model erişimi ve API bakiyesi hesabına bağlıdır. API kullanımı ücretli olabilir. Anahtarını paylaşma veya Git'e yükleme. `.env` `.gitignore` içinde dışlanmıştır; yedek betiği de bu dosyayı almaz.

Uygulamada **LLM (OpenAI API)** seç. Sorunu yaz, gönderim kutusunu işaretle ve **Planı hazırla** düğmesine bas. Örnek: `Ankara bölgesindeki toplam geliri hesapla` veya `Ürünlere göre kayıt sayısını grafikle göster`. Model soruyu bir JSON planına dönüştürür. Planın sorunu doğru temsil ettiğini kontrol edip **Analizi çalıştır** düğmesine bas.

API'ye **sorunun metni, sütun adları ve türleri** gider. Ham veri satırları, kategori örnekleri ve hesaplanan sonuçlar gönderilmez. Sorunun içine yazdığın kişisel bilgiler veya filtre değerleri soru metniyle birlikte gönderilir; hassas alan adlarını da gerekirse dosyada anonimleştir. API çağrısı 45 saniye zaman aşımı kullanır, otomatik yeniden deneme yapmaz. Yeni plan isteği yeni bir çağrıdır. Analizi çalıştırma ve rapor indirme ek API çağrısı yapmaz.

Bu pakette canlı, ücretli API çağrısıyla başarı veya LLM doğruluk oranı doğrulanmadı. LangChain zinciri kontrollü HTTP yanıtıyla test edildi. Kendi hesabında ilk canlı sorgu sonraki doğrulama adımıdır.

## 4. Kendi CSV veya Excel dosyan

Örnek veri kutusunu kapat ve `.csv` veya `.xlsx` yükle. Dosya en fazla 10 MB, 100.000 satır ve 100 sütun olabilir. Başlıklar boş veya tekrar eden adlar içermemeli; `__` ile başlayan adlar sonuç alanlarına ayrıldığı için reddedilir. Eski `.xls` desteklenmez; Excel'den `.xlsx` kaydet.

CSV için ayırıcı, ondalık işareti ve karakter kodlamasını sol menüden seç. Türkçe Excel çıktısı için `;`, `,`, `utf-8-sig` veya gerektiğinde `cp1254` kullan. Excel sayfa numarası sıfırdan başlar; `0` ilk sayfadır. İlk satır başlık, sonraki satırlar veri olmalıdır. Excel formülleri çalıştırılmaz; dosyada bulunan son kaydedilmiş değerler okunur. Excel dosyasını önceden açıp hesaplayarak kaydet.

Önizlemede ilk 20 kayıt ve sütun türleri görünür. Pandas dosya türlerini otomatik çıkarır; başında sıfır bulunan kimlikleri sayıya çevirebilir. Kimlik/tarih/sayı alanlarının anlamını kontrol et. Hatalı tipler uygulamada sessizce düzeltilmez. Sayı olarak okunması gereken alan metinse dosyayı veya okuma ayarını düzelt. CSV tarihleri genellikle metin kalır; ISO `YYYY-MM-DD` biçimi sıraya uygun karşılaştırılabilir. Karışık yerel tarih formatlarına anlam çıkarılmaz.

Uygulama kaynak dosyayı değiştirmez. Boş hücreler doldurulmaz, tekrarlanan satırlar otomatik silinmez. Aynı kayıt gerçek bir işlem de olabilir; temizlik kararını veri anlamına göre ver.

## 5. Desteklenen analizler ve sınırlar

| İşlem | Davranış |
|---|---|
| Veri profili | Tür, boş/dolu sayısı, farklı değer sayısı; sayısal sütunların ortalama/minimum/maksimumu |
| Toplulaştırma | `sum`, `mean`, `min`, `max` sayısal alanlar için; `count` ve `nunique` |
| Gruplama | En fazla iki sütun; boş grup anahtarları da sonuca dahil |
| Filtre | `eq`, `ne`, `gt`, `ge`, `lt`, `le`, düz metin `contains`, boş/dolu kontrolü; en fazla beş koşul, AND bağlantısı |
| Satır seçimi | Belirli sütunlar, sıralama ve en fazla 1.000 sonuç satırı |
| Grafik | Tek gruplama sütunlu toplulaştırma; çubuk veya çizgi; en fazla ilk 50 sonuç satırı |
| Çıktı | UTF-8 CSV tablo, PNG grafik, JSON plan, tek dosyalık HTML raporu |

Toplam/ortalama/minimum/maksimum boş ölçümleri atlar; tümü boşsa sonuç boş kalır. `count` bir sütun seçiliyken boş olmayan değerleri sayar; `metric=null` ile tüm satırları sayar. `nunique` boş hariç farklı değer sayısıdır. Sonuçtaki `__value__` hesaplanan ölçümdür. Filtreler sırayla kaynak veriye uygulanır. Sıralama toplulaştırmadan sonra, sınır uygulamadan önce yapılır. Çıktı sınırlandırıldıysa ekranda ve raporda belirtilir.

Ay/yıl çıkarımı, hesaplanan yeni sütunlar, çoklu ölçümler, OR filtreleri, tabloları birleştirme, pivot, korelasyon, istatistiksel hipotez testi ve tahmin bu sürümde desteklenmez. Model bunlar için `unsupported` planı üretmelidir; sunucu bu planı reddeder. Model bazen desteklenmeyen bir isteği yanlışlıkla desteklenen plana çevirebilir; planı inceleme adımı bunun için gereklidir. Geçerli JSON tek başına doğru soru yorumunu kanıtlamaz.

Serbest Python/SQL üreten dataframe agent veya Python REPL kullanılmaz. LLM yalnızca şeması sınırlandırılmış bir plan üretir. Pydantic yapıyı, analiz motoru sütunları ve işlemlerin uygunluğunu doğrular. `eval`, `exec`, shell veya dosya/network işlemleri plan yürütmesinde bulunmaz. Bu yaklaşım keyfi kod çalıştırmayı kaldırır; verinin veya model yorumunun doğruluğunu garanti etmez.

HTML çıktısındaki veri ve soru metinleri kaçışlanır. CSV indirmede formül olarak yorumlanabilecek metinler başlarına tek tırnak eklenerek korunur; sayısal değerler değiştirilmez. İndirilen rapor veri sonuçlarını içerir; paylaşmadan önce bunları incele.

## 6. Rapor ve terminal kullanımı

Arayüzde tablo, grafik, plan ve HTML raporunu ayrı düğmelerle indir. HTML raporu tarayıcıda açılır; **Yazdır → PDF olarak kaydet** ile PDF oluşturabilirsin. Rapor, veri kalite özetini, soruyu, uygulanan planı, tabloyu, grafiği ve hesaplama notlarını içerir. Spekülatif nedensellik veya model tarafından uydurulmuş sonuç yorumları eklenmez.

Terminalden API'siz örnek çalıştırma:

```powershell
.\.venv\Scripts\python.exe -m data_assistant.cli --file "sample_data\sales.csv" --output "runs\demo_01"
```

Bu komut planı yazdırır ve çalıştırır; arayüzdeki ayrı plan inceleme düğmesi terminal akışında yoktur. Serbest soruda `.env` hazırlandıktan sonra `--mode llm --question "Ankara bölgesindeki toplam geliri hesapla"` ekle. `--mode llm` API'ye soru/şema gönderimini seçer. Eski çıktılar korunur; ikinci çalışma için `runs\demo_02` gibi yeni klasör kullan.

## 7. Doğrulama, yedek ve CV

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe backup.py
```

`VALIDATION.md` test kapsamını ve doğrulanmamış noktaları açıklar. `backup.py` kaynak kodu, örnek verileri, yönergeleri ve testleri ZIP'e alır; `.env`, `.venv`, kişisel veri klasörleri ve `runs` çıktılarını dahil etmez. ZIP'i başka disk veya buluta da kopyala. Kendi veri ve sonuçlarını ayrıca güvenli şekilde yedekle.

Bu bir LLM uygulama projesidir; CNN/One-Class SVM gibi kendi modelimizi eğitmiyoruz. Hazır model soruyu yorumlar; Pandas gerçek hesaplamayı yapar, Matplotlib çizer, Streamlit sunar, LangChain akışı bağlar. CV'de model doğruluğu veya kazandırdığı süre hakkında ölçülmemiş sayı kullanma. Canlı LLM sorgularını doğruladıktan sonra şöyle yazabilirsin:

> Developed a CSV/Excel analysis assistant using Python, Pandas, LangChain and Streamlit, with validated natural-language query plans, data-quality checks, charts and downloadable reports.

## Teknik referanslar

- LangChain ChatOpenAI: https://docs.langchain.com/oss/python/integrations/chat/openai
- OpenAI model: https://developers.openai.com/api/docs/models/gpt-4.1-mini
- Streamlit uygulama testleri: https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest
