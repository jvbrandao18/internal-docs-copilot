def test_basic_query_flow_returns_grounded_answer(client) -> None:
    csv_content = b"Policy,Rule\nPassword policy,Minimum 12 characters\n"
    upload_response = client.post(
        "/documents/upload",
        files={"file": ("policies.csv", csv_content, "text/csv")},
    )
    document_id = upload_response.json()["document_id"]

    response = client.post(
        "/queries/ask",
        json={
            "question": "What is the password policy?",
            "document_ids": [document_id],
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieved_chunks"] >= 1
    assert payload["confidence"] >= 0.05
    assert payload["sources"][0]["document_name"] == "policies.csv"
    assert "Minimum 12 characters" in payload["answer"]
