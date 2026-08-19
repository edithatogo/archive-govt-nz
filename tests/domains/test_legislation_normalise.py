"""Unit tests for source-evidenced, namespace-aware legislation normalisation."""

from __future__ import annotations

import defusedxml.ElementTree as DefusedET

from archive_govt_nz.domains.legislation.models import (
    LegislationType,
    VersionStatus,
)
from archive_govt_nz.domains.legislation.normalise import (
    _extract_text_from_xml_element,
    _local_tag,
    _SafeHTMLTextExtractor,
    normalise_legislation_payload,
)


def test_normalise_namespaced_xml_act() -> None:
    """Test normalising XML Act with official NZ legislation namespaces."""
    raw_xml = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<leg:act xmlns:leg="http://www.legislation.govt.nz/namespaces/legislation" '
        b'id="DLM12345" status="in-force">\n'
        b'  <leg:cover id="DLM12345-cover">\n'
        b"    <leg:title>Public Finance Act 1989</leg:title>\n"
        b"    <leg:assent-date>1989-07-26</leg:assent-date>\n"
        b"    <leg:commencement-date>1989-07-01</leg:commencement-date>\n"
        b"  </leg:cover>\n"
        b"  <leg:body>\n"
        b'    <leg:section id="DLM12346">\n'
        b"      <leg:no>1</leg:no>\n"
        b"      <leg:heading>Title</leg:heading>\n"
        b"      <leg:text>This Act is the Public Finance Act 1989.</leg:text>\n"
        b"    </leg:section>\n"
        b'    <leg:section id="DLM12347">\n'
        b"      <leg:enum>2</leg:enum>\n"
        b"      <leg:label>Interpretation</leg:label>\n"
        b"      <leg:text>In this Act, unless the context requires...</leg:text>\n"
        b"    </leg:section>\n"
        b"  </leg:body>\n"
        b'  <leg:schedule id="DLM12348">\n'
        b"    <leg:no>1</leg:no>\n"
        b"    <leg:heading>Departments and Offices of Parliament</leg:heading>\n"
        b"    <leg:text>Schedule details...</leg:text>\n"
        b"  </leg:schedule>\n"
        b'  <leg:schedule id="DLM12349">\n'
        b"    <leg:enum>2</leg:enum>\n"
        b"    <leg:title>Schedule Two Title</leg:title>\n"
        b"    <leg:text>More schedule text.</leg:text>\n"
        b"  </leg:schedule>\n"
        b"</leg:act>"
    )

    rec = normalise_legislation_payload(
        raw_content=raw_xml,
        work_id="act-1989-107",
        title="Public Finance Act 1989",
        canonical_uri="https://www.legislation.govt.nz/act/public/1989/0107/latest/whole.html",
        retrieval_timestamp="2026-08-19T00:00:00Z",
        source_modified_timestamp="2026-08-18T10:00:00Z",
        source_media_type="application/xml",
    )

    assert rec.legislation_type == LegislationType.ACT
    assert rec.status == VersionStatus.IN_FORCE
    assert rec.status_uncertain is False
    assert rec.assent_date == "1989-07-26"
    assert rec.commencement_date == "1989-07-01"
    assert len(rec.sections) == 2
    assert rec.sections[0].section_id == "DLM12346"
    assert rec.sections[0].number == "1"
    assert rec.sections[0].heading == "Title"
    assert "Public Finance Act 1989" in rec.sections[0].content
    assert rec.sections[1].number == "2"
    assert rec.sections[1].heading == "Interpretation"
    assert len(rec.schedules) == 2
    assert rec.schedules[0].schedule_id == "DLM12348"
    assert rec.schedules[0].heading == "Departments and Offices of Parliament"
    assert rec.schedules[1].number == "2"
    assert rec.schedules[1].heading == "Schedule Two Title"
    assert rec.retrieval_timestamp == "2026-08-19T00:00:00Z"
    assert rec.source_modified_timestamp == "2026-08-18T10:00:00Z"
    assert rec.expression_id is not None
    assert rec.expression_id.startswith("exp:act-1989-107:")
    assert rec.manifestation_id is not None
    assert rec.manifestation_id.startswith(f"man:{rec.expression_id}:xml:")


