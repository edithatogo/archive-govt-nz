"""Offline controls for official source acquisition and lossless XLSX cells."""

import importlib.util
import io
import sys
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools/capture_soc_sources.py"
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


def workbook(extra=None, formula=False):
    """Build a small explicitly synthetic OOXML source."""
    content = {
        "xl/workbook.xml": f'<workbook xmlns="{NS}" xmlns:r="{REL}"><sheets><sheet name="Population" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Target="/xl/worksheets/sheet1.xml" Type="{REL}/worksheet"/></Relationships>',
        "xl/sharedStrings.xml": f'<sst xmlns="{NS}"><si><t>Area</t></si><si><r><t>Median </t></r><r><t>income</t></r></si></sst>',
        "xl/worksheets/sheet1.xml": f'<worksheet xmlns="{NS}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>TEST</t></is></c><c r="B2"><v>123.50</v></c><c r="C2" t="inlineStr"><is><t>..</t></is></c><c r="D2"><f>SUM(B2)</f><v>123.50</v></c></row></sheetData></worksheet>',
    }
    content.update(extra or {})
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in content.items():
            archive.writestr(name, value)
    return out.getvalue()


class AcquisitionTests(unittest.TestCase):
    """Exercise boundaries without a network call or public side effect."""

    def setUp(self):
        self.assertTrue(SCRIPT.exists(), "official source acquisition not implemented")
        spec = importlib.util.spec_from_file_location("capture_soc_sources", SCRIPT)
        self.mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.mod
        spec.loader.exec_module(self.mod)

    def test_preserves_all_cell_types_and_source_coordinates(self):
        result = self.mod.workbook_cells(workbook())
        cells = {c[0]: c for c in result[0]["cells"]}
        self.assertEqual(result[0]["name"], "Population")
        self.assertEqual(cells["B1"][2], "Median income")
        self.assertEqual(cells["B2"][2], "123.50")
        self.assertEqual(cells["C2"][2], "..")
        self.assertEqual(cells["D2"][3], "SUM(B2)")

    def test_rejects_html_error_body(self):
        with self.assertRaises(ValueError):
            self.mod.workbook_cells(b"<html>denied</html>")

    def test_rejects_archive_traversal(self):
        with self.assertRaises(ValueError):
            self.mod.workbook_cells(workbook({"../outside": "bad"}))

    def test_rejects_dtd(self):
        with self.assertRaises(ValueError):
            self.mod.workbook_cells(workbook({"xl/sharedStrings.xml": '<!DOCTYPE x [<!ENTITY y "hi">]><sst/>'}))

    def test_rejects_external_links(self):
        with self.assertRaises(ValueError):
            self.mod.workbook_cells(workbook({"xl/externalLinks/externalLink1.xml": "<x/>"}))

    def test_rejects_macros(self):
        with self.assertRaises(ValueError):
            self.mod.workbook_cells(workbook({"xl/vbaProject.bin": "bad"}))

    def test_rejects_expanded_size_limit(self):
        with self.assertRaises(ValueError):
            self.mod.workbook_cells(workbook(), max_expanded=1)

    def test_rejects_duplicate_coordinate(self):
        xml = f'<worksheet xmlns="{NS}"><sheetData><row><c r="A1"><v>1</v></c><c r="A1"><v>2</v></c></row></sheetData></worksheet>'
        with self.assertRaises(ValueError):
            self.mod.workbook_cells(workbook({"xl/worksheets/sheet1.xml": xml}))

    def test_rejects_unknown_shared_string(self):
        xml = f'<worksheet xmlns="{NS}"><sheetData><row><c r="A1" t="s"><v>99</v></c></row></sheetData></worksheet>'
        with self.assertRaises(ValueError):
            self.mod.workbook_cells(workbook({"xl/worksheets/sheet1.xml": xml}))

    def test_only_registered_https_hosts(self):
        self.assertEqual(self.mod.validate_url("https://www3.parliament.nz/media/x.xlsx").hostname, "www3.parliament.nz")
        for url in ["http://www3.parliament.nz/x", "https://evil.example/x", "https://a:b@www3.parliament.nz/x", "https://www3.parliament.nz:444/x", "https://www3.parliament.nz/x?token=secret"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.mod.validate_url(url)

    def test_source_register_has_both_systems_and_boundary_vintages(self):
        register = self.mod.SOURCES
        census = [s for s in register if s["family"] == "census"]
        self.assertEqual(len(census), 4)
        self.assertEqual({(s["system"], s["boundary"]) for s in census}, {("general_electorate", "2020"), ("general_electorate", "2025"), ("maori_electorate", "2020"), ("maori_electorate", "2025")})
        self.assertTrue(all(s["reference_year"] == 2023 for s in census))


if __name__ == "__main__":
    unittest.main()
