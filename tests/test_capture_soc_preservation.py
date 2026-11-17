"""Prove extraction failure cannot discard an acquired official original."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import test_capture_soc_sources as support


class PreservationTests(unittest.TestCase):
    """Retain original source identity even for unsupported spreadsheet features."""

    def setUp(self):
        support.AcquisitionTests.setUp(self)

    def test_original_survives_extraction_failure(self):
        raw = support.workbook({"xl/externalLinks/externalLink1.xml": "<x/>"})
        with TemporaryDirectory() as directory:
            output = Path(directory) / "capture"
            with patch.object(self.mod, "SOURCES", [self.mod.SOURCES[0]]), patch.object(self.mod, "download", return_value=(raw, {})):
                result = self.mod.capture(output)
            self.assertEqual((output / "census2023_general_2020.xlsx").read_bytes(), raw)
            self.assertEqual(result["records"][0]["status"], "captured_extraction_failed")
            self.assertEqual(len(result["records"][0]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
