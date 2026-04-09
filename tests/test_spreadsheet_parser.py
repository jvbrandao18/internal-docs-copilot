import pandas as pd

from app.infra.parsers.spreadsheet import SpreadsheetParser


def test_csv_parser_creates_row_sections(tmp_path) -> None:
    csv_path = tmp_path / "policies.csv"
    dataframe = pd.DataFrame(
        [
            {"Policy": "Leave", "Days": 30},
            {"Policy": "Travel", "Days": 15},
        ]
    )
    dataframe.to_csv(csv_path, index=False)

    parsed = SpreadsheetParser().parse(csv_path, filename=csv_path.name)

    assert parsed.metadata["source_type"] == "csv"
    assert parsed.metadata["row_count"] == 2
    assert len(parsed.sections) == 2
    assert "Policy: Leave" in parsed.sections[0].text


def test_xlsx_parser_reads_multiple_sheets(tmp_path) -> None:
    xlsx_path = tmp_path / "matrix.xlsx"
    with pd.ExcelWriter(xlsx_path) as writer:
        pd.DataFrame([{"Team": "Ops", "Lead": "Ana"}]).to_excel(
            writer,
            sheet_name="Teams",
            index=False,
        )
        pd.DataFrame([{"Policy": "Remote", "Active": "Yes"}]).to_excel(
            writer,
            sheet_name="Policies",
            index=False,
        )

    parsed = SpreadsheetParser().parse(xlsx_path, filename=xlsx_path.name)

    assert parsed.metadata["source_type"] == "xlsx"
    assert parsed.metadata["sheet_count"] == 2
    assert len(parsed.sections) == 2
    assert any(section.metadata["sheet_name"] == "Teams" for section in parsed.sections)
