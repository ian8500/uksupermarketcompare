def test_compare_basket_flow(client):
    payload = {"items": ["heinz baked beans"], "retailers": ["tesco", "asda"]}
    response = client.post("/baskets/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cheapest_overall_basket"] > 0
    assert len(data["results"]) == 1


def test_saved_lists(client):
    create = client.post("/saved-lists", json={"name": "weekly", "items": ["milk", "bread"]})
    assert create.status_code == 200
    got = client.get("/saved-lists")
    assert got.status_code == 200
    assert len(got.json()) == 1

    saved_id = create.json()["id"]
    deleted = client.delete(f"/saved-lists/{saved_id}")
    assert deleted.status_code == 204

    after_delete = client.get("/saved-lists")
    assert after_delete.status_code == 200
    assert after_delete.json() == []
