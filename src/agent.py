import numpy as np
import random
import pickle
import os

class QLearningAgent:
    def __init__(self, action_size=3, learning_rate=0.1, discount_rate=0.99, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01):
        self.action_size = action_size 
        self.lr = learning_rate 
        self.gamma = discount_rate 
        self.epsilon = epsilon 
        self.epsilon_decay = epsilon_decay 
        self.epsilon_min = epsilon_min
        self.q_table = {} 

    def get_state_key(self, state):
        # State içinden önemli bilgileri alıp bir anahtar oluşturur
        hour = int(state[1])
        inventory = int(state[5])
        
        # Fiyat Durumu (Price Ratio)
        ratio = state[6]
        if ratio < 0.90: price_status = 0 # Ucuz
        elif ratio > 1.10: price_status = 2 # Pahalı
        else: price_status = 1 # Normal
        
        # Trend
        trend_val = state[7]
        if trend_val > 0: trend = 1 # Artıyor
        else: trend = 0 # Düşüyor/Yatay
        
        # Kârlılık (Maliyetin üstünde miyiz?)
        is_profitable = int(state[8])

        return f"{hour}_{inventory}_{price_status}_{trend}_{is_profitable}"

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state_key = self.get_state_key(state)
        if state_key not in self.q_table:
            return random.randrange(self.action_size)
        return np.argmax(self.q_table[state_key])

    def learn(self, state, action, reward, next_state, done):
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)
        
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_size)
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = np.zeros(self.action_size)
        
        target = reward + self.gamma * np.max(self.q_table[next_state_key])
        self.q_table[state_key][action] += self.lr * (target - self.q_table[state_key][action])
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_brain(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self.q_table, f)
        print(f"🧠 Beyin kaydedildi: {filepath}")

    def load_brain(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                self.q_table = pickle.load(f)
            self.epsilon = self.epsilon_min
            print(f"🧠 Beyin yüklendi: {filepath}")
        else:
            print("⚠️ Beyin bulunamadı!")