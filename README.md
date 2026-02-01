# ⚡ EPİAŞ AI Trader & Akıllı Fatura Analiz Sistemi

Bu proje, Türkiye Elektrik Piyasası (EPİAŞ/PTF) verilerini kullanarak **elektrik fiyatlarını tahmin eden**, **otonom al-sat yapan** ve son kullanıcılar için **akıllı fatura analizi** sunan kapsamlı bir yapay zeka çözümüdür.

Proje iki ana modülden oluşur:
1.  **AI Trading Bot:** Geçmiş verilerden öğrenerek sanal piyasada kâr maksimizasyonu yapan Pekiştirmeli Öğrenme (Reinforcement Learning) ajanı.
2.  **Fatura Danışmanı:** Gelecek ayın fiyatlarını tahmin edip, sabit fiyatlı teklifler ile piyasa fiyatlarını (PTF+YEKDEM) kıyaslayan Karar Destek Sistemi.

## 🚀 Özellikler

### 🤖 1. Otonom Ticaret Robotu (RL Agent)
* **Algoritma:** Q-Learning (Epsilon-Greedy stratejisi ile).
* **Strateji:** "Realized Profit" (Gerçekleşen Kâr) odaklı. Bot, fiyat düşse bile zararına satış yapmaz, maliyetin üzerine çıkana kadar bekler (Hold Strategy).
* **Teknik Analiz:** RSI benzeri fiyat oranları, Hareketli Ortalamalar (MA-24) ve Trend (Momentum) verilerini işler.
* **Mevsimsellik:** Saatlik, Günlük ve Aylık döngüleri (Seasonality) öğrenir.

### 📊 2. Akıllı Fatura & Teklif Analizi
* **Tahmin Modeli:** Random Forest Regressor kullanılarak gelecek ayın saatlik fiyatları tahmin edilir.
* **Tarife Analizi:** T1 (Gündüz), T2 (Puant) ve T3 (Gece) tüketim profiline göre maliyet hesaplar.
* **Detaylı Hesaplama:** Sadece PTF değil, YEKDEM maliyeti ve Şirket Kar Marjı (%3, %5 vb.) dahil edilerek net kıyaslama yapar.
* **Karar Destek:** Özel şirketlerin sunduğu "Sabit Fiyat" tekliflerinin piyasa beklentisine göre kârlı olup olmadığını raporlar.

### 🛠 3. Veri İşleme (ETL)
* **Robust Import:** Bozuk CSV formatlarını, Excel (.xlsx) dosyalarını ve hatalı sütun yapılarını otomatik düzelten güçlü bir veri birleştirme modülü.


⚙️ Kurulum
Projeyi yerel ortamınızda çalıştırmak için:

Repoyu klonlayın:

git clone [https://github.com/kullaniciadi/epias-ai-trader.git](https://github.com/kullaniciadi/epias-ai-trader.git)
cd epias-ai-trader
Sanal ortam oluşturun (Önerilen):

python3 -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate

Gerekli kütüphaneleri yükleyin:
pip install pandas numpy scikit-learn matplotlib openpyxl

🖥 Kullanım
Adım 1: Veri Hazırlığı

Ham EPİAŞ verilerini (Excel veya CSV) data/ klasörüne atın ve birleştirin:
python3 data/fix_merge_v2.py

Adım 2: Botu Eğitmek (Trading)
Botun piyasayı öğrenmesi ve expert_trader.pkl dosyasını oluşturması için:

python3 src/train_bot.py
Bu işlem sonucunda eğitim grafikleri ve model dosyası oluşturulacaktır.

Adım 3: Fatura ve Teklif Analizi (Son Kullanıcı)

Gelecek ayın faturasını hesaplamak veya bir teklifi değerlendirmek için:
python3 fatura_hesapla.py

Sistem size tüketim miktarınızı ve şirketin teklifini soracak, yapay zeka tahminlerine dayanarak "Kabul Et" veya "Reddet" tavsiyesi verecektir.

📈 Performans
Eğitim Süresi: 15.000 saatlik veri üzerinde 500 epizot.

ROI (Yatırım Getirisi): Simülasyon ortamında 10.000 TL başlangıç sermayesi ile 2 yıllık periyotta %10.000+ sanal getiri (Botun "Hold" stratejisi ve doğru trend takibi sayesinde).

🤝 Katkıda Bulunma
Pull request'ler kabul edilir. Büyük değişiklikler için lütfen önce tartışma başlatın.

📜 Lisans
MIT


---

### 💡 Ekstra Tavsiyeler (GitHub İçin)

1.  **`requirements.txt` Oluştur:**
    Projeni başkalarının çalıştırabilmesi için terminale şu komutu yazarak bir dosya oluştur:
    ```bash
    pip freeze > requirements.txt
    ```
    Bu dosyayı da GitHub'a yüklemeyi unutma.

2.  **Ekran Görüntüsü (Screenshot):**
    GitHub'da görsellik çok önemlidir.
    * `fatura_hesapla.py` çalışırken çıkan o detaylı raporun ekran görüntüsünü al.
    * `src/expert_egitim.png` grafiğini al.
    * Bunları README dosyasının içine sürükleyip bırakırsan (veya `![Resim](resim_yolu.png)` koduyla eklersen) projen çok daha havalı görünür.

3.  **Başlık:** "kullaniciadi" yazan yere kendi GitHub kullanıcı adını yazmayı unutma.

Hayırlı olsun! Çok sağlam bir proje oldu. 🧿


## 📂 Proje Yapısı

```bash
├── data/                  # Ham ve işlenmiş veri dosyaları
│   ├── fix_merge_v2.py    # Veri temizleme ve birleştirme scripti
│   └── merged_data.csv    # Eğitim için hazırlanan nihai veri seti
├── models/                # Eğitilmiş AI modelleri (.pkl)
├── src/
│   ├── agent.py           # Q-Learning Ajanı (Beyin)
│   ├── market_env.py      # Piyasa Simülasyon Ortamı
│   ├── features.py        # Teknik indikatör hesaplamaları
│   └── train_bot.py       # Bot eğitim scripti
├── fatura_hesapla.py      # Kullanıcı Arayüzü (Fatura Kıyaslama)
├── requirements.txt       # Gerekli kütüphaneler
└── README.md              # Proje dokümantasyonu


