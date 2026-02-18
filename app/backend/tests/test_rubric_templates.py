from httpx import AsyncClient

from tests.helpers import VALID_RUBRIC_STRUCTURE


async def test_create_template_valid_structure(
    authenticated_client: AsyncClient,
) -> None:
    payload = {
        "name": "Engineering Interview",
        "description": "Standard rubric",
        "structure": VALID_RUBRIC_STRUCTURE,
    }
    response = await authenticated_client.post("/api/rubric-templates", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Engineering Interview"
    assert data["description"] == "Standard rubric"
    assert data["is_archived"] is False
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "structure" in data


async def test_create_template_invalid_category_weights(
    authenticated_client: AsyncClient,
) -> None:
    structure = {
        "categories": [
            {
                "name": "Technical Skills",
                "description": None,
                "weight": 50,
                "sort_order": 0,
                "criteria": [
                    {
                        "name": "Coding",
                        "description": None,
                        "weight": 100,
                        "sort_order": 0,
                    },
                ],
            },
            {
                "name": "Communication",
                "description": None,
                "weight": 30,
                "sort_order": 1,
                "criteria": [
                    {
                        "name": "Verbal",
                        "description": None,
                        "weight": 100,
                        "sort_order": 0,
                    },
                ],
            },
        ]
    }
    payload = {"name": "Bad Weights Rubric", "structure": structure}
    response = await authenticated_client.post("/api/rubric-templates", json=payload)

    assert response.status_code == 422


async def test_create_template_invalid_criterion_weights(
    authenticated_client: AsyncClient,
) -> None:
    structure = {
        "categories": [
            {
                "name": "Technical Skills",
                "description": None,
                "weight": 100,
                "sort_order": 0,
                "criteria": [
                    {
                        "name": "System Design",
                        "description": None,
                        "weight": 40,
                        "sort_order": 0,
                    },
                    {
                        "name": "Coding",
                        "description": None,
                        "weight": 30,
                        "sort_order": 1,
                    },
                ],
            },
        ]
    }
    payload = {"name": "Bad Criterion Weights Rubric", "structure": structure}
    response = await authenticated_client.post("/api/rubric-templates", json=payload)

    assert response.status_code == 422


async def test_create_template_missing_name(authenticated_client: AsyncClient) -> None:
    payload = {"structure": VALID_RUBRIC_STRUCTURE}
    response = await authenticated_client.post("/api/rubric-templates", json=payload)

    assert response.status_code == 422


async def test_create_template_empty_categories(
    authenticated_client: AsyncClient,
) -> None:
    payload = {"name": "Empty Categories Rubric", "structure": {"categories": []}}
    response = await authenticated_client.post("/api/rubric-templates", json=payload)

    assert response.status_code == 422


async def test_list_templates_empty(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/api/rubric-templates")

    assert response.status_code == 200
    data = response.json()
    assert data == {"items": [], "total": 0}


async def test_list_templates_returns_created(
    authenticated_client: AsyncClient,
) -> None:
    payload = {
        "name": "Listed Template",
        "description": None,
        "structure": VALID_RUBRIC_STRUCTURE,
    }
    create_response = await authenticated_client.post(
        "/api/rubric-templates", json=payload
    )
    assert create_response.status_code == 201

    list_response = await authenticated_client.get("/api/rubric-templates")
    assert list_response.status_code == 200

    data = list_response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["name"] == "Listed Template"
    assert item["category_count"] == 2
    assert "id" in item
    assert "created_at" in item


async def test_get_template_not_found(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/api/rubric-templates/99999")

    assert response.status_code == 404


async def test_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/rubric-templates")

    assert response.status_code == 401
