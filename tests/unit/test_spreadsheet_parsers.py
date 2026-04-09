import pandas as pd

from app.infra.parsers.csv_parser import CsvParser
from app.infra.parsers.xlsx_parser import XlsxParser


def test_csv_parser_extracts_non_empty_rows(tmp_path) -> None:
    csv_path = tmp_path / "policies.csv"
    pd.DataFrame(
        [
            {"Policy": "Password policy", "Rule": "Minimum 12 characters"},
            {"Policy": "", "Rule": ""},
        ]
    ).to_csv(csv_path, index=False)

    result = CsvParser().parse(csv_path)

    assert result.file_type == "csv"
    assert len(result.records) == 1
    assert "Password policy" in result.records[0].content
    assert result.records[0].row_start == 2


def test_xlsx_parser_extracts_rows_by_sheet(tmp_path) -> None:
    xlsx_path = tmp_path / "matrix.xlsx"
    with pd.ExcelWriter(xlsx_path) as writer:
        pd.DataFrame([{"Team": "Security", "Owner": "Ana"}]).to_excel(
            writer,
            sheet_name="Teams",
            index=False,
        )
        pd.DataFrame([{"Policy": "Remote Work", "Status": "Approved"}]).to_excel(
            writer,
            sheet_name="Policies",
            index=False,
        )

    result = XlsxParser().parse(xlsx_path)

    assert result.file_type == "xlsx"
    assert result.sheet_count == 2
    assert len(result.records) == 2
    assert any(record.sheet_name == "Teams" for record in result.records)
