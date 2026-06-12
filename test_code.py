import pandas as pd
import json

df = pd.read_parquet('https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-04.parquet')

payment_type_mapping = {
    1: 'Credit Card',
    2: 'Cash',
    3: 'No Charge',
    4: 'Dispute',
    5: 'Unknown'
}

df['payment_type_name'] = df['payment_type'].map(payment_type_mapping)

payment_distribution = df['payment_type_name'].value_counts()
payment_percentages = (payment_distribution / payment_distribution.sum() * 100).round(2)

labels = payment_percentages.index.tolist()
values = payment_percentages.values.tolist()

colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']

chart_data = {
    'labels': labels,
    'datasets': [{
        'data': values,
        'backgroundColor': colors[:len(labels)],
        'borderColor': '#fff',
        'borderWidth': 2
    }]
}

chart_data_json = json.dumps(chart_data)

FINAL_OUTPUT = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Type Distribution - NYC Yellow Taxi (April 2026)</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 800px;
            width: 100%;
        }}
        
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 14px;
        }}
        
        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin-bottom: 30px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-label {{
            font-size: 12px;
            opacity: 0.9;
            margin-bottom: 8px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
        }}
        
        .stat-percent {{
            font-size: 14px;
            margin-top: 5px;
            opacity: 0.8;
        }}
        
        footer {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        
        @media (max-width: 600px) {{
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 22px;
            }}
            
            .chart-wrapper {{
                height: 300px;
            }}
            
            .stat-card {{
                padding: 15px;
            }}
            
            .stat-value {{
                font-size: 18px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💳 Payment Type Distribution</h1>
        <p class="subtitle">NYC Yellow Taxi Data - April 2026</p>
        
        <div class="chart-wrapper">
            <canvas id="paymentChart"></canvas>
        </div>
        
        <div class="stats">
"""

for label, percentage in zip(labels, values):
    count = int(payment_distribution[label])
    FINAL_OUTPUT += f"""            <div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{percentage:.1f}%</div>
                <div class="stat-percent">{count:,} trips</div>
            </div>
"""

FINAL_OUTPUT += """        </div>
        
        <footer>
            <p>Data source: NYC Yellow Taxi Trip Data | Generated with Pandas & Chart.js</p>
        </footer>
    </div>
    
    <script>
        const ctx = document.getElementById('paymentChart').getContext('2d');
        const chartData = """ + chart_data_json + """;
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 14,
                                weight: 'bold'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return label + ': ' + value.toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""