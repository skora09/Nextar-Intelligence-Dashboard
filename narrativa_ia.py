import pandas as pd
import json
import openai
import os
import re # Biblioteca para limpar as tags <think>

# Configuração LM Studio
client = openai.OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def analisar_com_ia_local():
    LOG_TREINO = 'logs/log_treinamento_estoque.csv'
    BASE_DADOS = 'outputs_estoque/base_treinamento_completa.csv'
    CAMINHO_JSON = 'outputs_estoque/dashboard_insights.json'
    
    os.makedirs('outputs_estoque', exist_ok=True)

    if not os.path.exists(LOG_TREINO) or not os.path.exists(BASE_DADOS):
        print("❌ Arquivos de treino ou base de dados não encontrados.")
        return

    df_log = pd.read_csv(LOG_TREINO)
    df_base = pd.read_csv(BASE_DADOS)

    # Processamento técnico
    loss_inicial = df_log['loss'].iloc[0]
    loss_final = df_log['loss'].iloc[-1]
    correlacoes = df_base[['vendas', 'temp', 'selic', 'preco']].corr()['vendas'].to_dict()

    prompt = f"""
            Você é o "Nextar Strategist", um Consultor Sênior de Varejo com doutorado em Ciência de Dados e vasta experiência no mercado de Santa Catarina e Paraná.
            Sua missão é traduzir métricas técnicas complexas em ações práticas que geram lucro para pequenos e médios lojistas.

            ### CONTEXTO DO NEGÓCIO
            O lojista utiliza o sistema Nextar para gerir estoque e vendas. 
            Ele está localizado em uma região (SC/PR) onde o clima é volátil (frentes frias súbitas) e a economia é sensível a variações de crédito.

            ### DADOS DO MOTOR DE IA (PyTorch)
            1. Performance do Modelo: O erro (Loss) caiu de {loss_inicial:.4f} para {loss_final:.4f}. 
               *Nota: Se a queda foi maior que 50%, o modelo está muito confiável.*
            2. Variável CLIMA: A correlação com a temperatura é de {correlacoes['temp']:.2f}.
            3. Variável ECONOMIA: A correlação com a taxa SELIC é de {correlacoes['selic']:.2f}.

            ### SUAS DIRETRIZES DE RESPOSTA
            1. FOCO EM AÇÃO: Não explique apenas o "quê", explique o "como agir".
            2. TONE-OF-VOICE: Use um tom profissional, porém alegre e encorajador. Evite termos técnicos como "MSE" ou "convergência" — transforme isso em "precisão" ou "inteligência".
            3. CORRELAÇÃO EXTERNA: Relacione os dados com a realidade de Curitiba ou SC (ex: frentes frias, feriados, hábitos locais).

            ### ESTRUTURA DA RESPOSTA (Obrigatória):
            - O INSIGHT (Uma frase impactante sobre o que a IA descobriu).
            - POR QUE ISSO IMPORTA? (A explicação lógica ligando clima/economia ao estoque).
            - AÇÃO IMEDIATA (O que o lojista deve fazer amanhã de manhã).
            - DICA DE SEO (Como usar a IA de catálogo para aproveitar essa tendência).
            """

    print("🤖 IA processando... (Limpando tags <think>)")

    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        raw_content = response.choices[0].message.content

        # --- LIMPEZA DAS TAGS <think> ---
        # Remove tudo que estiver entre <think> e </think>
        narrativa = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
        
        # Caso o modelo não use tags mas escreva o raciocínio, 
        # garantimos que não haja restos de tags vazias
        narrativa = narrativa.replace('<think>', '').replace('</think>', '').strip()

        # 4. CARREGAR E SALVAR NO JSON
        if os.path.exists(CAMINHO_JSON):
            with open(CAMINHO_JSON, 'r', encoding='utf-8') as f:
                dados = json.load(f)
        else:
            dados = {}

        # IMPORTANTE: Usamos 'narrativa_ia' para bater com o seu index.php
        dados['narrativa_ia'] = narrativa
        
        # Atualiza métricas para o Dashboard
        dados['correlacao_temp'] = correlacoes['temp']
        dados['correlacao_selic'] = correlacoes['selic']
        dados['media_vendas_recentes'] = float(df_base['vendas'].tail(30).mean())
        dados['vendas_frio_media'] = float(df_base[df_base['temp'] < 16]['vendas'].mean())

        with open(CAMINHO_JSON, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
            
        print("✅ Insight limpo e salvo com sucesso!")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    analisar_com_ia_local()