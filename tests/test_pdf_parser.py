import fitz

from app.infra.parsers.pdf import PdfParser


def test_pdf_parser_extracts_text_by_page(tmp_path) -> None:
    pdf_path = tmp_path / "sample.pdf"

    document = fitz.open()
    page_one = document.new_page()
    page_one.insert_text((72, 72), "Travel policy overview")
    page_two = document.new_page()
    page_two.insert_text((72, 72), "Expense approvals require manager sign-off")
    document.save(pdf_path)
    document.close()

    parsed = PdfParser().parse(pdf_path, filename=pdf_path.name)

    assert parsed.metadata["page_count"] == 2
    assert len(parsed.sections) == 2
    assert parsed.sections[0].metadata["page_number"] == 1
    assert "Travel policy overview" in parsed.sections[0].text
