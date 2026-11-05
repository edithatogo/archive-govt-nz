"""Exercise the distinction between papers presented and documents tabled."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.parliament_papers_index import paper_rows


def test_reference_stays_within_presentation_schedule() -> None:
    """An identical reference outside the schedule must never be joined."""
    sample = (
        "\f  PAPERS PRESENTED\nFifty-second Parliament\n"
        "13 Feb 2018   765   Government response to a petition\n"
        "\f DOCUMENTS TABLED BY LEAVE\n13 Feb 2018   765   Other document\n"
    )
    assert paper_rows(sample) == [
        {
            "date": "2018-02-13",
            "reference": "765",
            "title_first_line": "Government response to a petition",
        }
    ]
