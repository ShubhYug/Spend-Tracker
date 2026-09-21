def test_create_expense_success(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 25.5, "category": "Food", "note": "Lunch", "date": "2026-01-15"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["amount"] == 25.5
    assert body["category"] == "Food"
    assert body["note"] == "Lunch"
    assert body["id"] is not None


def test_create_expense_without_note_is_optional(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "2026-01-15"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["note"] is None


def test_create_expense_rejects_zero_amount(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 0, "category": "Food", "date": "2026-01-15"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_negative_amount(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": -5, "category": "Food", "date": "2026-01-15"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_blank_category(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "   ", "date": "2026-01-15"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_bad_date(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "Food", "date": "not-a-date"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_future_date(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "Food", "date": "2099-01-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_requires_api_key(client):
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "Food", "date": "2026-01-15"},
    )
    assert resp.status_code == 401


def test_create_expense_rejects_wrong_api_key(client):
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "Food", "date": "2026-01-15"},
        headers={"X-API-Key": "wrong"},
    )
    assert resp.status_code == 401


def test_list_expenses_requires_api_key(client):
    resp = client.get("/expenses")
    assert resp.status_code == 401


def test_list_expenses_filters_by_category(client, auth_headers):
    client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "2026-01-01"},
        headers=auth_headers,
    )
    client.post(
        "/expenses",
        json={"amount": 20, "category": "Transport", "date": "2026-01-02"},
        headers=auth_headers,
    )

    resp = client.get("/expenses", params={"category": "Food"}, headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["category"] == "Food"


def test_list_expenses_filters_by_date_range(client, auth_headers):
    client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "2026-01-01"},
        headers=auth_headers,
    )
    client.post(
        "/expenses",
        json={"amount": 20, "category": "Food", "date": "2026-02-01"},
        headers=auth_headers,
    )

    resp = client.get(
        "/expenses",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["date"] == "2026-01-01"


def test_list_expenses_rejects_inverted_date_range(client, auth_headers):
    resp = client.get(
        "/expenses",
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_list_expenses_empty_by_default(client, auth_headers):
    resp = client.get("/expenses", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []
