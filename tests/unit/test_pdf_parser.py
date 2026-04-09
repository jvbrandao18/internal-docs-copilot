import fitz

from app.infra.parsers.pdf_parser import PdfParser


def test_pdf_parser_extracts_text_by_page(tmp_path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    document = fitz.open()
    page_one = document.new_page()
    page_one.insert_text((72, 72), "Corporate travel policy")
    page_two = document.new_page()
    page_two.insert_text((72, 72), "Expenses require manager approval")
    document.save(pdf_path)
    document.close()

    result = PdfParser().parse(pdf_path)

    assert result.file_type == "pdf"
    assert result.page_count == 2
    assert len(result.records) == 2
    assert result.records[0].page_number == 1
    assert "Corporate travel policy" in result.records[0].content
