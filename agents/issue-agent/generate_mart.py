from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def generate_mart(normalized_dir: str, out_dir: str):
    in_dir = Path(normalized_dir)
    parts = sorted(in_dir.glob("*.parquet"))
    if not parts:
        raise FileNotFoundError(f"No parquet parts found in {normalized_dir}")
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)

    # compute top issues by comments
    if "comments" in df.columns:
        top = df.sort_values("comments", ascending=False).head(5)
        top_issues = top[
            [c for c in ["nid", "title", "comments", "url"] if c in top.columns]
        ]
        top_list = top_issues.to_dict(orient="records")
    else:
        top_list = []

    summary = {
        "top_issues": top_list,
        "summary_text": f"{len(df)} issues processed",
    }

    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    (outp / "issue_overview.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    # simple embeddings manifest stub
    (outp / "embeddings_manifest.json").write_text(
        json.dumps({"status": "stub"}, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    import typer

    app = typer.Typer()

    @app.command()
    def run(
        normalized_dir: str = "data/normalized/drupal/issues/",
        out_dir: str = "data/marts/00-mvp/",
    ):
        generate_mart(normalized_dir, out_dir)

    app()
