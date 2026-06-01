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


def test_recommendations_user_based(client):
    """Test user-based collaborative filtering strategy."""
    r = client.get("/recommendations/1?strategy=user&k=5")
    assert r.status_code == 200
    data = r.json()
    assert data["userId"] == 1
    assert data["strategy"] == "user"
    assert "results" in data
    assert isinstance(data["results"], list)


def test_recommendations_hybrid(client):
    """Test hybrid recommendation strategy."""
    r = client.get("/recommendations/1?strategy=hybrid&k=5")
    assert r.status_code == 200
    data = r.json()
    assert data["userId"] == 1
    assert data["strategy"] == "hybrid"
    assert "results" in data
    assert isinstance(data["results"], list)


def test_recommendations_invalid_user(client):
    """Test that requesting recommendations for non-existent user returns 404."""
    r = client.get("/recommendations/9999?strategy=content&k=5")
    assert r.status_code == 404
    assert "User not found" in r.json()["detail"]


def test_recommendations_invalid_strategy(client):
    """Test that invalid strategy returns 400."""
    r = client.get("/recommendations/1?strategy=invalid&k=5")
    assert r.status_code == 400
    assert "Unknown strategy" in r.json()["detail"]


def test_get_single_item(client):
    """Test getting a single item by ID."""
    r = client.get("/items/1")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert "title" in data
    assert "tags" in data


def test_get_item_not_found(client):
    """Test that non-existent item returns 404."""
    r = client.get("/items/9999")
    assert r.status_code == 404
