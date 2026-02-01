import pandas as pd

def add_technical_indicators(df):
    """
    Veriye teknik analiz göstergelerini (RSI, Trend, Ortalama) ekler.
    Botun piyasanın yönünü anlamasını sağlar.
    """
    df = df.copy()
    
    # 1. Hareketli Ortalama (Son 24 saat)
    df['ma_24'] = df['ptf'].rolling(window=24).mean()
    
    # 2. Fiyat Oranı (Şu anki Fiyat / Ortalama)
    # 1.0 altı ucuz, üstü pahalı demektir.
    df['price_ratio'] = df['ptf'] / df['ma_24']
    
    # 3. Trend (Momentum)
    # Şu anki fiyat ile 1 saat öncesinin farkı
    df['trend'] = df['ptf'].diff()
    
    # 4. Volatilite (Standart Sapma)
    df['volatility'] = df['ptf'].rolling(window=24).std()
    
    # Hesaplama yapılamayan ilk satırları (NaN) temizle
    df = df.dropna().reset_index(drop=True)
    
    return df