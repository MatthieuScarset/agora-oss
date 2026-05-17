from pathlib import Path

from agents.issue_agent.generate_mart import generate_mart
from packages.agora.harvest.flow import harvest_flow
from packages.agora.normalize.mapper import normalize


def test_end_to_end(tmp_path: Path):
    # use the mock input included in the repo
    mock = Path("data/mock/drupalorg/issues.json")
    assert mock.exists(), "Mock input missing"

    harvest_id = "test_run"
    # run harvest (Prefect flow)
    res = harvest_flow(input_path=str(mock), harvest_id=harvest_id)
    assert res and res.get("pages") is not None

    harvest_dir = Path("data/raw/drupal/issues") / harvest_id
    assert harvest_dir.exists()

    out_norm = tmp_path / "normalized"
    normalize(harvest_dir, Path("data/schema/issue.schema.yml"), out_norm)
    # expect a parquet file
    parts = list(out_norm.glob("*.parquet"))
    assert parts, "No parquet output"

    out_mart = tmp_path / "marts"
    generate_mart(str(out_norm), str(out_mart))
    assert (out_mart / "issue_overview.json").exists()
