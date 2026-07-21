from datetime import datetime
from pathlib import Path
import config

import pandas as pd
from jinja2 import Environment, FileSystemLoader

def aggregate(df: pd.DataFrame, top_n: int = 10) -> dict:
    return {
        'kpi': {
            '총매출': int(df['amount'].sum()),
            '주문 수': len(df),
            '평균 주문액': round(df['amount'].mean(), 1)
        },
        'by_category': (df.groupby('category', observed=True)['amount']
                        .sum().sort_values(ascending=False)
                        .head(top_n).reset_index()
                        .to_dict('records'))
    }

def render(data: dict, cfg: config.Config) -> Path:
    env = Environment(loader=FileSystemLoader('Python_data_0721_Day2/Total3/'))
    tpl = env.get_template('report.html')
    html = tpl.render(
        title=cfg.title,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **data,
    )

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    out = cfg.output_dir / f"report_{stamp}.html"
    out.write_text(html, encoding='utf-8')
    return out

def run_once():
    df = pd.read_csv(config.CONFIG.data_path)
    df['amount'] = df['quantity'] * df['unit_price'] * (1-df['discount'])
    render(aggregate(df), config.CONFIG)