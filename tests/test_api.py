def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_items_list_pagination(client):
    r = client.get("/items?page=1&page_size=2")
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1
    assert data["pageSize"] == 2
    assert data["total"] >= 3
    assert len(data["results"]) == 2


def test_create_event_and_history(client):
    payload = {"userId": 1, "itemId": 3, "eventType": "view"}
    r = client.post("/events", json=payload)
    assert r.status_code == 200
    ev = r.json()
    assert ev["userId"] == 1
    assert ev["itemId"] == 3
    assert ev["eventType"] == "view"

    r2 = client.get("/users/1/history?limit=10")
    assert r2.status_code == 200
    hist = r2.json()
    assert hist["userId"] == 1
    assert len(hist["results"]) >= 1


def test_recommendations_content(client):
    r = client.get("/recommendations/1?strategy=content&k=5")
    assert r.status_code == 200
    data = r.json()
    assert data["userId"] == 1
    assert data["strategy"] == "content"
    assert "results" in data
    assert isinstance(data["results"], list)


def test_metrics_offline(client):
    r = client.get("/metrics/offline?strategy=content&k=5&users=10")
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "content"
    assert "metrics" in data
    assert "precision@k" in data["metrics"]
    assert "recall@k" in data["metrics"]
