# Doğrulama kaydı

## Çalıştırılan kontroller

- `python smoke_test.py`: geçti. Yapay satış verisinde 12 kayıt, toplam gelir 20.800; Istanbul 8.000, Ankara 6.500, Izmir 6.300. PNG, CSV, JSON ve HTML üretimi doğrulandı.
- `python -m unittest discover -s tests -v`: **13 test geçti**.
- CLI aynı örneği `.xlsx` dosyasından okuyup bölge toplamlarını, grafiği ve HTML raporunu üretti.
- Streamlit sunucusu başlatıldı; yerel sağlık uç noktası `ok` yanıtı verdi ve sunucu kapatıldı.
- Örnek PNG grafik görsel olarak incelendi: etiketler ve beklenen üç bölge değeri doğru.

## Test kapsamı

1. Altı demo planı ve bağımsız olarak bilinen toplam/filtre sonuçları.
2. Boş grup anahtarlarının dahil edilmesi; tümü boş ölçümlerde toplamın boş kalması.
3. Boş olmayan ölçüm sayımı ile tüm satır sayımı arasındaki fark.
4. AND filtreleri, sıralama, sonuç sınırı ve kaynak verinin değişmemesi.
5. `contains` filtresinin regex değil düz metin araması olması.
6. Olmayan sütun, metin alanında sayısal toplam, geçersiz sıralama ve filtre türünün reddi.
7. Kod alanları, bilinmeyen işlemler ve serbest demo sorularının reddi.
8. Tekrarlanan/boş CSV başlıkları; Türkçe kodlama, noktalı virgül ve ondalık virgül.
9. Excel sayfa seçimi ve tekrar eden Excel başlıkları.
10. HTML kaçışlama, CSV formül koruması ve eski rapor klasörünün üzerine yazmama.
11. Filtre sonrasında boş sonuç.
12. **Gerçek LangChain ChatPromptTemplate → ChatOpenAI yapılandırılmış çıktı zinciri**, HTTP isteğini ağ yerine `httpx.MockTransport` ile karşılayarak test edildi. Plan ayrıştırıldı ve hesaplandı; gönderilen mesajlarda örnek satır/kategori değerleri bulunmadığı kontrol edildi. Bu bir canlı LLM yanıtı değildir.
13. Streamlit AppTest: başlangıç, demo plan hazırlama, hesaplama, doğru tablo ve çalışma modu değiştiğinde önceki sonucun temizlenmesi.

## Ortam

Linux; Python 3.12.14; Pandas 2.2.3; NumPy 2.3.5; Matplotlib 3.10.8; openpyxl 3.1.5; Pydantic 2.13.5; Streamlit 1.65.0; langchain-core 1.6.6; langchain-openai 1.6.7; python-dotenv 1.2.4.

`requirements.txt` uyumlu ana sürüm aralıkları kullanır. Gelecekte yeni paket sürümleri kurulabilir; kendi ortamında smoke testini çalıştır. Kurulumdan sonra sürümleri kaydetmek için `python -m pip freeze > environment.txt` kullanabilirsin.

## Doğrulanmamış noktalar

- Kullanıcının Windows bilgisayarında kurulum ve ilk açılış henüz doğrulanmadı.
- Gerçek OpenAI hesabı, anahtar, model erişimi, bakiye ve ücretli canlı model yanıtı test edilmedi.
- Serbest doğal dil soruları için LLM doğruluk oranı, performans karşılaştırması veya zaman tasarrufu ölçülmedi.
- Demo hesaplamaları ve kontrollü HTTP testleri canlı LLM doğruluğu olarak sunulamaz.
- Kullanıcının gerçek dosyalarında tip çıkarımı, veri kalitesi ve planın soruya uygunluğu ayrıca incelenmelidir.
- Arayüz akışı AppTest ile test edildi; gerçek Windows tarayıcısında görsel doğrulama henüz yapılmadı.

İlk kullanıcı doğrulaması: smoke test → örnek veriyle arayüz analizi → gerekirse `.env` kurulumuyla tek bir canlı LLM sorgusu → planı ve sonucu elle karşılaştırma.
