"""Bind retained SOC source/extract bytes to independently recorded capture pins.

No network, source-rights decision, workflow activation or publication is performed.
Changing this cohort requires a reviewed source-version change, not a resealed manifest.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

# From retained artifact 14220795860, independently matched to all original cells.
PINS: dict[str, tuple[str, str, str, str]] = {
    'census2023_general_2020': ('c3bd589f7aa6ff053c3a1ac9c1d4d678e6f30908c5b7d5bcf6533b38cd501fe2', 'a3dd56bbfaf47734f9eb1e9be702f3f3d052693f8973d75731929aff0da27b39', 'general_electorate', '2020'),
    'census2023_maori_2020': ('d775725a52511a4869c2da4e7a17dabff07b0bb48cebb95a5aafe6c6e60f2735', '321d6c477eeb1cb6b6af658d5b8f211a58d45d9af07f0578ea6174fe7e4f5529', 'maori_electorate', '2020'),
    'census2023_general_2025': ('50eff43591730c3c670e94e6d75058c8e376635fdac64fd471c4238685b3a1d2', '2ab8340f939c83cf67ddb62f6caf60cbbd85adc9ea819e5f12d3e56a9f9c9239', 'general_electorate', '2025'),
    'census2023_maori_2025': ('85cb7fa45eb5a245d6281d4ff235cc6eac57468225699a4808240ce1f1374cf6', '247a7f783877693ef401e51f9d5c9ee4984fdf007305664ce32dd989dbfed9ba', 'maori_electorate', '2025'),
    'turnout2023_age_descent': ('ecf32160d7aa7a024861bd402877f2eacd11a1a5308eac385f2948447c1a78be', 'b65b9c8fd181b03dbc280ae3922cee3ff9cb80311c57bf6314417a38f7deee0e', 'source_defined_electorates', '2020'),
    'turnout2023_sa2': ('a03f9f994ba9a304fd33259aebed153ea5f59c47a1777729ecac103cb295f443', '8f96f3043a1ed5db77ed75bb133402c4c3bbced1abfb6bb56c414e9ba4756c7e', 'source_defined_sa2', 'requires_workbook_metadata'),
}
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def require(condition: bool, message: str) -> None:
    """Reject unsafe or incomplete source evidence without leaking source values."""
    if not condition:
        raise ValueError(message)


def retained_bytes(directory: Path, name: str) -> bytes:
    """Read only bounded regular files directly inside the supplied snapshot."""
    path = directory / name
    require(not path.is_symlink() and path.is_file(), 'missing/unsafe retained file')
    require(path.stat().st_size <= 128_000_000, 'retained file exceeds limit')
    return path.read_bytes()


def verify_bound_capture(directory: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Reject a changed extract even when its companion manifest was rehashed."""
    records = manifest.get('records')
    require(isinstance(records, list), 'invalid source inventory')
    ids = [r.get('id') for r in records if isinstance(r, dict)]
    require(len(ids) == len(records) == len(PINS) and set(ids) == set(PINS),
            'incomplete/duplicate/unapproved source inventory')
    checked = []
    for record in records:
        identity = record['id']
        original_pin, extract_pin, system, boundary = PINS[identity]
        require(record.get('status') == 'captured', 'incomplete source capture')
        require((record.get('system'), record.get('boundary')) == (system, boundary),
                'source geographic metadata mismatch')
        require(record.get('sha256') == original_pin
                and record.get('cells_sha256') == extract_pin,
                'independent original/extract hash pin mismatch')
        original = retained_bytes(directory, identity + '.xlsx')
        extract = retained_bytes(directory, identity + '.cells.json')
        require(type(record.get('bytes')) is int and len(original) == record['bytes'],
                'original size mismatch')
        require(hashlib.sha256(original).hexdigest() == original_pin,
                'original bytes do not match independent pin')
        require(hashlib.sha256(extract).hexdigest() == extract_pin,
                'extract bytes do not match independent pin')
        payload = json.loads(extract)
        require(payload.get('source_sha256') == original_pin,
                'extract source binding mismatch')
        checked.append({'source_id': identity, 'original_sha256': original_pin,
                        'extract_sha256': extract_pin})
    return {'schema_version': 'soc-bound-capture-v1', 'sources': len(checked),
            'records': sorted(checked, key=lambda r: r['source_id']),
            'publication_authorised': False, 'source_rights_admitted': False}


def original_cells(raw: bytes) -> list[dict[str, Any]]:
    """Independently recover native cell tuples from already pinned OOXML bytes."""
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        names = [m.filename for m in members]
        require(len(names) == len(set(names)) and len(names) <= 2000,
                'duplicate/oversized workbook inventory')
        require(sum(m.file_size for m in members) <= 128_000_000,
                'expanded workbook limit')
        require(all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
                    and '\\' not in n for n in names), 'unsafe workbook member')

        def xml(name: str) -> ET.Element:
            raw_xml = archive.read(name)
            require(b'<!DOCTYPE' not in raw_xml.upper() and b'<!ENTITY' not in raw_xml.upper(),
                    'XML entity declarations prohibited')
            return ET.fromstring(raw_xml)

        strings = []
        if 'xl/sharedStrings.xml' in names:
            strings = [''.join(t.text or '' for t in item.iter(S+'t'))
                       for item in xml('xl/sharedStrings.xml')]
        relations = {r.attrib['Id']: r for r in xml('xl/_rels/workbook.xml.rels')}
        sheets = xml('xl/workbook.xml').find(S+'sheets')
        require(sheets is not None, 'missing workbook sheets')
        output = []
        for sheet in sheets:
            rel = relations[sheet.attrib[R+'id']]
            require(rel.get('TargetMode') != 'External', 'external sheet prohibited')
            target = rel.attrib['Target']
            path = target[1:] if target.startswith('/xl/') else 'xl/' + target
            require(path.startswith('xl/worksheets/') and '..' not in PurePosixPath(path).parts,
                    'unsafe worksheet target')
            cells = []
            seen = set()
            for row in xml(path).iter(S+'row'):
                for cell in row.findall(S+'c'):
                    coordinate = cell.attrib['r']
                    require(coordinate not in seen, 'duplicate original coordinate')
                    seen.add(coordinate)
                    kind = cell.get('t', 'n')
                    val, formula = cell.find(S+'v'), cell.find(S+'f')
                    text = None if val is None else val.text
                    if kind == 's':
                        require(text is not None and text.isdigit() and int(text) < len(strings),
                                'invalid shared-string index')
                        text = strings[int(text)]
                    elif kind == 'inlineStr':
                        text = ''.join(n.text or '' for n in cell.iter(S+'t'))
                    if text is not None or formula is not None:
                        cells.append([coordinate, kind, text, None if formula is None else formula.text])
            output.append({'name': sheet.attrib['name'], 'sheet_id': sheet.attrib['sheetId'],
                           'cells': cells})
        return output


def audit_original_cells(directory: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Compare every retained tuple with its independently read original worksheet."""
    verification = verify_bound_capture(directory, manifest)
    worksheets = matched = 0
    for identity in sorted(PINS):
        original = original_cells(retained_bytes(directory, identity+'.xlsx'))
        retained = json.loads(retained_bytes(directory, identity+'.cells.json'))['sheets']
        require(original == retained, 'original/extract cell parity mismatch')
        worksheets += len(original)
        matched += sum(len(sheet['cells']) for sheet in original)
    return {**verification, 'worksheets': worksheets, 'matched_cells': matched,
            'mismatches': 0, 'method': 'independent OOXML cell-tuple comparison'}
