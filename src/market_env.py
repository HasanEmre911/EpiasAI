import pandas as pd
import numpy as np

class EnergyMarketEnv:
    def __init__(self, df, initial_balance=10000, max_inventory=10):
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.max_inventory = max_inventory # Depo limiti (Örn: 10 birim)
        
        self.current_step = 0
        self.balance = initial_balance
        self.inventory = 0 
        self.avg_buy_price = 0 # Maliyet ortalaması
        self.net_worth = initial_balance 
        self.max_steps = len(df) - 1

    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.inventory = 0
        self.avg_buy_price = 0
        self.net_worth = self.initial_balance
        return self._next_observation()

    def _next_observation(self):
        obs = self.df.iloc[self.current_step]
        
        # Botun gördüğü özellikler:
        return np.array([
            obs['ptf'], 
            obs['hour'], 
            obs['day_of_week'],
            obs['month'],
            self.balance,
            self.inventory,
            # Teknik göstergeler
            obs.get('price_ratio', 1.0), 
            obs.get('trend', 0.0),
            # Ekstra Bilgi: Şu an kârda mıyım? (1: Evet, 0: Hayır)
            1 if self.inventory > 0 and obs['ptf'] > self.avg_buy_price else 0
        ])

    def step(self, action):
        current_price = self.df.iloc[self.current_step]['ptf']
        reward = 0
        
        # --- 1. AL (BUY) ---
        if action == 1 and self.inventory < self.max_inventory and self.balance >= current_price:
            self.balance -= current_price
            # Maliyet güncelle (Ağırlıklı Ortalama)
            total_cost = (self.inventory * self.avg_buy_price) + current_price
            self.inventory += 1
            self.avg_buy_price = total_cost / self.inventory
            reward = 0 # Alırken ödül yok

        # --- 2. SAT (SELL) ---
        elif action == 2 and self.inventory > 0:
            self.balance += current_price
            self.inventory -= 1
            
            # Sadece satınca kâr/zarar hesaplanır (Realized Profit)
            profit = current_price - self.avg_buy_price
            
            if profit > 0:
                reward = profit * 1.5 # Kârı ödüllendir
            else:
                reward = profit * 2.0 # Zararı cezalandır
            
            if self.inventory == 0:
                self.avg_buy_price = 0

        # --- 0. BEKLE (HOLD) ---
        else:
            reward = 0 # Beklemek bedava, panik yok.

        # --- İLERLE ---
        self.current_step += 1
        done = self.current_step >= self.max_steps
        self.net_worth = self.balance + (self.inventory * current_price)
        
        return self._next_observation(), reward, done, {}