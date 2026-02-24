import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO E CARREGAMENTO
# ==========================================
os.makedirs('logs', exist_ok=True)
os.makedirs('modelos', exist_ok=True)
os.makedirs('outputs_estoque', exist_ok=True)

# Lendo seu CSV (ajuste o nome se necessário)
CAMINHO_CSV = 'dados.csv'

if not os.path.exists(CAMINHO_CSV):
    print(f"❌ Erro: O arquivo {CAMINHO_CSV} não foi encontrado!")
    # Criando um exemplo rápido caso você queira testar agora
    df_exemplo = pd.DataFrame({
        'Nome_Produto': ['Tenis Pro', 'Casaco Lã', 'Camiseta'],
        'Categoria': ['Calçados', 'Inverno', 'Verão'],
        'Preco': [299.0, 450.0, 89.0]
    })
    df_exemplo.to_csv(CAMINHO_CSV, index=False)
    print("⚠️ Criado um arquivo de exemplo para evitar erro.")

df_estoque = pd.read_csv(CAMINHO_CSV)
print(f"✅ Estoque carregado: {len(df_estoque)} produtos encontrados.")

# ==========================================
# 2. ENGENHARIA DE DADOS (DATA ENRICHMENT)
# ==========================================
# Como o estoque é estático, vamos gerar 365 dias de história para o treinamento
datas = pd.date_range(start="2024-01-01", periods=365, freq='D')

def gerar_historico_vendas(estoque):
    historico_completo = []
    
    # Macro de Curitiba/SC
    temp = 18 + 12 * np.cos(2 * np.pi * (datas.dayofyear + 10) / 365) + np.random.normal(0, 2, 365)
    selic = np.linspace(11.75, 10.5, 365)
    
    for _, item in estoque.iterrows():
        # Lógica: Produtos caros vendem menos com SELIC alta.
        # Produtos de 'Inverno' ou caros vendem mais no frio de Curitiba.
        base_venda = 100 / (item['Preco'] / 50) # Preço influencia volume
        
        vendas = base_venda - 2 * (temp - 20) - 5 * (selic - 11) + np.random.normal(0, 5, 365)
        vendas = np.maximum(vendas, 2) # Mínimo de 2 vendas/dia
        
        for i in range(len(datas)):
            historico_completo.append({
                'produto': item['Nome_Produto'],
                'preco': item['Preco'],
                'data': datas[i],
                'vendas': vendas[i],
                'temp': temp[i],
                'selic': selic[i]
            })
    return pd.DataFrame(historico_completo)

df_treino = gerar_historico_vendas(df_estoque)
df_treino.to_csv('outputs_estoque/base_treinamento_completa.csv', index=False)

# ==========================================
# 3. PREPARAÇÃO DA REDE NEURAL (PYTORCH)
# ==========================================
# Vamos prever 'vendas' usando [preco, temp, selic]
X = df_treino[['preco', 'temp', 'selic']].values.astype(np.float32)
y = df_treino['vendas'].values.reshape(-1, 1).astype(np.float32)

# Normalização (Z-Score) - Guardamos as médias para o Dashboard depois
X_mean, X_std = X.mean(axis=0), X.std(axis=0)
y_mean, y_std = y.mean(), y.std()

X_t = torch.from_numpy((X - X_mean) / X_std)
y_t = torch.from_numpy((y - y_mean) / y_std)

class NextarDeepStock(nn.Module):
    def __init__(self):
        super(NextarDeepStock, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(3, 64),
            nn.ReLU(),
            nn.Dropout(0.2), # Evita Overfitting
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    def forward(self, x): return self.layers(x)

model = NextarDeepStock()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# ==========================================
# 4. LOOP DE TREINAMENTO (COM EPOCHS E LOGS)
# ==========================================
epochs = 300
logs = []

print(f"🚀 Iniciando treinamento para {len(df_estoque)} SKUs...")

for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()
    outputs = model(X_t)
    loss = criterion(outputs, y_t)
    loss.backward()
    optimizer.step()
    
    if (epoch + 1) % 50 == 0:
        print(f"Época {epoch+1}/{epochs} | Loss: {loss.item():.6f}")
    
    logs.append({"epoch": epoch+1, "loss": loss.item()})

# Salvar logs e Pesos
pd.DataFrame(logs).to_csv('logs/log_treinamento_estoque.csv', index=False)
torch.save(model.state_dict(), 'modelos/pesos_v1.pth')

# ==========================================
# 5. VISUALIZAÇÃO E EXPORTAÇÃO
# ==========================================
plt.figure(figsize=(10, 4))
plt.plot(pd.DataFrame(logs)['loss'], color='purple')
plt.title("Otimização do Modelo de Demanda - Nextar")
plt.xlabel("Epochs")
plt.ylabel("Erro")
plt.savefig('outputs_estoque/curva_aprendizado.png')

# Gerar Predição para o Dashboard
model.eval()
with torch.no_grad():
    pred_final = model(X_t).numpy() * y_std + y_mean
    df_treino['predicao'] = pred_final

# Exportar para o Three.js (Amostra de 500 pontos para não pesar)
df_viz = df_treino.sample(min(500, len(df_treino)))
viz_data = []
for _, r in df_viz.iterrows():
    viz_data.append({
        "x": float(r['temp']), 
        "y": float(r['vendas']), 
        "z": float(r['preco']),
        "p": float(r['predicao'])
    })

with open('outputs_estoque/three_data_estoque.json', 'w') as f:
    json.dump(viz_data, f)

print("✅ Treinamento finalizado. Arquivos gerados em /outputs_estoque")