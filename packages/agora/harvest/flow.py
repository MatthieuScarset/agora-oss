from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Dict, List

from prefect import flow, task


@task(retries=3, retry_delay_seconds=2)
def write_page(page_data: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_path, "wt", encoding="utf-8") as fh:
        json.dump(page_data, fh)


@task
def write_manifest(manifest: Dict[str, Any], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))


@flow(name="harvest_flow")
def harvest_flow(
    input_path: str,
    provider: str = "drupal",
    entity_type: str = "issues",
    harvest_id: str | None = None,
    page_size: int = 100,
    concurrency: int = 4,
) -> Dict[str, Any]:
    """Simple Prefect flow to convert an input JSON list into
    a raw harvest layout.

    This flow is provider-agnostic and intended for local/mock usage. It
    writes `manifest.json`, `checkpoint.json`, and gzipped page files under
    the harvest directory: `data/raw/{provider}/{entity_type}/{harvest_id}/`.
    """
    src = Path(input_path)
    data = []
    if src.is_file():
        data = json.loads(src.read_text())
    else:
        raise FileNotFoundError(f"Input not found: {input_path}")

    if harvest_id is None:
        harvest_id = "manual"

    base = Path("data/raw") / provider / entity_type / harvest_id
    pages_dir = base / "pages"

    total = len(data)
    manifest = {
        "provider": provider,
        "entity_type": entity_type,
        "harvest_id": harvest_id,
        "total_records": total,
    }

    # split into pages
    page_no = 0
    for i in range(0, total, page_size):
        page_no += 1
        chunk = data[i : i + page_size]
        page_file = pages_dir / f"page_{page_no:06d}.json.gz"
        write_page.submit(chunk, page_file)

    write_manifest.submit(manifest, base / "manifest.json")
    # write a simple checkpoint
    write_manifest.submit({"last_page": page_no}, base / "checkpoint.json")

    return {"harvest_id": harvest_id, "pages": page_no}


def main() -> None:
    # simple CLI entry for manual invocation
    import typer

    app = typer.Typer()

    @app.command()
    def run(input_path: str, harvest_id: str = "manual"):
        harvest_flow(input_path=input_path, harvest_id=harvest_id)

    app()


if __name__ == "__main__":
    main()
