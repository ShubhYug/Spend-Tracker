def _add(client, headers, amount, category, expense_date):
    resp = client.post(
        "/expenses",
        json={"amount": amount, "category": category, "date": expense_date},
        headers=headers,
    )
    assert resp.status_code == 201


def test_summary_requires_api_key(client):
    resp = client.get("/summary")
    assert resp.status_code == 401


def test_summary_totals_and_by_category(client, auth_headers):
    _add(client, auth_headers, 100, "Food", "2026-03-05")
    _add(client, auth_headers, 50, "Transport", "2026-03-10")
    _add(client, auth_headers, 25, "Food", "2026-03-20")

    resp = client.get("/summary", params={"month": "2026-03"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["month"] == "2026-03"
    assert body["total_spend"] == 175
    by_cat = {c["category"]: c["total"] for c in body["by_category"]}
    assert by_cat["Food"] == 125
    assert by_cat["Transport"] == 50


def test_summary_ignores_expenses_outside_month(client, auth_headers):
    _add(client, auth_headers, 100, "Food", "2026-02-28")
    _add(client, auth_headers, 200, "Food", "2026-04-01")

    resp = client.get("/summary", params={"month": "2026-03"}, headers=auth_headers)
    body = resp.json()
    assert body["total_spend"] == 0
    assert body["by_category"] == []


def test_summary_month_over_month_change(client, auth_headers):
    _add(client, auth_headers, 100, "Food", "2026-02-10")
    _add(client, auth_headers, 150, "Food", "2026-03-10")

    resp = client.get("/summary", params={"month": "2026-03"}, headers=auth_headers)
    body = resp.json()
    assert body["previous_month_total"] == 100
    assert body["total_change_pct"] == 50.0


def test_summary_handles_january_previous_month_wraparound(client, auth_headers):
    _add(client, auth_headers, 100, "Food", "2025-12-15")
    _add(client, auth_headers, 100, "Food", "2026-01-15")

    resp = client.get("/summary", params={"month": "2026-01"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["previous_month_total"] == 100


def test_summary_flags_category_increase_over_20_percent(client, auth_headers):
    _add(client, auth_headers, 100, "Food", "2026-02-10")
    _add(client, auth_headers, 130, "Food", "2026-03-10")

    resp = client.get("/summary", params={"month": "2026-03"}, headers=auth_headers)
    body = resp.json()
    assert any("Food" in insight for insight in body["insights"])


def test_summary_does_not_flag_small_increase(client, auth_headers):
    _add(client, auth_headers, 100, "Food", "2026-02-10")
    _add(client, auth_headers, 110, "Food", "2026-03-10")

    resp = client.get("/summary", params={"month": "2026-03"}, headers=auth_headers)
    body = resp.json()
    assert body["insights"] == []


def test_summary_previous_zero_spend_is_not_flagged(client, auth_headers):
    _add(client, auth_headers, 50, "Food", "2026-03-10")

    resp = client.get("/summary", params={"month": "2026-03"}, headers=auth_headers)
    body = resp.json()
    change = next(c for c in body["by_category_change"] if c["category"] == "Food")
    assert change["previous"] == 0
    assert change["change_pct"] is None
    assert body["insights"] == []


def test_summary_rejects_bad_month_format(client, auth_headers):
    resp = client.get("/summary", params={"month": "2026/03"}, headers=auth_headers)
    assert resp.status_code == 400


def test_summary_rejects_invalid_month_number(client, auth_headers):
    resp = client.get("/summary", params={"month": "2026-13"}, headers=auth_headers)
    assert resp.status_code == 400
