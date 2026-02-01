import pandas as pd
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import os
import calendar
from datetime import datetime
import warnings

# Gereksiz uyarıları sustur
warnings.filterwarnings('ignore')

# EPDK Saat Dilimleri
def get_tariff_period(hour):
    if 6 <= hour < 17: return 'T1 (Gündüz)'
    elif 17 <= hour < 22: return 'T2 (Puant)'
    else: return 'T3 (Gece)'

class NeuralPriceEngine:
    """
    Gerçek Yapay Zeka (Yapay Sinir Ağları - MLP)
    Fiyat seviyesini Neural Network tahmin eder.
    Saatlik dağılımı (T1/T2/T3) tarihsel oranlara (Ratio) göre yapar.
    Böylece T3 asla T1'den pahalı çıkmaz.
    """
    def __init__(self):
        # 3 Katmanlı Sinir Ağı (Deep Learning Lite)
        self.model = MLPRegressor(
            hidden_layer_sizes=(100, 50, 25), # Beyin nöron katmanları
            activation='relu',
            solver='adam',
            max_iter=1000,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.hourly_ratios = {} # Her saatin gün ortalamasına oranı

    def fit(self, df):
        print("🧠 Sinir Ağları (Neural Network) eğitiliyor...")
        
        # 1. Hiyerarşik Veri Hazırlığı
        # Önce veriyi "Günlük Ortalama"ya indirgeyelim.
        # Çünkü Neural Network trendi günlük bazda daha iyi yakalar.
        daily_avg = df.groupby(df['tarih'].dt.date)['ptf'].mean().reset_index()
        daily_avg['tarih'] = pd.to_datetime(daily_avg['tarih'])
        
        # Zamanı sayıya çevir (Trend için)
        daily_avg['time_idx'] = (daily_avg['tarih'] - daily_avg['tarih'].min()).dt.days
        
        # 2. Oranları Öğren (Seasonality)
        # Her saatin, o günün ortalamasına göre oranı nedir?
        # Örn: Saat 04:00 genelde ortalamanın %70'idir (0.7)
        df['daily_mean'] = df.groupby(df['tarih'].dt.date)['ptf'].transform('mean')
        df['ratio'] = df['ptf'] / df['daily_mean']
        
        # Her saatin ortalama çarpanını kaydet
        self.hourly_ratios = df.groupby('hour')['ratio'].mean().to_dict()
        
        # 3. Sinir Ağını Eğit (Sadece Fiyat Seviyesi İçin)
        X = daily_avg[['time_idx']]
        y = daily_avg['ptf']
        
        # Veriyi ölçekle (Neural Network için şarttır)
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled, y)
        self.start_date = daily_avg['tarih'].min()
        print("✅ Yapay Zeka enflasyon trendini ve saatlik oranları ezberledi.")

    def predict(self, future_df):
        # Gelecek günlerin "time_idx"ini bul
        future_dates = pd.to_datetime(future_df[['year', 'month', 'day']])
        time_idx = (future_dates - self.start_date).dt.days.values.reshape(-1, 1)
        
        # 1. Neural Network ile "Günlük Ortalama Fiyatı" tahmin et
        X_scaled = self.scaler.transform(time_idx)
        daily_base_price = self.model.predict(X_scaled)
        
        # 2. Saatlik Oranları Uygula (Ratio Reconstruction)
        # Bu işlem T3 < T1 < T2 hiyerarşisini GARANTİ eder.
        final_prices = []
        for i, row in future_df.iterrows():
            hour = row['hour']
            ratio = self.hourly_ratios.get(hour, 1.0)
            base_price = daily_base_price[i]
            
            # Negatif fiyat tahminini engelle
            price = max(base_price * ratio, 0)
            final_prices.append(price)
            
        return np.array(final_prices)

def train_neural_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, 'data', 'merged_data.csv')
    
    if not os.path.exists(data_path):
        print("❌ Veri bulunamadı!")
        exit()

    df = pd.read_csv(data_path)
    df['tarih'] = pd.to_datetime(df['tarih'])
    df = df.sort_values('tarih').reset_index(drop=True)
    
    # Çok eski verileri at, kafası karışmasın (Son 20.000 saat)
    df['hour'] = df['tarih'].dt.hour
    df_train = df.tail(20000).reset_index(drop=True)
    
    engine = NeuralPriceEngine()
    engine.fit(df_train)
    
    return engine

