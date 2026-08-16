"""CLI contract tests for Track 20 tools."""

import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent


def test_query_knowledge_graph_cli(tmp_path: Path) -> None:
    """CLI tool successfully queries scope manifest and exports DCAT-AP graph."""
    scope_manifest_file = tmp_path / "scope.json"
    dcat_export_file = tmp_path / "dcat.jsonld"

    scope_manifest = {
        "datasets": [
            {
                "id": "ds-water-01",
                "title": "National River Water Quality Monitoring",
                "notes": "E. coli and nutrient concentrations in freshwater rivers.",
                "organization": {"title": "Land, Air, Water Aotearoa"},
                "tags": [{"name": "water"}, {"name": "environment"}],
                "resources": [{"format": "CSV"}],
            }
        ]
    }
    scope_manifest_file.write_text(json.dumps(scope_manifest), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "tools/query_knowledge_graph.py",
            "--scope-manifest",
            str(scope_manifest_file),
            "--query",
            "river water quality",
            "--export-dcat-ap",
            str(dcat_export_file),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Search results for 'river water quality'" in result.stdout
    assert "National River Water Quality Monitoring" in result.stdout
    assert dcat_export_file.is_file()

    graph = json.loads(dcat_export_file.read_text(encoding="utf-8"))
    assert graph["@type"] == "dcat:Catalog"


def test_notify_webhook_cli_without_url() -> None:
    """CLI tool gracefully skips notification if no webhook URL is configured."""
    result = subprocess.run(
        [sys.executable, "tools/notify_webhook.py"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0
    assert "INFO: No webhook URL configured" in result.stdout
