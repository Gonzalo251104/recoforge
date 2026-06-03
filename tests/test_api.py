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


def test_list_users(client):
    """Test listing users with pagination."""
    r = client.get("/users?page=1&page_size=2")
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1
    assert data["pageSize"] == 2
    assert "total" in data
    assert len(data["results"]) == 2


def test_create_user(client):
    """Test creating a new user."""
    payload = {"username": "new_test_user"}
    r = client.post("/users", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "new_test_user"
    assert "id" in data
    assert "created_at" in data


def test_get_user_profile(client):
    """Test getting user detailed profile statistics."""
    r = client.get("/users/1")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert "username" in data
    assert "created_at" in data
    assert "stats" in data
    assert "totalViews" in data["stats"]
    assert "totalClicks" in data["stats"]
    assert "totalSaves" in data["stats"]
    assert "favoriteTags" in data["stats"]


def test_list_events(client):
    """Test listing events with filters and pagination."""
    r = client.get("/events?page=1&page_size=5")
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1
    assert data["pageSize"] == 5
    assert "total" in data
    assert "results" in data
    
    # Filter by user_id
    r_filtered = client.get("/events?user_id=1&page_size=5")
    assert r_filtered.status_code == 200
    data_filtered = r_filtered.json()
    for item in data_filtered["results"]:
        assert item["userId"] == 1


def test_item_crud_and_similarity(client):
    """Test creating, updating, getting similar items, and deleting an item."""
    # 1. Create item
    payload = {
        "title": "CRUD Adventure Hike",
        "description": "A wonderful hiking experience through local trails.",
        "city": "Huaraz",
        "priceMin": 50.0,
        "priceMax": 120.0,
        "tags": ["adventure", "nature", "hiking"],
    }
    r = client.post("/items", json=payload)
    assert r.status_code == 201
    created_data = r.json()
    item_id = created_data["id"]
    assert created_data["title"] == "CRUD Adventure Hike"
    assert created_data["description"] == "A wonderful hiking experience through local trails."
    assert created_data["city"] == "Huaraz"
    assert created_data["priceMin"] == 50.0
    assert created_data["priceMax"] == 120.0
    assert "adventure" in created_data["tags"]

    # 2. Get similar items for item 1
    r_sim = client.get(f"/items/1/similar?k=3")
    assert r_sim.status_code == 200
    sim_data = r_sim.json()
    assert isinstance(sim_data, list)
    for sim_item in sim_data:
        assert "score" in sim_item
        assert "explanation" in sim_item
        assert "description" in sim_item

    # 3. Update item
    update_payload = {
        "title": "Updated Hiking Adventure",
        "priceMin": 60.0,
        "tags": ["nature", "hiking", "extreme"],
    }
    r_up = client.put(f"/items/{item_id}", json=update_payload)
    assert r_up.status_code == 200
    updated_data = r_up.json()
    assert updated_data["title"] == "Updated Hiking Adventure"
    assert updated_data["priceMin"] == 60.0
    assert updated_data["priceMax"] == 120.0 # unchanged
    assert "extreme" in updated_data["tags"]
    assert "adventure" not in updated_data["tags"]

    # 4. Delete item
    r_del = client.delete(f"/items/{item_id}")
    assert r_del.status_code == 200
    assert r_del.json()["status"] == "success"

    # 5. Get item 404
    r_get = client.get(f"/items/{item_id}")
    assert r_get.status_code == 404


def test_metrics_offline_all(client):
    """Test evaluating all strategies in offline evaluation."""
    r = client.get("/metrics/offline/all?k=5&users=10")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    for strategy in ["content", "user", "hybrid", "popular"]:
        assert strategy in data
        item = data[strategy]
        assert item["strategy"] == strategy
        assert "metrics" in item
        assert "precision@k" in item["metrics"]
        assert "recall@k" in item["metrics"]
        assert "ndcg@k" in item["metrics"]


