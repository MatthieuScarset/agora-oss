from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


def write_parquet(
    rows: Iterable[Mapping], out_dir: Path, filename: str = "part-000.parquet"
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(list(rows))
    out_path = out_dir / filename
    df.to_parquet(out_path, engine="pyarrow", compression="snappy", index=False)