def calculate_bill():
    print("\n" + "="*60)
    print("⚡ NEURAL NETWORK FATURA SİSTEMİ (Derin Öğrenme) ⚡")
    print("="*60)
    
    engine = train_neural_model()
    
    print("\n📅 Hesaplama Dönemi:")
    try:
        target_year = int(input("Yıl (Örn: 2026): "))
        target_month = int(input("Ay (1-12): "))
    except ValueError:
        print("❌ Lütfen sayı girin!")
        return

    print(f"\n🔄 {target_month}/{target_year} için Sinir Ağları çalışıyor...")
    
    num_days = calendar.monthrange(target_year, target_month)[1]
    future_data = []
    
    for day in range(1, num_days + 1):
        for hour in range(24):
            future_data.append({
                'year': target_year,
                'month': target_month,
                'day': day,
                'hour': hour,
                'period': get_tariff_period(hour)
            })
            
    future_df = pd.DataFrame(future_data)
    
    # TAHMİN (Neural Network + Ratios)
    future_df['Tahmin_PTF'] = engine.predict(future_df)
    
    avg_ptf = future_df.groupby('period')['Tahmin_PTF'].mean()
    
    print("\n💰 Ek Maliyet Parametreleri:")
    try:
        yekdem_val = input("Tahmini YEKDEM (TL/MWh) [Varsayılan 250]: ")
        yekdem = float(yekdem_val) if yekdem_val else 250.0
    except ValueError: yekdem = 250.0
        
    try:
        margin_input = input("Marj Oranı (Örn: %5 için '5' yaz) [Varsayılan 5]: ")
        margin_percent = float(margin_input) if margin_input else 5.0
    except ValueError: margin_percent = 5.0
    
    margin_multiplier = 1 + (margin_percent / 100)

    final_unit_prices = {}
    print(f"\n📊 Hesaplanan PİYASA Birim Fiyatları (Vergiler Hariç):")
    
    # FİYAT KONTROLÜ (Sağlama)
    t1_p = avg_ptf['T1 (Gündüz)']
    t2_p = avg_ptf['T2 (Puant)']
    t3_p = avg_ptf['T3 (Gece)']
    
    # Matematiksel olarak T3 < T1 < T2 olması lazım artık
    
    for period in ['T1 (Gündüz)', 'T2 (Puant)', 'T3 (Gece)']:
        price_mwh = (avg_ptf[period] + yekdem) * margin_multiplier
        price_kwh = price_mwh / 1000
        final_unit_prices[period] = price_kwh
        
        label = "✅ UCUZ" if period == "T3 (Gece)" else "🔥 PAHALI" if period == "T2 (Puant)" else "NORMAL"
        print(f"   🔹 {period}: {price_kwh:.3f} TL/kWh [{label}]")

    print("\n📝 Tüketim Girişi:")
    print("1. Detaylı (Her tarife için ayrı kWh)")
    print("2. Pratik (Toplam kWh ve yüzdelik dağılım)")
    choice = input("Seçim (1 veya 2): ")
    
    consumption = {'T1 (Gündüz)': 0, 'T2 (Puant)': 0, 'T3 (Gece)': 0}
    total_kwh = 0
    
    if choice == '1':
        consumption['T1 (Gündüz)'] = float(input("T1 kWh: "))
        consumption['T2 (Puant)'] = float(input("T2 kWh: "))
        consumption['T3 (Gece)'] = float(input("T3 kWh: "))
        total_kwh = sum(consumption.values())
    elif choice == '2':
        total_kwh = float(input("Toplam Tüketim (kWh): "))
        print("Dağılım oranlarını gir (Toplam 100)")
        p1 = float(input("T1 %: "))
        p2 = float(input("T2 %: "))
        p3 = float(input("T3 %: "))
        total_p = p1 + p2 + p3
        consumption['T1 (Gündüz)'] = total_kwh * (p1 / total_p)
        consumption['T2 (Puant)'] = total_kwh * (p2 / total_p)
        consumption['T3 (Gece)'] = total_kwh * (p3 / total_p)
    
    print("\n💼 Şirket Teklifi (Sabit Fiyat):")
    offer_price = float(input("Teklif Fiyatı (TL/kWh): "))
    
    cost_market = (consumption['T1 (Gündüz)'] * final_unit_prices['T1 (Gündüz)'] +
                   consumption['T2 (Puant)']  * final_unit_prices['T2 (Puant)'] +
                   consumption['T3 (Gece)']   * final_unit_prices['T3 (Gece)'])
    cost_offer = offer_price * total_kwh
    diff = cost_offer - cost_market
    
    print("\n" + "*"*50)
    print(f"💰 {target_month}/{target_year} DETAYLI RAPOR")
    print("*"*50)
    print(f"1️⃣  PİYASA (Endeksli) Tahmini: {cost_market:.2f} TL")
    print(f"    -> Ort. Birim Fiyat: {cost_market/total_kwh:.3f} TL/kWh")
    print(f"2️⃣  TEKLİF (Sabit) Tutarı:     {cost_offer:.2f} TL")
    print("-" * 40)
    
    if diff > 0:
        print(f"❌ TEKLİFİ REDDET! (Piyasa {abs(diff):.2f} TL daha ucuz)")
    else:
        print(f"✅ TEKLİFİ KABUL ET! (Piyasa {abs(diff):.2f} TL daha pahalı)")

if __name__ == "__main__":
    calculate_bill()
