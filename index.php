<?php
// Caminhos dos ficheiros baseados no teu ambiente atual
$json_path = 'outputs_estoque/dashboard_insights.json';
$log_path = 'logs/log_treinamento_estoque.csv';

// Carregamento de Insights gerados pela IA
$insights = file_exists($json_path) ? json_decode(file_get_contents($json_path), true) : [];

// Carregamento dos logs de treino do PyTorch
$training_logs = [];
if (file_exists($log_path) && ($handle = fopen($log_path, "r")) !== FALSE) {
    fgetcsv($handle); // Ignorar o cabeçalho (epoch, loss)
    while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
        if(isset($data[0], $data[1])) {
            $training_logs[] = [
                'epoch' => (int)$data[0],
                'loss' => (float)$data[1]
            ];
        }
    }
    fclose($handle);
}

// Cálculo de métricas rápidas
$correlacao_clima = isset($insights['correlacao_temp']) ? round($insights['correlacao_temp'] * 100) : '--';
$impacto_selic = isset($insights['correlacao_selic']) ? round($insights['correlacao_selic'] * 100, 1) : '--';
$loss_final = !empty($training_logs) ? round(end($training_logs)['loss'], 5) : '--';
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nextar Intelligence Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg: #f8fafd;
            --card-bg: #ffffff;
            --text-main: #334155;
            --pastel-blue: #b2e2f2;
            --pastel-pink: #ffb7b2;
            --pastel-mint: #baffc9;
            --pastel-purple: #d1b2f2;
        }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; padding: 2rem; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 3rem; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card { background: var(--card-bg); padding: 1.5rem; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-top: 6px solid var(--pastel-blue); }
        .card-pink { border-top-color: var(--pastel-pink); }
        .card-mint { border-top-color: var(--pastel-mint); }
        
        h2 { font-size: 1rem; color: #64748b; margin: 0; text-transform: uppercase; }
        .stat { font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0; color: #1e293b; }
        
        .chart-box { background: var(--card-bg); padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        
        .ia-card { background: #f0f7ff; border-top: 5px solid var(--pastel-purple); padding: 1.5rem; border-radius: 1rem; }
        .ia-text { font-size: 1.1rem; line-height: 1.6; color: #334155; font-style: italic; }
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>🚀 Nextar Intelligence Dashboard</h1>
        <p>Análise Preditiva e Inteligência de Dados para o Varejo</p>
    </header>

    <div class="grid">
        <div class="card">
            <h2>Correlação Climática</h2>
            <div class="stat"><?php echo $correlacao_clima; ?>%</div>
            <p>Impacto das variações de temperatura nas vendas.</p>
        </div>
        
        <div class="card card-pink">
            <h2>Impacto SELIC</h2>
            <div class="stat"><?php echo $impacto_selic; ?>%</div>
            <p>Sensibilidade do inventário às taxas de juro.</p>
        </div>

        <div class="card card-mint">
            <h2>Precisão IA (Loss)</h2>
            <div class="stat"><?php echo $loss_final; ?></div>
            <p>Erro médio após <?php echo count($training_logs); ?> épocas.</p>
        </div>
    </div>

    <div class="chart-box">
        <h3 style="margin-top: 0;">Evolução do Treinamento (Loss History)</h3>
        <div style="height: 300px;">
            <canvas id="lossChart"></canvas>
        </div>
    </div>

    <div class="ia-card">
        <h3 style="color: #6d28d9; display: flex; align-items: center; margin-top: 0;">
            <span style="margin-right: 10px;">🧠</span> Sugestão da Inteligência Nextar
        </h3>
        <div class="ia-text">
            <?php 
                echo isset($insights['narrativa_ia']) 
                     ? nl2br(htmlspecialchars($insights['narrativa_ia'])) 
                     : "Aguardando análise da IA local... (Certifica-te que o LM Studio está a correr e executaste o script narrativa_ia.py)"; 
            ?>
        </div>
    </div>
</div>

<script>
    const ctx = document.getElementById('lossChart').getContext('2d');
    
    // Injeção segura de dados PHP para JavaScript
    const epochs = <?php echo json_encode(array_column($training_logs, 'epoch')); ?>;
    const lossData = <?php echo json_encode(array_column($training_logs, 'loss')); ?>;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: epochs,
            datasets: [{
                label: 'Perda do Modelo (MSE)',
                data: lossData,
                borderColor: '#ffb7b2',
                backgroundColor: 'rgba(255, 183, 178, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: false, grid: { color: '#f1f5f9' } }
            },
            plugins: {
                legend: { display: true, position: 'top' }
            }
        }
    });
</script>

</body>
</html>