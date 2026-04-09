def test_document_upload_and_list_documents(client) -> None:
    csv_content = b"Policy,Rule\nPassword policy,Minimum 12 characters\n"

    upload_response = client.post(
        "/documents/upload",
        files={"file": ("policies.csv", csv_content, "text/csv")},
    )

    assert upload_response.status_code == 201
    payload = upload_response.json()
    assert payload["status"] == "indexed"
    document_id = payload["document_id"]

    list_response = client.get("/documents")

    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == document_id
    assert items[0]["filename"] == "policies.csv"
