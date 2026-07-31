"""Non-interactive command-line interface."""

import json
from typing import Literal

from cyclopts import App

from archive_govt_nz import __version__

app = App(
    name="archive-govt-nz",
    help="Evidence-first archival tooling for New Zealand government data.",
)


@app.command
def version(format: Literal["text", "json"] = "text") -> None:
    """Report the installed archive-govt-nz version."""
    if format == "json":
        payload = {
            "command": "version",
            "schema_version": "archive-govt-nz.cli/v1",
            "status": "success",
            "version": __version__,
        }
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return

    print(__version__)


def main() -> None:
    """Run the command-line application."""
    app()
