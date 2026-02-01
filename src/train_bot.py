import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

# Yolları ayarla
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(current_dir)

try:
    from market_env import EnergyMarketEnv
    from agent import QLearningAgent
    from features import add_technical_indicators
except ImportError:
    from src.market_env import EnergyMarketEnv
    from src.agent import QLearningAgent
    from src.features import add_technical_indicators

def main():
    print("🚀 EXPERT AI EĞİTİMİ BAŞLIYOR (v2.0)...")
    
    # 1. VERİ YÜKLE
    data_path = os.path.join(parent_dir, 'data', 'merged_data.csv')
    if not os.path.exists(data_path):
        print("❌ HATA: Veri dosyası bulunamadı! 'data/fix_merge_v2.py' çalıştırdın mı?")
        return

    df = pd.read_csv(data_path)
    df['tarih'] = pd.to_datetime(df['tarih'])
    df['hour'] = df['tarih'].dt.hour
    df['day_of_week'] = df['tarih'].dt.dayofweek
    df['month'] = df['tarih'].dt.month
    
    # 2. TEKNİK ANALİZ EKLENTİSİ
    print("📊 Teknik göstergeler hesaplanıyor...")
    df = add_technical_indicators(df)
    
    # Son 15.000 saati eğitim için kullan (Yaklaşık 2 yıl)
    df_train = df.tail(15000).reset_index(drop=True)
    print(f"📚 Eğitim Seti: {len(df_train)} saat.")
    
    # 3. ORTAM KURULUMU
    # Depo limitini 10 yaptık
    env = EnergyMarketEnv(df_train, initial_balance=10000, max_inventory=10)
    agent = QLearningAgent()
    
    episodes = 500 # İyice öğrenmesi için
    scores = []
    
    print(f"🔄 Eğitim başlıyor ({episodes} Tur)...")
    for e in range(episodes):
        state = env.reset()
        done = False
        
        while not done:
            action = agent.act(state)
            next_state, reward, done, _ = env.step(action)
            agent.learn(state, action, reward, next_state, done)
            state = next_state
        
        scores.append(env.net_worth)
        
        if (e + 1) % 50 == 0:
            print(f"Tur {e+1}/{episodes} | Kasa: {env.net_worth:.2f} TL | Keşfetme: %{agent.epsilon*100:.1f}")

    print("\n🎉 EĞİTİM TAMAMLANDI!")
    
    # 4. KAYDET (Modeli 'models' klasörüne atar)
    models_dir = os.path.join(parent_dir, 'models')
    brain_path = os.path.join(models_dir, 'expert_trader.pkl')
    agent.save_brain(brain_path)
    
    # Grafik
    plt.figure(figsize=(12, 6))
    plt.plot(scores)
    plt.title("Expert Bot Performansı")
    plt.xlabel("Tur")
    plt.ylabel("Kasa (TL)")
    plt.savefig(os.path.join(current_dir, "expert_egitim.png"))
    print("📊 Grafik kaydedildi.")

if __name__ == "__main__":
    main()