def test_normalise_bill_and_regulation_metadata() -> None:
    """Test Bill and Regulation extraction with stages and statuses."""
    bill_xml = (
        b'<bill id="DLM999" stage="introduced">\n'
        b"  <heading>Appropriation Bill 2026</heading>\n"
        b'  <section id="sec-1"><heading>Short Title</heading>'
        b"<text>Clause 1 text</text></section>\n"
        b"</bill>"
    )
    rec_bill = normalise_legislation_payload(
        raw_content=bill_xml,
        work_id="bill-2026-1",
        title="Appropriation Bill 2026",
        canonical_uri="https://www.legislation.govt.nz/bill/government/2026/0001/latest/whole.html",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_bill.legislation_type == LegislationType.BILL
    assert rec_bill.status == VersionStatus.BILL_INTRODUCED
    assert rec_bill.status_uncertain is False

    reg_xml = (
        b'<regulation id="DLM888" type="regulation" in.force="yes">\n'
        b"  <title>Health Regulations 2026</title>\n"
        b'  <section id="reg-1"><heading>Citation</heading>'
        b"<text>Reg 1 text</text></section>\n"
        b"</regulation>"
    )
    rec_reg = normalise_legislation_payload(
        raw_content=reg_xml,
        work_id="regulation-2026-50",
        title="Health Regulations 2026",
        canonical_uri="https://www.legislation.govt.nz/regulation/public/2026/0050/latest/whole.html",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_reg.legislation_type == LegislationType.REGULATION
    assert rec_reg.status == VersionStatus.IN_FORCE
    assert rec_reg.status_uncertain is False


def test_normalise_all_statutory_types() -> None:
    """Test Imperial Act, Provincial Act, Order in Council, and Deemed Reg."""
    imp_xml = b'<imperial-act id="DLM1"><title>Imperial Act</title></imperial-act>'
    rec_imp = normalise_legislation_payload(
        raw_content=imp_xml,
        work_id="imp-1",
        title="Imperial Statute",
        canonical_uri="https://example.com/act/imp",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_imp.legislation_type == LegislationType.ACT

    prov_xml = (
        b'<provincial-act id="DLM2"><title>Provincial Act</title></provincial-act>'
    )
    rec_prov = normalise_legislation_payload(
        raw_content=prov_xml,
        work_id="prov-1",
        title="Provincial Act",
        canonical_uri="https://example.com/act/prov",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_prov.legislation_type == LegislationType.ACT

    deemed_xml = b'<deemed-regulation id="DLM3"><title>Rule</title></deemed-regulation>'
    rec_deemed = normalise_legislation_payload(
        raw_content=deemed_xml,
        work_id="deemed-1",
        title="Civil Aviation Rule Part 121",
        canonical_uri="https://example.com/deemed/121",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_deemed.legislation_type == LegislationType.DEEMED_REGULATION

    order_xml = b'<order-in-council id="DLM4"><title>Order</title></order-in-council>'
    rec_order = normalise_legislation_payload(
        raw_content=order_xml,
        work_id="order-1",
        title="Order in Council 2026",
        canonical_uri="https://example.com/order/2026",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_order.legislation_type == LegislationType.ORDER_IN_COUNCIL

    rec_by_title_reg = normalise_legislation_payload(
        raw_content=b"<doc><title>Customs Rules 2026</title></doc>",
        work_id="rules-1",
        title="Customs Rules 2026",
        canonical_uri="https://example.com/item/1",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_by_title_reg.legislation_type == LegislationType.REGULATION

    rec_by_title_bill = normalise_legislation_payload(
        raw_content=b"<doc><title>Local Government Bill</title></doc>",
        work_id="bill-1",
        title="Local Government Bill",
        canonical_uri="https://example.com/item/2",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_by_title_bill.legislation_type == LegislationType.BILL


def test_normalise_status_variants() -> None:
    """Test all status attribute variations and structured child elements."""
    spent_xml = b'<act status="spent"><title>Spent Act</title></act>'
    rec_spent = normalise_legislation_payload(
        raw_content=spent_xml,
        work_id="act-spent",
        title="Spent Act",
        canonical_uri="https://example.com/act/spent",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_spent.status == VersionStatus.REPEALED

    revoked_xml = (
        b'<regulation status="revoked"><title>Revoked Reg</title></regulation>'
    )
    rec_rev = normalise_legislation_payload(
        raw_content=revoked_xml,
        work_id="reg-rev",
        title="Revoked Reg",
        canonical_uri="https://example.com/reg/rev",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_rev.status == VersionStatus.REPEALED

    amended_xml = b'<act status="amended"><title>Amended Act</title></act>'
    rec_amended = normalise_legislation_payload(
        raw_content=amended_xml,
        work_id="act-amended",
        title="Amended Act",
        canonical_uri="https://example.com/act/amended",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_amended.status == VersionStatus.AMENDED

    not_in_force_xml = b'<act in.force="no"><title>Future Act</title></act>'
    rec_nif = normalise_legislation_payload(
        raw_content=not_in_force_xml,
        work_id="act-future",
        title="Future Act",
        canonical_uri="https://example.com/act/future",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_nif.status == VersionStatus.UNKNOWN
    assert rec_nif.status_uncertain is True

    passed_xml = b'<bill status="bill-passed"><title>Passed Bill</title></bill>'
    rec_passed = normalise_legislation_payload(
        raw_content=passed_xml,
        work_id="bill-passed",
        title="Passed Bill",
        canonical_uri="https://example.com/bill/passed",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_passed.status == VersionStatus.BILL_PASSED

    hist_xml = b'<act status="historical"><title>Hist Act</title></act>'
    rec_hist = normalise_legislation_payload(
        raw_content=hist_xml,
        work_id="act-hist",
        title="Hist Act",
        canonical_uri="https://example.com/act/hist",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_hist.status == VersionStatus.HISTORICAL

    enacted_xml = b'<act stage="royal-assent"><title>Enacted Act</title></act>'
    rec_enacted = normalise_legislation_payload(
        raw_content=enacted_xml,
        work_id="act-enacted",
        title="Enacted Act",
        canonical_uri="https://example.com/act/enacted",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_enacted.status == VersionStatus.IN_FORCE

    stg_passed_xml = b'<bill stage="passed"><title>Stage Passed</title></bill>'
    rec_stg_passed = normalise_legislation_payload(
        raw_content=stg_passed_xml,
        work_id="bill-stg-passed",
        title="Stage Passed",
        canonical_uri="https://example.com/bill/stg",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_stg_passed.status == VersionStatus.BILL_PASSED

    for st_text, exp_st in (
        ("repealed", VersionStatus.REPEALED),
        ("in force", VersionStatus.IN_FORCE),
        ("introduced", VersionStatus.BILL_INTRODUCED),
    ):
        xml_bytes = f"<act><title>T</title><status>{st_text}</status></act>".encode()
        rec_child_st = normalise_legislation_payload(
            raw_content=xml_bytes,
            work_id=f"act-{st_text.replace(' ', '-')}",
            title="T",
            canonical_uri="https://example.com/act/test",
            retrieval_timestamp="2026-08-19T00:00:00Z",
        )
        assert rec_child_st.status == exp_st

    rec_uri_rep = normalise_legislation_payload(
        raw_content=b"<act><title>T</title></act>",
        work_id="act-uri-rep",
        title="T",
        canonical_uri="https://example.com/act/repealed/whole.html",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_uri_rep.status == VersionStatus.REPEALED

    rec_uri_bill = normalise_legislation_payload(
        raw_content=b"<bill><title>T</title></bill>",
        work_id="bill-uri",
        title="T",
        canonical_uri="https://example.com/bill/123/whole.html",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_uri_bill.status == VersionStatus.BILL_INTRODUCED

    rec_uri_lat = normalise_legislation_payload(
        raw_content=b"<act><title>T</title></act>",
        work_id="act-uri-lat",
        title="T",
        canonical_uri="https://example.com/act/latest/whole.html",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_uri_lat.status == VersionStatus.IN_FORCE
    assert rec_uri_lat.status_uncertain is True


def test_normalise_repealed_and_historical_expression() -> None:
    """Test repealed instruments and historical expressions."""
    repealed_xml = (
        b'<act id="DLM777" status="repealed">\n'
        b"  <title>Old Finance Act 1950</title>\n"
        b"  <date-of-repeal>1989-07-01</date-of-repeal>\n"
        b"</act>"
    )
    rec = normalise_legislation_payload(
        raw_content=repealed_xml,
        work_id="act-1950-1",
        title="Old Finance Act 1950",
        canonical_uri="https://www.legislation.govt.nz/act/public/1950/0001/repealed/whole.html",
        retrieval_timestamp="2026-08-19T00:00:00Z",
        version_date="1989-07-01",
    )
    assert rec.status == VersionStatus.REPEALED
    assert rec.status_uncertain is False
    assert rec.expression_id == "exp:act-1950-1:1989-07-01"


def test_normalise_unknown_status_and_controlled_fallback() -> None:
    """Unknown status must not default to in_force and must flag status_uncertain."""
    unknown_xml = (
        b'<custom id="CUST1">\n'
        b"  <title>Generic Document</title>\n"
        b"  <text>Some incidental text mentioning in force and repealed words.</text>\n"
        b"</custom>"
    )
    rec = normalise_legislation_payload(
        raw_content=unknown_xml,
        work_id="other-doc-1",
        title="Generic Document",
        canonical_uri="https://example.com/custom/doc1",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec.legislation_type == LegislationType.OTHER
    assert rec.status == VersionStatus.UNKNOWN
    assert rec.status_uncertain is True

    rec_default_time = normalise_legislation_payload(
        raw_content=unknown_xml,
        work_id="other-doc-2",
        title="Generic Document 2",
        canonical_uri="https://example.com/custom/doc2",
    )
    assert rec_default_time.retrieval_timestamp.endswith("Z")

    rec_explicit = normalise_legislation_payload(
        raw_content=unknown_xml,
        work_id="other-doc-3",
        title="Generic Document 3",
        canonical_uri="https://example.com/custom/doc3",
        retrieval_timestamp="2026-08-19T00:00:00Z",
        legislation_type=LegislationType.BILL,
        status=VersionStatus.IN_FORCE,
    )
    assert rec_explicit.legislation_type == LegislationType.BILL
    assert rec_explicit.status == VersionStatus.IN_FORCE
    assert rec_explicit.status_uncertain is False


def test_bounded_html_parser_and_tag_stripping() -> None:
    """Test bounded HTML parser excludes script, style, SVG, and noscript."""
    raw_html = (
        b"<!DOCTYPE html>\n"
        b"<html>\n"
        b"<head>\n"
        b"  <title>Test Bill</title>\n"
        b"  <script>console.log('malicious script');</script>\n"
        b"  <style>body { background: #000; }</style>\n"
        b"</head>\n"
        b"<body>\n"
        b"  <noscript><p>Enable JS</p></noscript>\n"
        b"  <svg><text>Ignored vector graphics</text></svg>\n"
        b"  <h1>Test Bill 2026</h1>\n"
        b"  <p>Main content text paragraph.</p>\n"
        b"</body>\n"
        b"</html>"
    )

    rec = normalise_legislation_payload(
        raw_content=raw_html,
        work_id="bill-2026-99",
        title="Test Bill 2026",
        canonical_uri="https://example.com/bill/2026/99",
        retrieval_timestamp="2026-08-19T00:00:00Z",
        source_media_type="text/html",
    )

    assert "malicious script" not in rec.plain_text
    assert "background: #000" not in rec.plain_text
    assert "Ignored vector graphics" not in rec.plain_text
    assert "Enable JS" not in rec.plain_text
    assert "Test Bill 2026" in rec.plain_text
    assert "Main content text paragraph." in rec.plain_text
    assert rec.manifestation_id is not None
    assert rec.manifestation_id.startswith(f"man:{rec.expression_id}:html:")


def test_safe_xml_malformed_fallback_and_depth_limits() -> None:
    """Test malformed XML falls back safely to HTML extractor without raising."""
    malformed_xml = b"<act><section id='1'><unclosed_tag>Content text</section></act>"
    rec = normalise_legislation_payload(
        raw_content=malformed_xml,
        work_id="act-fallback-1",
        title="Fallback Act",
        canonical_uri="https://example.com/act/fb",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert "Content text" in rec.plain_text
    assert rec.legislation_type == LegislationType.ACT

    extractor = _SafeHTMLTextExtractor(max_depth=2)
    extractor.feed("<div><div><div><p>Too deep</p></div></div></div>")
    extractor.close()
    assert "Too deep" not in extractor.get_text()


def test_xml_tail_and_local_tag_utilities() -> None:
    """Test _local_tag and _extract_text_from_xml_element with tail text."""
    assert _local_tag("tag") == "tag"
    assert _local_tag("{http://example.com}tag") == "tag"

    tree = DefusedET.fromstring(b"<root>Before<child>Inner</child>Tail</root>")
    text = _extract_text_from_xml_element(tree)
    assert "Before" in text
    assert "Inner" in text
    assert "Tail" in text


def test_coverage_branches_dates_and_stages() -> None:
    """Test specific date tags, stages, and URI patterns."""
    date_xml = (
        b"<act>"
        b"<title>Test Act</title>"
        b"<royal-assent-date>2026-05-01</royal-assent-date>"
        b"<date-of-commencement>2026-06-01</date-of-commencement>"
        b"</act>"
    )
    rec_dates = normalise_legislation_payload(
        raw_content=date_xml,
        work_id="act-dates",
        title="Test Act",
        canonical_uri="https://example.com/act/regs",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_dates.assent_date == "2026-05-01"
    assert rec_dates.commencement_date == "2026-06-01"

    r1_xml = b'<bill stage="first-reading"><title>R1 Bill</title></bill>'
    rec_r1 = normalise_legislation_payload(
        raw_content=r1_xml,
        work_id="bill-r1",
        title="R1 Bill",
        canonical_uri="https://example.com/bill/r1",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_r1.status == VersionStatus.BILL_INTRODUCED

    r3_xml = b'<bill stage="third-reading"><title>R3 Bill</title></bill>'
    rec_r3 = normalise_legislation_payload(
        raw_content=r3_xml,
        work_id="bill-r3",
        title="R3 Bill",
        canonical_uri="https://example.com/bill/r3",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_r3.status == VersionStatus.BILL_PASSED

    as_amended_xml = b'<act status="as-amended"><title>As Amended</title></act>'
    rec_as_am = normalise_legislation_payload(
        raw_content=as_amended_xml,
        work_id="act-asam",
        title="As Amended",
        canonical_uri="https://example.com/act/asam",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_as_am.status == VersionStatus.AMENDED

    as_am_child = b"<act><title>T</title><status>as amended</status></act>"
    assert (
        normalise_legislation_payload(
            raw_content=as_am_child,
            work_id="a-1",
            title="T",
            canonical_uri="https://example.com/act/t",
            retrieval_timestamp="2026-08-19T00:00:00Z",
        ).status
        == VersionStatus.AMENDED
    )

    bill_intro_child = b"<act><title>T</title><status>bill-introduced</status></act>"
    assert (
        normalise_legislation_payload(
            raw_content=bill_intro_child,
            work_id="a-2",
            title="T",
            canonical_uri="https://example.com/act/t2",
            retrieval_timestamp="2026-08-19T00:00:00Z",
        ).status
        == VersionStatus.BILL_INTRODUCED
    )

    empty_children_xml = (
        b"<act><title>T</title>"
        b'<section id="sec-empty"><heading></heading>'
        b"<no></no><text>Empty text</text></section>"
        b'<schedule id="sch-empty"><title></title>'
        b"<enum></enum><text>Empty sch text</text></schedule>"
        b"</act>"
    )
    rec_empty = normalise_legislation_payload(
        raw_content=empty_children_xml,
        work_id="act-emp",
        title="T",
        canonical_uri="https://example.com/act/emp",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert len(rec_empty.sections) == 1
    assert len(rec_empty.schedules) == 1
    assert rec_empty.sections[0].heading == "Section 1"
    assert rec_empty.schedules[0].heading == "Schedule 1"


def test_final_coverage_branches() -> None:
    """Test remaining URI, title, stage and tag permutations."""
    rec_regs = normalise_legislation_payload(
        raw_content=b"<doc><title>R</title></doc>",
        work_id="r-1",
        title="R",
        canonical_uri="https://example.com/regs/123",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_regs.legislation_type == LegislationType.REGULATION

    rec_title_act = normalise_legislation_payload(
        raw_content=b"<doc><title>The Great Act</title></doc>",
        work_id="a-title",
        title="The Great Act",
        canonical_uri="https://example.com/other/123",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_title_act.legislation_type == LegislationType.ACT

    rec_title_oic = normalise_legislation_payload(
        raw_content=b"<doc><title>Order in Council</title></doc>",
        work_id="o-title",
        title="Emergency Order in Council 2026",
        canonical_uri="https://example.com/other/oic",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_title_oic.legislation_type == LegislationType.ORDER_IN_COUNCIL

    rec_comm = normalise_legislation_payload(
        raw_content=b'<bill stage="committee-stage"><title>B</title></bill>',
        work_id="b-comm",
        title="B",
        canonical_uri="https://example.com/bill/comm",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_comm.status == VersionStatus.BILL_INTRODUCED

    alt_dates_xml = (
        b"<act>"
        b"<title>A</title>"
        b"<date-of-assent>2026-01-10</date-of-assent>"
        b"<commence-date>2026-02-10</commence-date>"
        b"<date-of-repeal>2026-12-31</date-of-repeal>"
        b"</act>"
    )
    rec_alt_d = normalise_legislation_payload(
        raw_content=alt_dates_xml,
        work_id="a-alt-d",
        title="A",
        canonical_uri="https://example.com/act/alt",
        retrieval_timestamp="2026-08-19T00:00:00Z",
    )
    assert rec_alt_d.assent_date == "2026-01-10"
    assert rec_alt_d.commencement_date == "2026-02-10"
    assert rec_alt_d.status == VersionStatus.REPEALED
