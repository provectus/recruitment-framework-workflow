from httpx import AsyncClient

from tests.helpers import VALID_RUBRIC_STRUCTURE

UPDATED_STRUCTURE = {
    "categories": [
        {
            "name": "Problem Solving",
            "description": None,
            "weight": 100,
            "sort_order": 0,
            "criteria": [
                {
                    "name": "Algorithms",
                    "description": None,
                    "weight": 100,
                    "sort_order": 0,
                },
            ],
        },
    ]
}

INVALID_STRUCTURE = {
    "categories": [
        {
            "name": "Technical Skills",
            "description": None,
            "weight": 60,
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


async def create_template(
    client: AsyncClient,
    name: str = "Test Rubric",
    description: str | None = "A test rubric",
) -> dict:
    payload = {
        "name": name,
        "description": description,
        "structure": VALID_RUBRIC_STRUCTURE,
    }
    response = await client.post("/api/rubric-templates", json=payload)
    assert response.status_code == 201
    return response.json()


async def test_update_template_name(authenticated_client: AsyncClient) -> None:
    template = await create_template(authenticated_client)
    template_id = template["id"]

    response = await authenticated_client.patch(
        f"/api/rubric-templates/{template_id}",
        json={"name": "Renamed Rubric"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Renamed Rubric"
    assert data["description"] == template["description"]
    assert data["id"] == template_id


async def test_update_template_structure(authenticated_client: AsyncClient) -> None:
    template = await create_template(authenticated_client)
    template_id = template["id"]

    response = await authenticated_client.patch(
        f"/api/rubric-templates/{template_id}",
        json={"structure": UPDATED_STRUCTURE},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["structure"]["categories"][0]["name"] == "Problem Solving"
    assert data["name"] == template["name"]


async def test_update_template_invalid_structure(
    authenticated_client: AsyncClient,
) -> None:
    template = await create_template(authenticated_client)
    template_id = template["id"]

    response = await authenticated_client.patch(
        f"/api/rubric-templates/{template_id}",
        json={"structure": INVALID_STRUCTURE},
    )

    assert response.status_code == 422


async def test_update_template_not_found(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.patch(
        "/api/rubric-templates/99999",
        json={"name": "Ghost Rubric"},
    )

    assert response.status_code == 404


async def test_duplicate_template(authenticated_client: AsyncClient) -> None:
    template = await create_template(authenticated_client, name="Original Rubric")
    template_id = template["id"]

    response = await authenticated_client.post(
        f"/api/rubric-templates/{template_id}/duplicate"
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Original Rubric (Copy)"
    assert data["structure"] == template["structure"]
    assert data["id"] != template_id
    assert data["is_archived"] is False


async def test_duplicate_not_found(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/api/rubric-templates/99999/duplicate")

    assert response.status_code == 404


async def test_archive_template(authenticated_client: AsyncClient) -> None:
    template = await create_template(authenticated_client)
    template_id = template["id"]

    response = await authenticated_client.post(
        f"/api/rubric-templates/{template_id}/archive"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert data["is_archived"] is True
    assert data["position_count"] == 0


async def test_archive_template_hidden_from_list(
    authenticated_client: AsyncClient,
) -> None:
    template = await create_template(authenticated_client)
    template_id = template["id"]

    archive_response = await authenticated_client.post(
        f"/api/rubric-templates/{template_id}/archive"
    )
    assert archive_response.status_code == 200

    list_response = await authenticated_client.get("/api/rubric-templates")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 0
    assert all(item["id"] != template_id for item in data["items"])


async def test_archived_template_404_on_get(authenticated_client: AsyncClient) -> None:
    template = await create_template(authenticated_client)
    template_id = template["id"]

    archive_response = await authenticated_client.post(
        f"/api/rubric-templates/{template_id}/archive"
    )
    assert archive_response.status_code == 200

    get_response = await authenticated_client.get(
        f"/api/rubric-templates/{template_id}"
    )
    assert get_response.status_code == 404
