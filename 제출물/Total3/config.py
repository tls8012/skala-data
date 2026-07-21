from dataclasses import dataclass
from pathlib import Path

class Config:
    data_path:  Path = Path('utils/sales_raw.csv')
    output_dir: Path = Path('out_yay')
    title: str = "DONE!"
    top_n: int = 10

CONFIG = Config()