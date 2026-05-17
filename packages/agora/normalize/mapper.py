from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

from packages.agora.io.writer import write_parquet
from packages.agora.models.issue import Issue


def _get_by_path(obj: Dict[str, Any], path: str):
    parts = path.split(".") if path else []
    cur = obj
    for p in parts:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
    return cur


def map_page_records(
    page_path: Path, schema: Dict[str, Any]
) -> List[Dict[str, Any]]:
    with gzip.open(page_path, "rt", encoding="utf-8") as fh:
        records = json.load(fh)

    out: List[Dict[str, Any]] = []
    for rec in records:
        mapped: Dict[str, Any] = {}
        for field, meta in schema.get("fields", {}).items():
            src = meta.get("source")
            val = _get_by_path(rec, src) if src else None
            # simple transform: timestamp_seconds
            if val is not None and meta.get("transform") == "timestamp_seconds":
                # handle numeric ms or iso string
                try:
                    if isinstance(val, (int, float)) and val > 1e10:
                        # ms -> seconds
                        val = int(val // 1000)
                    else:
                        val = int(val)
                except Exception:
                    pass
            mapped[field] = val
        out.append(mapped)
    return out


def normalize(harvest_dir: Path, schema_path: Path, out_dir: Path):
    schema = yaml.safe_load(schema_path.read_text())
    pages = sorted((harvest_dir / "pages").glob("*.json.gz"))
    rows = []
    for p in pages:
        recs = map_page_records(p, schema)
        for r in recs:
            # validate via Pydantic
            try:
                issue = Issue.model_validate(r)
                rows.append(issue.model_dump())
            except Exception as e:
                # write simple error log and continue
                errp = Path("logs/normalize_errors.log")
                errp.parent.mkdir(parents=True, exist_ok=True)
                with errp.open("a", encoding="utf-8") as ef:
                    ef.write(f"Error validating record: {e}\n")
    # write parquet
    write_parquet(rows, out_dir)


if __name__ == "__main__":
    import typer

    app = typer.Typer()

    @app.command()
    def run(
        harvest_dir: str,
        out_dir: str,
        schema: str = "data/schema/issue.schema.yml",
    ):
        normalize(Path(harvest_dir), Path(schema), Path(out_dir))

    app()
