import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import os
import calendar
from datetime import datetime

# EPDK Saat Dilimleri
def get_tariff_period(hour):
    if 6 <= hour < 17: return 'T1 (Gündüz)'
    elif 17 <= hour < 22: return 'T2 (Puant)'
    else: return 'T3 (Gece)'

def train_model():
    print("⏳ Geçmiş piyasa verileri öğreniliyor...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, 'data', 'merged_data.csv')
    
    if not os.path.exists(data_path):
        print("❌ Veri bulunamadı! Lütfen önce verileri birleştir.")
        exit()

    df = pd.read_csv(data_path)
    df['tarih'] = pd.to_datetime(df['tarih'])
    df['hour'] = df['tarih'].dt.hour
    df['day_of_week'] = df['tarih'].dt.dayofweek
    df['month'] = df['tarih'].dt.month
    df['year'] = df['tarih'].dt.year
    
    df_train = df.tail(20000).reset_index(drop=True)
    X = df_train[['hour', 'day_of_week', 'month', 'year']]
    y = df_train['ptf']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X, y)
    print("✅ Tahmin Modeli Hazır.")
    return model

def calculate_bill():
    print("\n" + "="*60)
    print("⚡ PROFESYONEL FATURA KIYASLAMA (PTF + YEKDEM + MARJ) ⚡")
    print("="*60)
    
    model = train_model()
    
    # --- TARİH GİRİŞİ ---
    print("\n📅 Hesaplama Dönemi:")
    try:
        target_year = int(input("Yıl (Örn: 2026): "))
        target_month = int(input("Ay (1-12): "))
    except ValueError:
        print("❌ Lütfen sayı girin!")
        return

    # --- PİYASA SİMÜLASYONU ---
    print(f"\n🔄 {target_month}/{target_year} PTF fiyatları tahmin ediliyor...")
    num_days = calendar.monthrange(target_year, target_month)[1]
    future_data = []
    
    for day in range(1, num_days + 1):
        for hour in range(24):
            future_data.append({
                'hour': hour,
                'day_of_week': datetime(target_year, target_month, day).weekday(),
                'month': target_month,
                'year': target_year,
                'period': get_tariff_period(hour)
            })
            
    future_df = pd.DataFrame(future_data)
    features = future_df[['hour', 'day_of_week', 'month', 'year']]
    future_df['Tahmin_PTF'] = model.predict(features)
    
    # Ortalama PTF'ler (TL/MWh)
    avg_ptf = future_df.groupby('period')['Tahmin_PTF'].mean()
    
    # --- EKSTRA MALİYETLER (YEKDEM + MARJ) ---
    print("\n💰 Ek Maliyet Parametreleri:")
    
    # YEKDEM Girişi
    print("ℹ️  YEKDEM (Yenilenebilir Enerji Maliyeti) genelde 200-400 TL/MWh arasıdır.")
    try:
        yekdem_val = input("Tahmini YEKDEM (TL/MWh) [Varsayılan 250 için Enter'a bas]: ")
        yekdem = float(yekdem_val) if yekdem_val else 250.0
    except ValueError:
        yekdem = 250.0
        
    # Kar Marjı Girişi
    print("\nℹ️  Şirket Kar Marjı (Örn: %5 ise 1.05 ile çarpılır).")
    try:
        margin_input = input("Marj Oranı (Örn: %5 için '5' yaz) [Varsayılan 5]: ")
        margin_percent = float(margin_input) if margin_input else 5.0
    except ValueError:
        margin_percent = 5.0
    
    margin_multiplier = 1 + (margin_percent / 100)

    # --- NİHAİ BİRİM FİYATLARIN HESAPLANMASI ---
    # Formül: (PTF + YEKDEM) * (1 + Marj)
    
    final_unit_prices = {}
    print(f"\n📊 Hesaplanan PİYASA Birim Fiyatları (Vergiler Hariç):")
    print(f"   (Hesap: (PTF + {yekdem}) * {margin_multiplier})")
    
    for period in ['T1 (Gündüz)', 'T2 (Puant)', 'T3 (Gece)']:
        # MWh -> kWh dönüşümü için 1000'e bölüyoruz
        # Önce MWh fiyatını bul: (PTF + YEKDEM) * Marj
        price_mwh = (avg_ptf[period] + yekdem) * margin_multiplier
        price_kwh = price_mwh / 1000
        final_unit_prices[period] = price_kwh
        print(f"   🔹 {period}: {price_kwh:.3f} TL/kWh (Saf PTF: {avg_ptf[period]/1000:.3f})")

    # --- TÜKETİM GİRİŞİ ---
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
    
    # --- TEKLİF KARŞILAŞTIRMA ---
    print("\n💼 Şirket Teklifi (Sabit Fiyat):")
    offer_price = float(input("Teklif Fiyatı (TL/kWh): "))
    
    # PİYASA MALİYETİ (PTF + YEKDEM + MARJ)
    cost_market = (consumption['T1 (Gündüz)'] * final_unit_prices['T1 (Gündüz)'] +
                   consumption['T2 (Puant)']  * final_unit_prices['T2 (Puant)'] +
                   consumption['T3 (Gece)']   * final_unit_prices['T3 (Gece)'])
                   
    # TEKLİF MALİYETİ
    cost_offer = offer_price * total_kwh
    
    diff = cost_offer - cost_market
    
    print("\n" + "*"*50)
    print(f"💰 {target_month}/{target_year} DETAYLI RAPOR")
    print("*"*50)
    print(f"🔋 Tüketim: {total_kwh:.2f} kWh")
    print(f"⚙️  Parametreler: YEKDEM={yekdem} TL, Marj=%{margin_percent}")
    print("-" * 40)
    print(f"1️⃣  PİYASA (Endeksli) Tahmini: {cost_market:.2f} TL")
    print(f"    -> Ort. Birim Fiyat: {cost_market/total_kwh:.3f} TL/kWh")
    print(f"2️⃣  TEKLİF (Sabit) Tutarı:     {cost_offer:.2f} TL")
    print(f"    -> Sabit Birim Fiyat: {offer_price:.3f} TL/kWh")
    print("-" * 40)
    
    if diff > 0:
        print(f"❌ TEKLİFİ REDDET!")
        print(f"   Sabit fiyat, piyasa beklentisinden {abs(diff):.2f} TL daha PAHALI.")
    else:
        print(f"✅ TEKLİFİ KABUL ET!")
        print(f"   Sabit fiyat, piyasa beklentisinden {abs(diff):.2f} TL daha UCUZ.")

if __name__ == "__main__":
    calculate_bill()