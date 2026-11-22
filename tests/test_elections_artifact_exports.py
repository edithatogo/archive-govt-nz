"""Exercise legacy export serialization, without validating its research claims."""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pytest
from PIL import Image
from pptx import Presentation
from pptx.shapes.autoshape import Shape
from pptx.shapes.picture import Picture

from archive_govt_nz.domains.elections import (
    generate_beyond_frontier,
    generate_presentation,
)

FIGURE_NAMES = {
    "beyond_frontier_1_wetware_slime_mould.png",
    "beyond_frontier_2_psychoacoustic_sonification_haptics.png",
    "beyond_frontier_3_neural_manifold_latent_landscape.png",
    "beyond_frontier_4_true_quantum_superposition_qubits.png",
    "beyond_frontier_5_autonomous_multiagent_parliament.png",
}


def _assert_png_exports(paths: list[Path], root: Path) -> dict[str, bytes]:
    """Require readable high-resolution images and identical publication copies."""
    assert {path.name for path in paths} == FIGURE_NAMES
    assert len(paths) == len(FIGURE_NAMES)
    payloads = {path.name: path.read_bytes() for path in paths}
    assert len({hashlib.sha256(data).digest() for data in payloads.values()}) == len(
        FIGURE_NAMES
    )
    space = root / "spaces" / "nz-election-explorer"
    for path in paths:
        assert path.parent == root / "figures"
        data = payloads[path.name]
        with Image.open(BytesIO(data)) as image:
            assert image.format == "PNG"
            image.load()
            assert image.width >= 3000
            assert image.height >= 2000
            assert image.info["dpi"] == pytest.approx((300, 300), abs=0.1)
            channel_variation = []
            for extrema in image.convert("RGB").getextrema():
                assert isinstance(extrema, tuple)
                channel_variation.append(extrema[0] < extrema[1])
            assert any(channel_variation)
        assert (space / path.name).read_bytes() == data
        assert (space / "static" / path.name).read_bytes() == data
    return payloads


def _assert_presentation(path: Path, payloads: dict[str, bytes]) -> None:
    """Require a readable deck with embedded images, text and bounded geometry."""
    with ZipFile(path) as package:
        assert package.testzip() is None
        assert "ppt/presentation.xml" in package.namelist()
    deck = Presentation(str(path))
    width, height = deck.slide_width, deck.slide_height
    assert width is not None
    assert height is not None
    assert width / height == pytest.approx(16 / 9, rel=0.001)
    assert len(deck.slides) >= len(payloads) + 2
    embedded = []
    text = []
    for slide in deck.slides:
        for shape in slide.shapes:
            assert shape.width > 0
            assert shape.height > 0
            assert 0 <= shape.left < shape.left + shape.width <= width
            assert 0 <= shape.top < shape.top + shape.height <= height
            if isinstance(shape, Picture):
                embedded.append(hashlib.sha256(shape.image.blob).digest())
            if shape.has_text_frame:
                assert isinstance(shape, Shape)
                text.append(shape.text)
    assert len(embedded) == len(payloads)
    assert set(embedded) == {
        hashlib.sha256(data).digest() for data in payloads.values()
    }
    assert "NEW ZEALAND GENERAL ELECTION ANALYTICS" in "\n".join(text)
    assert "METHODOLOGY & SPECIFICATION" in "\n".join(text)


def test_legacy_election_exports_are_readable_and_self_contained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Render real exports offline; certify file contracts, not analytical claims."""
    root = tmp_path / "archive"
    (root / "spaces" / "nz-election-explorer" / "static").mkdir(parents=True)
    module_path = root / "src/archive_govt_nz/domains/elections/generator.py"
    monkeypatch.setattr(generate_beyond_frontier, "__file__", str(module_path))
    backend = plt.get_backend()
    rng_state = np.random.get_state()  # noqa: NPY002 - preserve the generators' complete legacy state
    try:
        plt.switch_backend("Agg")
        figures = generate_beyond_frontier.generate_all_beyond_frontier_figures()
        payloads = _assert_png_exports(figures, root)
        output = root / "presentation" / "legacy-illustrations.pptx"
        result = generate_presentation.build_election_presentation(
            output, root / "figures"
        )
        assert result == output
        _assert_presentation(output, payloads)
    finally:
        np.random.set_state(rng_state)  # noqa: NPY002 - restore cached Gaussian state too
        plt.close("all")
        plt.switch_backend(backend)
